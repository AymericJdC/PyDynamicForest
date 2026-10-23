"""Q-9F.3 distributional diagnostics without calibration.

Comparisons use native nodal masses U*w on the common PyDynamicForest grid.
They separate height marginal, DBH marginal, joint dependence and slenderness.
"""
from __future__ import annotations
from dataclasses import dataclass,asdict
from pathlib import Path
import numpy as np
from pydynamicforest.numerics import product_trapezoidal_weights
from pydynamicforest.observation_operators import physical_height_nodes,physical_dbh_nodes
from simulations.article.parameters import build_parameters

YEARS=(1998,2016,2020)
QUANTILES=(0.05,0.10,0.25,0.50,0.75,0.90,0.95)

@dataclass(frozen=True)
class DistributionComparison:
    year:int; dimension:str; total_simulated:float; total_target:float
    mean_simulated:float; mean_target:float; sd_simulated:float; sd_target:float
    wasserstein_1:float; cdf_max_distance:float; cdf_l1_distance:float
    def record(self):return asdict(self)

@dataclass(frozen=True)
class JointComparison:
    year:int; correlation_simulated:float; correlation_target:float
    mean_slenderness_simulated:float; mean_slenderness_target:float
    sd_slenderness_simulated:float; sd_slenderness_target:float
    h0_minus_hm_simulated:float; h0_minus_hm_target:float
    positive_mass_excess:float; negative_mass_deficit:float
    def record(self):return asdict(self)


def load_state(path:Path,key:str):
    if not path.is_file():raise FileNotFoundError(path)
    with np.load(path) as z:
        if key not in z.files:raise KeyError(f'{path} does not contain {key}')
        return np.array(z[key],dtype=float,copy=True)


def nodal_mass(U,p):
    mass=np.asarray(U,dtype=float)*product_trapezoidal_weights(p)
    if not np.all(np.isfinite(mass)) or np.min(mass)<-p.numerics.positivity_tolerance:
        raise ValueError('invalid native state mass')
    return np.maximum(mass,0.0)


def weighted_quantile(nodes,masses,q):
    x=np.asarray(nodes,dtype=float);w=np.asarray(masses,dtype=float)
    total=float(w.sum())
    if total<=0:return float('nan')
    c=np.cumsum(w)/total
    return float(np.interp(q,c,x,left=x[0],right=x[-1]))


def marginal_metrics(nodes,sim,target,year,dimension):
    x=np.asarray(nodes,dtype=float);s=np.asarray(sim,dtype=float);t=np.asarray(target,dtype=float)
    Ss=float(s.sum());Tt=float(t.sum())
    ps=s/Ss;pt=t/Tt
    ms=float(np.sum(ps*x));mt=float(np.sum(pt*x))
    sds=float(np.sqrt(np.sum(ps*(x-ms)**2)));sdt=float(np.sqrt(np.sum(pt*(x-mt)**2)))
    cs=np.cumsum(ps);ct=np.cumsum(pt);delta=np.abs(cs-ct)
    widths=np.diff(x)
    w1=float(np.sum(delta[:-1]*widths));ks=float(np.max(delta));l1=float(np.trapezoid(delta,x))
    return DistributionComparison(year,dimension,Ss,Tt,ms,mt,sds,sdt,w1,ks,l1)


def weighted_corr(H,D,M):
    total=M.sum();mh=np.sum(M*H)/total;md=np.sum(M*D)/total
    vh=np.sum(M*(H-mh)**2)/total;vd=np.sum(M*(D-md)**2)/total
    return float(np.sum(M*(H-mh)*(D-md))/total/np.sqrt(vh*vd)) if vh>0 and vd>0 else float('nan')


def dominant_height(H,D,M,target=100.0):
    atoms=[]
    for i,h in enumerate(H[:,0]):
        for j,d in enumerate(D[0,:]):
            if M[i,j]>0:atoms.append((float(d),float(h),float(M[i,j])))
    available=sum(a[2] for a in atoms)
    if available+1e-12<target:return float('nan')
    remaining=target;num=sel=0.0
    for d in sorted({a[0] for a in atoms},reverse=True):
        group=[a for a in atoms if a[0]==d];gw=sum(a[2] for a in group);take=min(remaining,gw);f=take/gw
        num+=sum(a[1]*a[2]*f for a in group);sel+=take;remaining-=take
        if remaining<=1e-12:break
    return num/sel


