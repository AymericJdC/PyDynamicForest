"""Diagnostic completion for Q-9F.7 status-shape experiments.

The decomposition is deliberately descriptive. The implicit finite-difference
step couples transport, diffusion and mortality, so instantaneous integrals are
not claimed to add exactly to the realised one-step mass change.
"""
from __future__ import annotations
from dataclasses import dataclass,asdict,replace
from pathlib import Path
import numpy as np
from pydynamicforest.initial_conditions import build_initial_state
from pydynamicforest.numerics import compute_derived_quantities,product_trapezoidal_weights
from pydynamicforest.solver import compute_transport_components_legacy,evaluate_model_fields_for_solver
from pydynamicforest.types import SimulationContext,OutputSpecification
from simulations.article.parameters import build_parameters
from .short_dynamic_control import load_native_initial_condition
from .status_shape_sensitivity import advance_one_step_height_status_shape,transformed_status

GAMMAS=(0.75,1.0,1.25)
CHECKPOINT_AGES=(45.0,45.0051,45.051,45.51,46.0,51.0,69.0,73.0)
ABSOLUTE_MASS_ALERT_HA=1.0
RELATIVE_MASS_ALERT=1e-3

@dataclass(frozen=True)
class MassBalanceRow:
 gamma:float;step_index:int;time:float;age_before:float;age_after:float
 density_before:float;density_after:float;realised_density_change:float
 baseline_next_density:float;alternative_minus_baseline_next_density:float
 height_transport_integral_baseline:float;height_transport_integral_transformed:float
 dbh_transport_integral_baseline:float;mortality_sink_integral_baseline:float
 diffusion_field_min:float;diffusion_field_max:float
 status_min:float;status_max:float;transformed_status_min:float;transformed_status_max:float
 minimum_density_before:float;minimum_density_after:float;maximum_density_after:float
 cumulative_density_change:float;absolute_alert:bool;relative_alert:bool
 def record(self):return asdict(self)

def _field(fields,name):
 if isinstance(fields,dict):return np.asarray(fields[name],dtype=float)
 return np.asarray(getattr(fields,name),dtype=float)

def diagnostic_terms(state,p,gamma):
 derived=compute_derived_quantities(state,p);fields=evaluate_model_fields_for_solver(state,p);weights=product_trapezoidal_weights(p)
 transformed=replace(derived,status_field=transformed_status(derived.status_field,gamma))
 baseline=compute_transport_components_legacy(state,p,derived,fields);alternative=compute_transport_components_legacy(state,p,transformed,fields)
 mortality=_field(fields,'mortality');diffusion=_field(fields,'diffusion')
 mortality_sink=float(np.sum(weights*mortality*derived.status_field*np.maximum(state.U,0.0)))
 return {'density':float(np.sum(weights*state.U)),'status_min':float(np.min(derived.status_field)),'status_max':float(np.max(derived.status_field)),'transformed_status_min':float(np.min(transformed.status_field)),'transformed_status_max':float(np.max(transformed.status_field)),'height_transport_integral_baseline':float(np.sum(weights*baseline['height'])),'height_transport_integral_transformed':float(np.sum(weights*alternative['height'])),'dbh_transport_integral_baseline':float(np.sum(weights*baseline['dbh'])),'mortality_sink_integral_baseline':mortality_sink,'diffusion_field_min':float(np.min(diffusion)),'diffusion_field_max':float(np.max(diffusion))}

def run_mass_balance(initial_state_path:Path,gamma:float,*,final_age:float=73.0,record_every:int=100):
 p=build_parameters();x0=load_native_initial_condition(initial_state_path,year=1992,age=45.0,provider_id='savine-douglas-fixed-effects');c=SimulationContext(f'q9f7_balance_gamma_{gamma:.2f}',45.0,final_age,OutputSpecification(observation_ages=[],save_full_trajectory=False),description='Q-9F.7 diagnostic only.')
 state=build_initial_state(x0,p,c);initial_density=diagnostic_terms(state,p,gamma)['density'];rows=[];first_alert=None;final_step=int(round((final_age-45.0)/p.numerics.time.dt))
 checkpoints={int(round((age-45.0)/p.numerics.time.dt)) for age in CHECKPOINT_AGES if age<=final_age+1e-12}
 for step in range(final_step):
  terms=diagnostic_terms(state,p,gamma);baseline_next=advance_one_step_height_status_shape(state,p,1.0);next_state=advance_one_step_height_status_shape(state,p,gamma)
  weights=product_trapezoidal_weights(p);n0=terms['density'];n1=float(np.sum(weights*next_state.U));nb=float(np.sum(weights*baseline_next.U));delta=n1-n0;cumulative=n1-initial_density
  alert_abs=abs(cumulative)>=ABSOLUTE_MASS_ALERT_HA;alert_rel=abs(cumulative)/initial_density>=RELATIVE_MASS_ALERT
  new_alert = first_alert is None and (alert_abs or alert_rel)
  if new_alert:
   first_alert = {
    'gamma': gamma,
    'step_index': step + 1,
    'age': next_state.age,
    'cumulative_density_change': cumulative,
    'relative_change': cumulative / initial_density,
   }
  if step < 10 or (step + 1) % record_every == 0 or (step + 1) in checkpoints or new_alert:
   rows.append(MassBalanceRow(gamma,step,state.time,state.age,next_state.age,n0,n1,delta,nb,n1-nb,terms['height_transport_integral_baseline'],terms['height_transport_integral_transformed'],terms['dbh_transport_integral_baseline'],terms['mortality_sink_integral_baseline'],terms['diffusion_field_min'],terms['diffusion_field_max'],terms['status_min'],terms['status_max'],terms['transformed_status_min'],terms['transformed_status_max'],float(np.min(state.U)),float(np.min(next_state.U)),float(np.max(next_state.U)),cumulative,alert_abs,alert_rel))
  state=next_state
 return tuple(r.record() for r in rows),first_alert,{'gamma':gamma,'initial_density':initial_density,'final_density':float(np.sum(product_trapezoidal_weights(p)*state.U)),'final_age':state.age,'steps':state.step_index,'first_alert':first_alert}
