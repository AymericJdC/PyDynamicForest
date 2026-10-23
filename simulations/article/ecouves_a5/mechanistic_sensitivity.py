"""Q-9F.4 centred OAT mechanistic sensitivity from the empirical 1992 state."""
from __future__ import annotations
from copy import deepcopy
from dataclasses import dataclass,asdict
from pathlib import Path
import numpy as np
from pydynamicforest.initial_conditions import build_initial_state
from pydynamicforest.solver import advance_one_step_sparse_legacy
from pydynamicforest.types import SimulationContext,OutputSpecification,State
from simulations.article.config import ARTICLE_CONFIG
from simulations.article.parameters import build_parameters
from .short_dynamic_control import load_native_initial_condition
from .main_dynamic_trajectory import YEAR_TO_AGE,TARGET_YEARS,load_empirical_targets,nearest_target_steps,summarize_density
from .distributional_diagnostics import diagnose_year

MECHANISMS=('height_growth','dbh_growth','diffusion','mortality')
MULTIPLIERS=(0.8,1.2)
PARAMETER_PATHS={'height_growth':('height_growth','physical_rate'),'dbh_growth':('dbh_growth','physical_rate'),'diffusion':('diffusion','value'),'mortality':('mortality','value')}
SIGNATURE_METRICS=('N','G','Dm','Dg','Hm','Hq','H0','rho_HD')

@dataclass(frozen=True)
class SensitivityCase:
 mechanism:str; multiplier:float; baseline_value:float; perturbed_value:float
 @property
 def name(self):return f'{self.mechanism}_x{self.multiplier:.2f}'
 def record(self):return {'case':self.name,**asdict(self)}

def make_case(mechanism,multiplier):
 if mechanism not in PARAMETER_PATHS:raise ValueError(f'unknown mechanism: {mechanism}')
 if multiplier not in MULTIPLIERS:raise ValueError(f'multiplier must be one of {MULTIPLIERS}')
 section,field=PARAMETER_PATHS[mechanism];baseline=float(ARTICLE_CONFIG['model'][section][field])
 return SensitivityCase(mechanism,float(multiplier),baseline,baseline*float(multiplier))

def case_parameters(case):
 config=deepcopy(ARTICLE_CONFIG);section,field=PARAMETER_PATHS[case.mechanism];config['model'][section][field]=case.perturbed_value
 config['name']=f'q9f4_ecouves_a5_{case.name}';config['description']='Centred OAT screening from reconstructed 1992 state; not calibration.'
 return build_parameters(config)

def selected_cases():return tuple(make_case(m,x) for m in MECHANISMS for x in MULTIPLIERS)

def run_case(case,initial_state_path,native_dir,progress=None):
 p=case_parameters(case);x0=load_native_initial_condition(initial_state_path,year=1992,age=45.0,provider_id='savine-douglas-fixed-effects')
 c=SimulationContext(case.name,45.0,73.0,OutputSpecification(observation_ages=list(YEAR_TO_AGE.values()),save_full_trajectory=False),description='Q-9F.4 OAT screening only.')
 state=build_initial_state(x0,p,c);targets=load_empirical_targets(native_dir,p);steps=nearest_target_steps(p.numerics.time.dt);final_step=steps[2020];saved={1992:State(state.time,state.age,state.U.copy(),0)}
 iterator=range(final_step+1)
 if progress is not None:iterator=progress(iterator,total=final_step+1,desc=case.name,leave=False)
 for step in iterator:
  for year,target_step in steps.items():
   if target_step==step and year not in saved:saved[year]=State(state.time,state.age,state.U.copy(),state.step_index)
  if step==final_step:break
  state=advance_one_step_sparse_legacy(state,p)
 rows=[]
 for year in TARGET_YEARS[1:]:
  summary=summarize_density(saved[year].U,p);target=targets[year]
  comps,_,_,_,_=diagnose_year(saved[year].U,load_target_state(native_dir,year),p,year);dist={c.dimension:c for c in comps}
  for metric in SIGNATURE_METRICS:
   value=getattr(summary,metric);reference=getattr(target,metric);rows.append({**case.record(),'year':year,'metric':metric,'value':value,'target':reference,'residual':value-reference,'relative_residual':(value-reference)/reference if reference else None})
  for metric,value in (('W1_dbh_cm',dist['dbh_cm'].wasserstein_1),('KS_dbh',dist['dbh_cm'].cdf_max_distance),('W1_height_m',dist['height_m'].wasserstein_1),('KS_height',dist['height_m'].cdf_max_distance)):
   rows.append({**case.record(),'year':year,'metric':metric,'value':value,'target':0.0,'residual':value,'relative_residual':None})
 return tuple(rows)

def load_target_state(native_dir,year):
 path=Path(native_dir)/f'ecouves_a5_native_initial_state_{year}.npz'
 with np.load(path) as z:return np.array(z['U0'],dtype=float,copy=True)

def centred_elasticities(rows):
 indexed={(r['mechanism'],r['multiplier'],r['year'],r['metric']):r for r in rows};out=[];delta=MULTIPLIERS[1]-MULTIPLIERS[0]
 for mechanism in MECHANISMS:
  for year in TARGET_YEARS[1:]:
   for metric in SIGNATURE_METRICS+('W1_dbh_cm','KS_dbh','W1_height_m','KS_height'):
    low=indexed[(mechanism,MULTIPLIERS[0],year,metric)]['value'];high=indexed[(mechanism,MULTIPLIERS[1],year,metric)]['value'];mid=0.5*(high+low)
    out.append({'mechanism':mechanism,'year':year,'metric':metric,'low_value':low,'high_value':high,'centred_difference':high-low,'elasticity':(high-low)/(delta*mid) if mid else None})
 return tuple(out)
