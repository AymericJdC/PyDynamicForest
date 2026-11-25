"""Q-9F.6 audit of global height growth and status-dependent allocation.

The legacy transport flux is driven by height_growth * status * density. The
status is the normalized joint lower-tail cumulative distribution in height and
DBH. It is therefore not a pure DBH rank and must not be labelled as such.
"""
from __future__ import annotations
from dataclasses import asdict,dataclass
from pathlib import Path
import numpy as np
from pydynamicforest.numerics import compute_derived_quantities,product_trapezoidal_weights
from pydynamicforest.observation_operators import physical_dbh_nodes,physical_height_nodes
from pydynamicforest.solver import (
    compute_transport_components_legacy,
    evaluate_model_fields_for_solver,
)
from pydynamicforest.types import State
from simulations.article.parameters import build_parameters
from .hierarchical_height_diagnostics import RELATIVE_DBH_EDGES,RELATIVE_DBH_LABELS

YEARS=(1992,1998,2016,2020)

@dataclass(frozen=True)
class AllocationClass:
 year:int;hierarchy_class:str;density_ha:float;density_share:float
 mean_status:float;mean_height_growth_field:float;mean_effective_height_velocity:float
 growth_status_covariance:float
 mean_height_m:float;mean_dbh_cm:float;height_transport_integral:float
 def record(self):return asdict(self)

def load_state(path:Path,key:str,year:int,age:float)->State:
 if not path.is_file():raise FileNotFoundError(path)
 with np.load(path) as z:U=np.array(z[key],dtype=float,copy=True)
 return State(time=age-45.0,age=age,U=U,step_index=0)

def audit_state(state:State,p,year:int):
 derived=compute_derived_quantities(state,p);fields=evaluate_model_fields_for_solver(state,p)
 if isinstance(fields,dict):height_growth=np.asarray(fields['height_growth'],dtype=float)
 else:height_growth=np.asarray(fields.height_growth,dtype=float)
 components=compute_transport_components_legacy(state,p,derived,fields)
 weights=product_trapezoidal_weights(p);mass=np.maximum(state.U,0)*weights
 h=physical_height_nodes(p);d=physical_dbh_nodes(p,unit='cm');total=mass.sum();dg=np.sqrt(np.sum(mass*d[None,:]**2)/total);relative=d/dg
 effective=height_growth*derived.status_field
 rows=[]
 for lower,upper,label in zip(RELATIVE_DBH_EDGES[:-1],RELATIVE_DBH_EDGES[1:],RELATIVE_DBH_LABELS):
  select=relative>=lower if np.isinf(upper) else ((relative>=lower)&(relative<upper))
  M=mass[:,select];density=M.sum()
  if density>0:
   status=float(np.sum(M*derived.status_field[:,select])/density)
   field=float(np.sum(M*height_growth[:,select])/density)
   velocity=float(np.sum(M*effective[:,select])/density)
   covariance=float(velocity-field*status)
   mh=float(np.sum(M*h[:,None])/density);md=float(np.sum(M*d[None,select])/density)
   transport=float(np.sum(weights[:,select]*components['height'][:,select]))
  else:
   status=field=velocity=covariance=mh=md=float('nan')
   transport=0.0
  rows.append(
   AllocationClass(
    year,label,float(density),float(density/total),
    status,field,velocity,covariance,mh,md,transport
   )
  )
 summary={'year':year,'total_density_ha':float(total),'status_min':float(np.min(derived.status_field)),'status_max':float(np.max(derived.status_field)),'height_growth_field_min':float(np.min(height_growth)),'height_growth_field_max':float(np.max(height_growth)),'height_growth_field_is_constant':bool(np.allclose(height_growth,height_growth.flat[0])),'effective_velocity_min':float(np.min(effective)),'effective_velocity_max':float(np.max(effective)),'height_transport_integral':float(np.sum(weights*components['height'])),'status_definition':'normalized joint lower-tail cumulative distribution in height and DBH','transported_quantity':'status * density','height_flux_velocity':'height_growth_field'}
 return tuple(rows),summary

def run_allocation_audit(simulated_dir:Path,target_dir:Path):
 p=build_parameters();rows=[];summaries=[]
 for year,age in ((1992,45.0),(1998,51.0),(2016,69.0),(2020,73.0)):
  path=(target_dir/f'ecouves_a5_native_initial_state_{year}.npz') if year==1992 else (simulated_dir/f'ecouves_a5_simulated_state_{year}.npz')
  key='U0' if year==1992 else 'U';state=load_state(path,key,year,age);r,s=audit_state(state,p,year);rows.extend(x.record() for x in r);summaries.append(s)
 return tuple(rows),tuple(summaries)
