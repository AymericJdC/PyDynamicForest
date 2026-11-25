"""Q-9F.2 unchanged-parameter trajectory from reconstructed 1992 to 2020 states."""
from __future__ import annotations
from dataclasses import dataclass,asdict
from pathlib import Path
import numpy as np
from pydynamicforest.initial_conditions import build_initial_state
from pydynamicforest.numerics import compute_derived_quantities
from pydynamicforest.observation_operators import (stand_density,mean_height,mean_dbh,quadratic_mean_dbh,basal_area_consistent,continuous_dominant_height,height_dbh_correlation,height_variance)
from pydynamicforest.solver import advance_one_step_sparse_legacy
from pydynamicforest.types import SimulationContext,OutputSpecification,State
from simulations.article.parameters import build_parameters
from .short_dynamic_control import load_native_initial_condition

YEAR_TO_AGE={1992:45.0,1998:51.0,2016:69.0,2020:73.0}
TARGET_YEARS=(1992,1998,2016,2020)

@dataclass(frozen=True)
class StandSummary:
 N:float; G:float; Dm:float; Dg:float; sigma_D:float; Hm:float; Hq:float; H0:float; rho_HD:float; H0_minus_Hm:float
 def record(self):return asdict(self)

def summarize_density(U,p)->StandSummary:
 N=stand_density(U,p);Dm=mean_dbh(U,p,unit='cm');Dg=quadratic_mean_dbh(U,p,unit='cm');Hm=mean_height(U,p);Hq=float(np.sqrt(height_variance(U,p)+Hm*Hm));H0=continuous_dominant_height(U,p)
 return StandSummary(N,basal_area_consistent(U,p),Dm,Dg,float(np.sqrt(max(0.0,Dg*Dg-Dm*Dm))),Hm,Hq,H0,height_dbh_correlation(U,p),H0-Hm)

def load_empirical_targets(native_dir:str|Path,p)->dict[int,StandSummary]:
 directory=Path(native_dir);out={}
 for year in TARGET_YEARS:
  path=directory/f'ecouves_a5_native_initial_state_{year}.npz'
  if not path.is_file():raise FileNotFoundError(path)
  with np.load(path) as z:
   U=np.array(z['U0'],dtype=float,copy=True);stored=int(z['year']);age=float(z['gis_age'])
  if stored!=year or abs(age-YEAR_TO_AGE[year])>1e-12:raise ValueError(f'inconsistent native-state provenance for {year}')
  out[year]=summarize_density(U,p)
 return out

def nearest_target_steps(dt:float)->dict[int,int]:
 return {year:int(round((age-YEAR_TO_AGE[1992])/dt)) for year,age in YEAR_TO_AGE.items()}

def run_main_trajectory(initial_state_path:str|Path,native_dir:str|Path,*,progress=None):
 p=build_parameters();x0=load_native_initial_condition(initial_state_path,year=1992,age=45.0,provider_id='savine-douglas-fixed-effects')
 c=SimulationContext('q9f2_ecouves_a5_main_1992_2020',45.0,73.0,OutputSpecification(observation_ages=list(YEAR_TO_AGE.values()),save_full_trajectory=False),description='Unchanged dynamic parameters; empirical 1992 initial state.')
 state=build_initial_state(x0,p,c);targets=load_empirical_targets(native_dir,p);steps=nearest_target_steps(p.numerics.time.dt);final_step=steps[2020]
 if final_step>p.numerics.time.n_steps:raise ValueError('configured article horizon is too short')
 saved={1992:State(state.time,state.age,state.U.copy(),state.step_index)};time_rows=[]
 iterator=range(final_step+1)
 if progress is not None: iterator=progress(iterator,total=final_step+1,desc='Q-9F.2 main trajectory')
 for step in iterator:
  if step%100==0 or step in steps.values():
   s=summarize_density(state.U,p);derived=compute_derived_quantities(state,p);time_rows.append({'step_index':state.step_index,'time':state.time,'age':state.age,**s.record(),'minimum_density':float(np.min(state.U)),'status_minimum':float(np.min(derived.status_field)),'status_maximum':float(np.max(derived.status_field))})
  for year,target_step in steps.items():
   if target_step==step and year not in saved:saved[year]=State(state.time,state.age,state.U.copy(),state.step_index)
  if step==final_step:break
  state=advance_one_step_sparse_legacy(state,p)
 comparisons=[]
 initial_N=targets[1992].N
 for year in TARGET_YEARS:
  sim=summarize_density(saved[year].U,p);obs=targets[year]
  for metric in StandSummary.__dataclass_fields__:
   sv=getattr(sim,metric);ov=getattr(obs,metric);comparisons.append({'year':year,'requested_age':YEAR_TO_AGE[year],'actual_simulated_age':saved[year].age,'step_index':saved[year].step_index,'metric':metric,'simulated_value':sv,'reconstructed_target_value':ov,'residual':sv-ov,'relative_residual':(sv-ov)/ov if ov!=0 else None})
  comparisons.append({'year':year,'requested_age':YEAR_TO_AGE[year],'actual_simulated_age':saved[year].age,'step_index':saved[year].step_index,'metric':'cumulative_stem_loss','simulated_value':initial_N-sim.N,'reconstructed_target_value':initial_N-obs.N,'residual':obs.N-sim.N,'relative_residual':None})
 valid=all(r['minimum_density']>=-p.numerics.positivity_tolerance and r['status_minimum']>=-1e-12 and r['status_maximum']<=1+1e-12 for r in time_rows)
 return x0,p,c,state,saved,targets,tuple(time_rows),tuple(comparisons),valid
