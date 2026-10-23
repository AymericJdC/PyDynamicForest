"""Q-9E.5 adapter from Q-9E.4 physical nodal masses to native solver density.

The solver state has axis order (height, DBH), lives on normalized coordinates,
and stores density per normalized height-DBH area. Conversion is performed from
nodal stem masses, not by interpolating density values. Compact bilinear
redistribution onto native physical nodes preserves total mass and physical
first moments whenever the source support lies inside the native domain.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import numpy as np
from pydynamicforest.numerics import product_trapezoidal_weights
from pydynamicforest.observation_operators import physical_height_nodes, physical_dbh_nodes
from pydynamicforest.types import InitialCondition, Parameters, SimulationContext, State
from pydynamicforest.initial_conditions import build_initial_state

@dataclass(frozen=True)
class Q9E4GridState:
    height_m: np.ndarray
    diameter_cm: np.ndarray
    nodal_mass_ha: np.ndarray
    density_ha_per_m_per_cm: np.ndarray | None = None
    source: str | None = None

@dataclass(frozen=True)
class NativeStateConversion:
    U0: np.ndarray
    native_nodal_mass_ha: np.ndarray
    source_mass_ha: float
    native_mass_ha: float
    source_mean_height_m: float
    native_mean_height_m: float
    source_mean_dbh_cm: float
    native_mean_dbh_cm: float
    clipped_source_nodes: int
    source: str | None = None


def _one_dimensional_weights(nodes: np.ndarray) -> np.ndarray:
    x=np.asarray(nodes,dtype=float)
    if x.ndim!=1 or x.size<2 or not np.all(np.isfinite(x)) or not np.all(np.diff(x)>0):
        raise ValueError('nodes must be finite, one-dimensional and strictly increasing')
    w=np.empty_like(x); w[0]=0.5*(x[1]-x[0]); w[-1]=0.5*(x[-1]-x[-2]); w[1:-1]=0.5*(x[2:]-x[:-2])
    return w


def load_q9e4_grid_state(path: str | Path) -> Q9E4GridState:
    file_path=Path(path)
    if not file_path.is_file(): raise FileNotFoundError(file_path)
    with np.load(file_path) as payload:
        required={'height_m','diameter_cm','nodal_mass_ha'}
        missing=required-set(payload.files)
        if missing: raise KeyError(f'missing Q-9E.4 arrays: {sorted(missing)}')
        h=np.array(payload['height_m'],dtype=float,copy=True)
        d=np.array(payload['diameter_cm'],dtype=float,copy=True)
        mass=np.array(payload['nodal_mass_ha'],dtype=float,copy=True)
        density=np.array(payload['density_ha_per_m_per_cm'],dtype=float,copy=True) if 'density_ha_per_m_per_cm' in payload.files else None
    if mass.shape!=(h.size,d.size): raise ValueError('nodal_mass_ha shape does not match height-DBH axes')
    if not np.all(np.isfinite(mass)) or np.min(mass)<0: raise ValueError('nodal masses must be finite and non-negative')
    if density is not None:
        if density.shape!=mass.shape or not np.all(np.isfinite(density)) or np.min(density)<0: raise ValueError('physical density is invalid')
        q=np.outer(_one_dimensional_weights(h),_one_dimensional_weights(d))
        if not np.allclose(density*q,mass,rtol=2e-12,atol=2e-10):
            raise ValueError('Q-9E.4 density and nodal masses are inconsistent')
    return Q9E4GridState(h,d,mass,density,str(file_path))


def _bracket(nodes: np.ndarray, value: float, allow_clip: bool):
    clipped=False; x=float(value)
    if x<nodes[0] or x>nodes[-1]:
        if not allow_clip: raise ValueError(f'source value {x} outside native domain [{nodes[0]}, {nodes[-1]}]')
        x=float(np.clip(x,nodes[0],nodes[-1])); clipped=True
    if x==nodes[-1]: return len(nodes)-2,len(nodes)-1,0.0,1.0,clipped
    k=int(np.searchsorted(nodes,x,side='right')-1); k=max(0,min(k,len(nodes)-2)); t=(x-nodes[k])/(nodes[k+1]-nodes[k])
    return k,k+1,1.0-t,t,clipped


def convert_q9e4_to_native(source: Q9E4GridState, p: Parameters, *, allow_clip: bool=False) -> NativeStateConversion:
    native_h=physical_height_nodes(p)
    native_d=physical_dbh_nodes(p,unit='cm')
    native_mass=np.zeros((native_h.size,native_d.size),dtype=float)
    clipped=0
    for i,h in enumerate(source.height_m):
        for j,d in enumerate(source.diameter_cm):
            mass=float(source.nodal_mass_ha[i,j])
            if mass<=0: continue
            h0,h1,wh0,wh1,ch=_bracket(native_h,float(h),allow_clip)
            d0,d1,wd0,wd1,cd=_bracket(native_d,float(d),allow_clip)
            clipped += int(ch or cd)
            for ih,wh in ((h0,wh0),(h1,wh1)):
                for jd,wd in ((d0,wd0),(d1,wd1)):
                    native_mass[ih,jd]+=mass*wh*wd
    weights=product_trapezoidal_weights(p)
    U0=np.divide(native_mass,weights,out=np.zeros_like(native_mass),where=weights>0)
    sm=float(np.sum(source.nodal_mass_ha)); nm=float(np.sum(native_mass))
    if sm<=0 or nm<=0: raise ValueError('source and native masses must be positive')
    sh=float(np.sum(source.nodal_mass_ha*source.height_m[:,None])/sm)
    sd=float(np.sum(source.nodal_mass_ha*source.diameter_cm[None,:])/sm)
    nh=float(np.sum(native_mass*native_h[:,None])/nm)
    nd=float(np.sum(native_mass*native_d[None,:])/nm)
    return NativeStateConversion(U0,native_mass,sm,nm,sh,nh,sd,nd,clipped,source.source)


def native_initial_condition(conversion: NativeStateConversion, *, age: float, year: int, provider_id: str, name: str='ecouves_a5_empirical_grid') -> InitialCondition:
    return InitialCondition(name=name,initial_age=float(age),mass_target=conversion.native_mass_ha,
        distribution_kind='precomputed_empirical_height_dbh',
        distribution_parameters={'inventory_year':int(year),'height_provider_id':provider_id,'conversion':'conservative_bilinear_nodal_mass','axis_order':'height_dbh','density_coordinates':'normalized'},
        source=conversion.source,description='Q-9E reconstructed state; replaceable height provider retained in provenance.',U0=conversion.U0)


def build_native_state(conversion: NativeStateConversion, p: Parameters, c: SimulationContext, *, age: float, year: int, provider_id: str) -> tuple[InitialCondition,State]:
    x0=native_initial_condition(conversion,age=age,year=year,provider_id=provider_id)
    if abs(c.initial_age-float(age))>1e-12: raise ValueError('simulation context initial age does not match reconstructed inventory age')
    return x0,build_initial_state(x0,p,c)
