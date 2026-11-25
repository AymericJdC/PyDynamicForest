"""Compatibility diagnostics between Q-9E.4 states and native PyDynamicForest states."""
from __future__ import annotations
from dataclasses import dataclass,asdict
import numpy as np
from pydynamicforest.observation_operators import (stand_density,mean_height,mean_dbh,quadratic_mean_dbh,basal_area_consistent,continuous_dominant_height,height_dbh_correlation)
from pydynamicforest.types import Parameters
from .pydynamicforest_adapter import Q9E4GridState,NativeStateConversion

@dataclass(frozen=True)
class StateCompatibility:
    source_mass_ha:float; native_mass_ha:float; mass_difference_ha:float
    source_mean_height_m:float; native_mean_height_m:float; mean_height_difference_m:float
    source_mean_dbh_cm:float; native_mean_dbh_cm:float; mean_dbh_difference_cm:float
    source_quadratic_mean_dbh_cm:float; native_quadratic_mean_dbh_cm:float
    source_basal_area_m2_ha:float; native_basal_area_m2_ha:float
    source_dominant_height_m:float|None; native_dominant_height_m:float
    native_height_dbh_correlation:float; clipped_source_nodes:int
    axis_order:str='height_dbh'; density_coordinates:str='normalized'; status:str='compatible'
    def record(self): return asdict(self)

def _source_metrics(source:Q9E4GridState):
    m=float(source.nodal_mass_ha.sum()); h=source.height_m[:,None]; d=source.diameter_cm[None,:]
    mean_h=float(np.sum(source.nodal_mass_ha*h)/m); mean_d=float(np.sum(source.nodal_mass_ha*d)/m)
    dg=float(np.sqrt(np.sum(source.nodal_mass_ha*d*d)/m)); ba=float(np.sum(source.nodal_mass_ha*np.pi*(d/100)**2/4))
    atoms=[]
    for i,hv in enumerate(source.height_m):
        for j,dv in enumerate(source.diameter_cm):
            w=float(source.nodal_mass_ha[i,j])
            if w>0: atoms.append((float(dv),float(hv),w))
    remaining=min(100.0,m); selected=remaining; num=0.0
    for dv in sorted({x[0] for x in atoms},reverse=True):
        group=[x for x in atoms if x[0]==dv]; gw=sum(x[2] for x in group); take=min(remaining,gw); frac=take/gw
        num+=sum(x[1]*x[2]*frac for x in group); remaining-=take
        if remaining<=1e-12: break
    return mean_h,mean_d,dg,ba,(num/selected if selected>0 else None)

def diagnose_native_compatibility(source:Q9E4GridState,conversion:NativeStateConversion,p:Parameters)->StateCompatibility:
    sh,sd,sdg,sba,sh0=_source_metrics(source); U=conversion.U0
    result=StateCompatibility(conversion.source_mass_ha,stand_density(U,p),stand_density(U,p)-conversion.source_mass_ha,
        sh,mean_height(U,p),mean_height(U,p)-sh,sd,mean_dbh(U,p,unit='cm'),mean_dbh(U,p,unit='cm')-sd,
        sdg,quadratic_mean_dbh(U,p,unit='cm'),sba,basal_area_consistent(U,p),sh0,continuous_dominant_height(U,p),height_dbh_correlation(U,p),conversion.clipped_source_nodes)
    finite=np.all(np.isfinite(U)); nonnegative=float(np.min(U))>=-p.numerics.positivity_tolerance
    conserved=abs(result.mass_difference_ha)<=1e-8 and abs(result.mean_height_difference_m)<=1e-10 and abs(result.mean_dbh_difference_cm)<=1e-10
    status='compatible' if finite and nonnegative and conserved and conversion.clipped_source_nodes==0 else 'incompatible'
    return StateCompatibility(**{**result.record(),'status':status})