def joint_metrics(sim,target,p,year):
    h=physical_height_nodes(p);d=physical_dbh_nodes(p,unit='cm');H=h[:,None];D=d[None,:]
    eps=np.finfo(float).eps;S=sim.sum();T=target.sum()
    slender=np.divide(100*H,D,out=np.full(np.broadcast_shapes(H.shape,D.shape),np.nan),where=D>eps)
    valid=np.isfinite(slender)
    def stats(M):
        W=np.where(valid,M,0.0);tot=W.sum();mean=np.nansum(W*slender)/tot;sd=np.sqrt(np.nansum(W*(slender-mean)**2)/tot)
        hm=np.sum(M*H)/M.sum();return weighted_corr(H,D,M),float(mean),float(sd),float(dominant_height(H,D,M)-hm)
    cs,ms,ss,gs=stats(sim);ct,mt,st,gt=stats(target);diff=sim-target
    return JointComparison(year,cs,ct,ms,mt,ss,st,gs,gt,float(np.maximum(diff,0).sum()),float(np.maximum(-diff,0).sum()))


def diagnose_year(simulated_U,target_U,p,year):
    sm=nodal_mass(simulated_U,p);tm=nodal_mass(target_U,p)
    h=physical_height_nodes(p);d=physical_dbh_nodes(p,unit='cm')
    comps=(marginal_metrics(d,sm.sum(axis=0),tm.sum(axis=0),year,'dbh_cm'),marginal_metrics(h,sm.sum(axis=1),tm.sum(axis=1),year,'height_m'))
    quant=[]
    for dimension,nodes,s,t in (('dbh_cm',d,sm.sum(axis=0),tm.sum(axis=0)),('height_m',h,sm.sum(axis=1),tm.sum(axis=1))):
        for q in QUANTILES:quant.append({'year':year,'dimension':dimension,'quantile':q,'simulated_value':weighted_quantile(nodes,s,q),'target_value':weighted_quantile(nodes,t,q),'difference':weighted_quantile(nodes,s,q)-weighted_quantile(nodes,t,q)})
    return comps,joint_metrics(sm,tm,p,year),tuple(quant),sm,tm


def run_distributional_diagnostics(sim_dir:Path,target_dir:Path):
    p=build_parameters();comparisons=[];joints=[];quantiles=[];marginals=[];cells=[]
    h=physical_height_nodes(p);d=physical_dbh_nodes(p,unit='cm')
    for year in YEARS:
        sim=load_state(sim_dir/f'ecouves_a5_simulated_state_{year}.npz','U')
        target=load_state(target_dir/f'ecouves_a5_native_initial_state_{year}.npz','U0')
        comps,joint,qs,sm,tm=diagnose_year(sim,target,p,year);comparisons.extend(c.record() for c in comps);joints.append(joint.record());quantiles.extend(qs)
        for dim,nodes,s,t in (('dbh_cm',d,sm.sum(axis=0),tm.sum(axis=0)),('height_m',h,sm.sum(axis=1),tm.sum(axis=1))):
            for x,sv,tv in zip(nodes,s,t):marginals.append({'year':year,'dimension':dim,'node':float(x),'simulated_mass_ha':float(sv),'target_mass_ha':float(tv),'mass_difference_ha':float(sv-tv)})
        diff=sm-tm
        for i,hv in enumerate(h):
            for j,dv in enumerate(d):
                if sm[i,j]>0 or tm[i,j]>0:cells.append({'year':year,'height_m':float(hv),'dbh_cm':float(dv),'simulated_mass_ha':float(sm[i,j]),'target_mass_ha':float(tm[i,j]),'mass_difference_ha':float(diff[i,j])})
    return tuple(comparisons),tuple(joints),tuple(quantiles),tuple(marginals),tuple(cells)
