"""Q-9F.1 short dynamic control from the reconstructed 1992 native state."""
from __future__ import annotations
from dataclasses import dataclass,asdict
from pathlib import Path
import numpy as np
from pydynamicforest.initial_conditions import build_initial_state
from pydynamicforest.numerics import compute_derived_quantities
from pydynamicforest.observation_operators import (stand_density,mean_height,mean_dbh,quadratic_mean_dbh,basal_area_consistent,continuous_dominant_height,height_dbh_correlation)
from pydynamicforest.solver import advance_one_step_sparse_legacy
from pydynamicforest.types import InitialCondition,SimulationContext,OutputSpecification
from simulations.article.parameters import build_parameters

@dataclass(frozen=True)
class ShortControlRow:
 step_index:int; time:float; age:float; stand_density:float; mean_height_m:float; mean_dbh_cm:float; quadratic_mean_dbh_cm:float; basal_area_m2_ha:float; dominant_height_m:float; height_dbh_correlation:float; minimum_density:float; maximum_density:float; status_minimum:float; status_maximum:float
 def record(self):return asdict(self)

def load_native_initial_condition(path:str|Path,*,year:int=1992,age:float=45.0,provider_id:str='replaceable-upstream-provider')->InitialCondition:
 p=Path(path)
 if not p.is_file():raise FileNotFoundError(p)
 with np.load(p) as z:
  if 'U0' not in z.files:raise KeyError('native state file does not contain U0')
  U0=np.array(z['U0'],dtype=float,copy=True)
  stored_year=int(z['year']) if 'year' in z.files else year
  stored_age=float(z['gis_age']) if 'gis_age' in z.files else age
 if stored_year!=year or abs(stored_age-age)>1e-12:raise ValueError('native state provenance does not match requested year and age')
 return InitialCondition(name='ecouves_a5_1992_reconstructed',initial_age=age,mass_target=float('nan'),distribution_kind='precomputed_empirical_height_dbh',distribution_parameters={'inventory_year':year,'height_provider_id':provider_id,'axis_order':'height_dbh','density_coordinates':'normalized'},source=str(p),description='Q-9F.1 reconstructed initial state; dynamic parameters unchanged.',U0=U0)

def summarize(state,p)->ShortControlRow:
 derived=compute_derived_quantities(state,p)
 return ShortControlRow(state.step_index,state.time,state.age,stand_density(state.U,p),mean_height(state.U,p),mean_dbh(state.U,p,unit='cm'),quadratic_mean_dbh(state.U,p,unit='cm'),basal_area_consistent(state.U,p),continuous_dominant_height(state.U,p),height_dbh_correlation(state.U,p),float(np.min(state.U)),float(np.max(state.U)),float(np.min(derived.status_field)),float(np.max(derived.status_field)))

def run_short_dynamic_control(path:str|Path,*,n_steps:int=5,year:int=1992,age:float=45.0,provider_id:str='replaceable-upstream-provider'):
 if n_steps<1:raise ValueError('n_steps must be positive')
 p=build_parameters();x0=load_native_initial_condition(path,year=year,age=age,provider_id=provider_id)
 c=SimulationContext(name='q9f1_ecouves_a5_short_control',initial_age=age,final_age=age+n_steps*p.numerics.time.dt,output=OutputSpecification(observation_ages=[],save_full_trajectory=False),description='Short numerical control only; no calibration.')
 state=build_initial_state(x0,p,c)
 if state.U is x0.U0:raise RuntimeError('initial-state builder must copy U0')
 rows=[summarize(state,p)]
 for _ in range(n_steps):
  state=advance_one_step_sparse_legacy(state,p);rows.append(summarize(state,p))
 return x0,p,c,state,tuple(rows)
