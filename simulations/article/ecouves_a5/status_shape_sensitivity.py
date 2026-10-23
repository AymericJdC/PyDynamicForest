"""Q-9F.7 sensitivity to the shape of height-status allocation only.

The transformation S**gamma is applied exclusively to height transport.
DBH transport, mortality allocation, coefficient fields, diffusion and all
numerical settings retain the baseline status and parameters.
"""
from __future__ import annotations
from dataclasses import dataclass,asdict,replace
from pathlib import Path
import numpy as np
from scipy.sparse.linalg import spsolve
from pydynamicforest.initial_conditions import build_initial_state
from pydynamicforest.numerics import compute_derived_quantities
from pydynamicforest.solver import (advance_one_step_sparse_legacy,assemble_sparse_legacy_system,compute_transport_components_legacy,evaluate_model_fields_for_solver)
from pydynamicforest.model import evaluate_model_fields
from pydynamicforest.types import SimulationContext,OutputSpecification,State
from simulations.article.parameters import build_parameters
from .short_dynamic_control import load_native_initial_condition
from .main_dynamic_trajectory import YEAR_TO_AGE,TARGET_YEARS,load_empirical_targets,nearest_target_steps,summarize_density
from .distributional_diagnostics import diagnose_year
from .hierarchical_height_diagnostics import hierarchy_profile,compare_profiles

GAMMAS=(0.75,1.0,1.25)
SIGNATURE_METRICS=('N','G','Dm','Dg','Hm','Hq','H0','rho_HD')

@dataclass(frozen=True)
class StatusShapeCase:
 gamma:float
 @property
 def name(self):return f'height_status_gamma_{self.gamma:.2f}'
 def record(self):return {'case':self.name,'gamma':self.gamma}

def transformed_status(status,gamma):
 if gamma<=0 or not np.isfinite(gamma):raise ValueError('gamma must be finite and positive')
 clipped=np.clip(np.asarray(status,dtype=float),0.0,1.0)
 return clipped**float(gamma)

def advance_one_step_height_status_shape(state,p,gamma):
 if gamma==1.0:return advance_one_step_sparse_legacy(state,p)
 dt=p.numerics.time.dt;derived=compute_derived_quantities(state,p)
 transformed=replace(derived,status_field=transformed_status(derived.status_field,gamma))
 fields_current=evaluate_model_fields_for_solver(state,p)
 baseline_parts=compute_transport_components_legacy(state,p,derived,fields_current)
 transformed_parts=compute_transport_components_legacy(state,p,transformed,fields_current)
 transport=transformed_parts['height']+baseline_parts['dbh']
 fields_next=evaluate_model_fields(p,state.time+dt)
 A,b=assemble_sparse_legacy_system(state,p,derived,fields_next,transport)
 U=spsolve(A,b).reshape((p.numerics.grid.nx,p.numerics.grid.ny))
 return State(state.time+dt,state.age+dt,U,state.step_index+1)

def selected_cases():return tuple(StatusShapeCase(x) for x in GAMMAS)

def run_case(case,initial_state_path,native_dir,progress=None):
 p=build_parameters();x0=load_native_initial_condition(initial_state_path,year=1992,age=45.0,provider_id='savine-douglas-fixed-effects')
 c=SimulationContext(case.name,45.0,73.0,OutputSpecification(observation_ages=list(YEAR_TO_AGE.values()),save_full_trajectory=False),description='Q-9F.7 height-only status-shape sensitivity; no calibration.')
 state=build_initial_state(x0,p,c);targets=load_empirical_targets(native_dir,p);steps=nearest_target_steps(p.numerics.time.dt);final_step=steps[2020];saved={1992:State(state.time,state.age,state.U.copy(),0)}
 iterator=range(final_step+1)
 if progress is not None:iterator=progress(iterator,total=final_step+1,desc=case.name,leave=False)
 for step in iterator:
  for year,target_step in steps.items():
   if target_step==step and year not in saved:saved[year]=State(state.time,state.age,state.U.copy(),state.step_index)
  if step==final_step:break
  state=advance_one_step_height_status_shape(state,p,case.gamma)
 rows=[];hierarchy=[]
 for year in TARGET_YEARS[1:]:
  summary=summarize_density(saved[year].U,p);target=targets[year]
  with np.load(Path(native_dir)/f'ecouves_a5_native_initial_state_{year}.npz') as z:target_U=np.array(z['U0'],copy=True)
  comps,_,_,_,_=diagnose_year(saved[year].U,target_U,p,year);dist={x.dimension:x for x in comps}
  for metric in SIGNATURE_METRICS:
   value=getattr(summary,metric);reference=getattr(target,metric);rows.append({**case.record(),'year':year,'metric':metric,'value':value,'target':reference,'residual':value-reference,'relative_residual':(value-reference)/reference if reference else None})
  for metric,value in (('W1_dbh_cm',dist['dbh_cm'].wasserstein_1),('W1_height_m',dist['height_m'].wasserstein_1),('KS_height',dist['height_m'].cdf_max_distance)):
   rows.append({**case.record(),'year':year,'metric':metric,'value':value,'target':0.0,'residual':value,'relative_residual':None})
  sim_profile=hierarchy_profile(saved[year].U,p,year=year,source=case.name);target_profile=hierarchy_profile(target_U,p,year=year,source='target')
  for item in compare_profiles(sim_profile,target_profile):hierarchy.append({**case.record(),**item.record()})
 return tuple(rows),tuple(hierarchy)
