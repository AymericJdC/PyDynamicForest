"""Weighted height diagnostics and target comparisons."""
from __future__ import annotations
from dataclasses import dataclass, fields
import math
from .height_types import *

@dataclass(frozen=True)
class DominantHeightResult:
    height_m:float|None; status:str; target_density_ha:float; available_density_ha:float; selected_density_ha:float
@dataclass(frozen=True)
class HeightDiagnostics:
    n_trees:int; n_with_valid_height:int; total_density_ha:float; valid_height_density_ha:float; weighted_coverage:float
    mean_height_m:float|None; quadratic_mean_height_m:float|None; height_diameter_correlation:float|None
    mean_slenderness:float|None; quadratic_mean_slenderness:float|None; minimum_slenderness:float|None; maximum_slenderness:float|None
    dominant_height_m:float|None; dominant_height_status:str; dominant_selected_density_ha:float
@dataclass(frozen=True)
class TargetComparison:
    metric:str; computed:float|None; target:float|None; difference:float|None; absolute_difference:float|None; relative_difference:float|None; status:str

def _pairs(trees,assignment):
    by={(h.tree_id,h.year):h for h in assignment.heights}; out=[]
    for t in trees:
        h=by.get((t.tree_id,t.year))
        if h and not h.is_missing and h.height_m is not None and math.isfinite(h.height_m): out.append((t,h.height_m))
    return out

def dominant_height(trees,assignment,target_density_ha=100.0):
    pairs=_pairs(trees,assignment); available=sum(t.weight_ha for t,_ in pairs)
    if available+1e-12<target_density_ha: return DominantHeightResult(None,"insufficient_density",target_density_ha,available,0.0)
    groups={}
    for t,h in pairs: groups.setdefault(t.diameter_cm,[]).append((t,h))
    remaining=target_density_ha; numerator=selected=0.0
    for diameter in sorted(groups,reverse=True):
        group=groups[diameter]; group_weight=sum(t.weight_ha for t,_ in group)
        take=min(remaining,group_weight); fraction=take/group_weight
        numerator += sum(t.weight_ha*fraction*h for t,h in group); selected += take; remaining -= take
        if remaining<=1e-12: break
    return DominantHeightResult(numerator/selected,"ok",target_density_ha,available,selected)

def compute_height_diagnostics(trees,assignment,target_density_ha=100.0):
    pairs=_pairs(trees,assignment); total=sum(t.weight_ha for t in trees); valid=sum(t.weight_ha for t,_ in pairs)
    if pairs:
        mean=sum(t.weight_ha*h for t,h in pairs)/valid; q=math.sqrt(sum(t.weight_ha*h*h for t,h in pairs)/valid)
        md=sum(t.weight_ha*t.diameter_cm for t,h in pairs)/valid
        vh=sum(t.weight_ha*(h-mean)**2 for t,h in pairs)/valid; vd=sum(t.weight_ha*(t.diameter_cm-md)**2 for t,h in pairs)/valid
        cov=sum(t.weight_ha*(h-mean)*(t.diameter_cm-md) for t,h in pairs)/valid
        corr=cov/math.sqrt(vh*vd) if vh>0 and vd>0 else None
        slender=[(t.weight_ha,100*h/t.diameter_cm) for t,h in pairs]
        sm=sum(w*s for w,s in slender)/valid; sq=math.sqrt(sum(w*s*s for w,s in slender)/valid)
        smin=min(s for _,s in slender); smax=max(s for _,s in slender)
    else: mean=q=corr=sm=sq=smin=smax=None
    dom=dominant_height(trees,assignment,target_density_ha)
    return HeightDiagnostics(len(trees),len(pairs),total,valid,valid/total if total else 0.0,mean,q,corr,sm,sq,smin,smax,dom.height_m,dom.status,dom.selected_density_ha)

def compare_height_targets(diag:HeightDiagnostics,targets:HeightTargets):
    mapping={"mean_height_m":"mean_height_m","quadratic_mean_height_m":"quadratic_mean_height_m","dominant_height_m":"dominant_height_m","height_diameter_correlation":"height_diameter_correlation","mean_slenderness":"mean_slenderness"}
    out=[]
    for target_name,diag_name in mapping.items():
        target=getattr(targets,target_name); value=getattr(diag,diag_name)
        if target is None: out.append(TargetComparison(target_name,value,None,None,None,None,"target_not_available")); continue
        if value is None: out.append(TargetComparison(target_name,None,target,None,None,None,"computed_not_available")); continue
        diff=value-target; rel=diff/abs(target) if target!=0 else None
        out.append(TargetComparison(target_name,value,target,diff,abs(diff),rel,"compared"))
    return tuple(out)
