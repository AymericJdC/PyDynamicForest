"""Conservative projection of weighted (height, diameter) trees onto a tensor grid.

The compact bilinear (cloud-in-cell) projection distributes each tree over at
most four neighbouring grid nodes. Nodal density is obtained by dividing nodal
mass by tensor trapezoidal weights. Consequently trapezoidal integration
preserves total density and both first moments up to floating-point precision.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from collections.abc import Sequence
import math
import numpy as np
from .height_types import TreeRecord, HeightAssignment

class BoundaryPolicy(str,Enum): STRICT="strict"; CLIP="clip"

@dataclass(frozen=True)
class ProjectionGrid:
    height_m: np.ndarray
    diameter_cm: np.ndarray
    def __post_init__(self):
        h=np.asarray(self.height_m,dtype=float); d=np.asarray(self.diameter_cm,dtype=float)
        for name,x in (("height_m",h),("diameter_cm",d)):
            if x.ndim!=1 or len(x)<2 or not np.all(np.isfinite(x)) or not np.all(np.diff(x)>0):
                raise ValueError(f"{name} must be a finite strictly increasing 1D array")
        object.__setattr__(self,"height_m",h.copy()); object.__setattr__(self,"diameter_cm",d.copy())

@dataclass(frozen=True)
class ProjectedState:
    grid: ProjectionGrid
    density_ha_per_m_per_cm: np.ndarray
    nodal_mass_ha: np.ndarray
    input_tree_count: int
    projected_tree_count: int
    missing_height_count: int
    clipped_tree_count: int
    warnings: tuple[str,...]=()

@dataclass(frozen=True)
class ProjectionDiagnostics:
    mass_input_ha: float; mass_grid_ha: float; mass_difference_ha: float
    mean_height_input_m: float; mean_height_grid_m: float; mean_height_difference_m: float
    mean_diameter_input_cm: float; mean_diameter_grid_cm: float; mean_diameter_difference_cm: float
    quadratic_mean_diameter_input_cm: float; quadratic_mean_diameter_grid_cm: float
    basal_area_input_m2_ha: float; basal_area_grid_m2_ha: float
    dominant_height_input_m: float|None; dominant_height_grid_m: float|None
    clipped_tree_count:int; missing_height_count:int

def trapezoidal_weights(nodes):
    x=np.asarray(nodes,dtype=float); w=np.empty_like(x); w[0]=(x[1]-x[0])/2; w[-1]=(x[-1]-x[-2])/2
    w[1:-1]=(x[2:]-x[:-2])/2
    return w

def _bracket(nodes,value,policy):
    clipped=False; x=float(value)
    if x<nodes[0] or x>nodes[-1]:
        if policy is BoundaryPolicy.STRICT: raise ValueError(f"value {x} outside grid [{nodes[0]}, {nodes[-1]}]")
        x=float(np.clip(x,nodes[0],nodes[-1])); clipped=True
    if x==nodes[-1]: return len(nodes)-2,len(nodes)-1,0.0,1.0,clipped
    j=int(np.searchsorted(nodes,x,side="right")-1); j=max(0,min(j,len(nodes)-2))
    t=(x-nodes[j])/(nodes[j+1]-nodes[j]); return j,j+1,1-t,t,clipped

def _valid_pairs(trees,assignment):
    by={(h.tree_id,h.year):h for h in assignment.heights}; pairs=[]; missing=0
    for t in trees:
        h=by.get((t.tree_id,t.year))
        if h is None or h.is_missing or h.height_m is None: missing+=1
        else: pairs.append((t,float(h.height_m)))
    return pairs,missing

def project_trees_to_grid(trees:Sequence[TreeRecord],assignment:HeightAssignment,grid:ProjectionGrid,
                          boundary_policy:BoundaryPolicy=BoundaryPolicy.STRICT)->ProjectedState:
    policy=BoundaryPolicy(boundary_policy); pairs,missing=_valid_pairs(trees,assignment)
    mass=np.zeros((len(grid.height_m),len(grid.diameter_cm)),dtype=float); clipped_count=0
    for tree,height in pairs:
        h0,h1,ah0,ah1,ch=_bracket(grid.height_m,height,policy)
        d0,d1,ad0,ad1,cd=_bracket(grid.diameter_cm,tree.diameter_cm,policy)
        clipped_count += int(ch or cd)
        for ih,wh in ((h0,ah0),(h1,ah1)):
            for id_,wd in ((d0,ad0),(d1,ad1)):
                mass[ih,id_] += tree.weight_ha*wh*wd
    q=np.outer(trapezoidal_weights(grid.height_m),trapezoidal_weights(grid.diameter_cm))
    density=np.divide(mass,q,out=np.zeros_like(mass),where=q>0)
    warnings=[]
    if missing: warnings.append(f"{missing} tree(s) omitted because height is missing.")
    if clipped_count: warnings.append(f"{clipped_count} tree(s) clipped to grid boundaries.")
    return ProjectedState(grid,density,mass,len(trees),len(pairs),missing,clipped_count,tuple(warnings))

def _dominant_height_atoms(atoms,target=100.0):
    available=sum(w for d,h,w in atoms)
    if available+1e-12<target:return None
    groups={}
    for d,h,w in atoms:groups.setdefault(d,[]).append((h,w))
    remaining=target; num=sel=0.0
    for d in sorted(groups,reverse=True):
        g=groups[d]; gw=sum(w for h,w in g); take=min(remaining,gw); f=take/gw
        num+=sum(h*w*f for h,w in g);sel+=take;remaining-=take
        if remaining<=1e-12:break
    return num/sel

def projection_diagnostics(trees,assignment,state):
    pairs,missing=_valid_pairs(trees,assignment); atoms_in=[(t.diameter_cm,h,t.weight_ha) for t,h in pairs]
    atoms_grid=[]
    for i,h in enumerate(state.grid.height_m):
        for j,d in enumerate(state.grid.diameter_cm):
            w=float(state.nodal_mass_ha[i,j])
            if w>0:atoms_grid.append((float(d),float(h),w))
    def metrics(atoms):
        m=sum(w for d,h,w in atoms); mh=sum(w*h for d,h,w in atoms)/m; md=sum(w*d for d,h,w in atoms)/m
        dg=math.sqrt(sum(w*d*d for d,h,w in atoms)/m); ba=sum(w*math.pi*(d/100)**2/4 for d,h,w in atoms)
        return m,mh,md,dg,ba,_dominant_height_atoms(atoms)
    mi,hi,di,dgi,bai,h0i=metrics(atoms_in); mg,hg,dg,dgg,bag,h0g=metrics(atoms_grid)
    return ProjectionDiagnostics(mi,mg,mg-mi,hi,hg,hg-hi,di,dg,dg-di,dgi,dgg,bai,bag,h0i,h0g,state.clipped_tree_count,missing)
