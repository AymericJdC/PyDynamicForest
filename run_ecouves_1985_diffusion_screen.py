#!/usr/bin/env python3
"""Screen diffusion for the calibrated Ecouves A5 trajectory.

K=0.0377 yr-1 and c_phi=0.0165 m yr-1 are fixed. The script first performs a
one-step smoke test at D=0. If the sparse legacy solver accepts D=0 and returns
a finite non-negative state, it runs full trajectories at D=0, 2.5e-6 and
5e-6. The frozen D=1e-5 trajectory is read as baseline.
"""
from __future__ import annotations
import argparse, copy, csv, hashlib, importlib.util, json, math, sys
from pathlib import Path
import numpy as np

K=0.0377
CPHI=0.0165
VALUES=(0.0,2.5e-6,5.0e-6)
BASELINE=1.0e-5
YEARS=(1992,1998,2016,2020)
METRICS=('N','G','Dm','sigma_D','Hm','H0_minus_Hm','rho_HD')

def load(path,name):
 spec=importlib.util.spec_from_file_location(name,path)
 if spec is None or spec.loader is None: raise RuntimeError(path)
 m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def read(path):
 with path.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def idx(rows):return {(int(float(r['year'])),r['metric']):r for r in rows}
def logscore(rows,metric):
 i=idx(rows);return sum((math.log(float(i[y,metric]['simulated_value']))-math.log(float(i[y,metric]['reconstructed_target_value'])))**2 for y in YEARS)
def rr(rows,metric):
 i=idx(rows);v=[float(i[y,metric]['simulated_value'])/float(i[y,metric]['reconstructed_target_value'])-1 for y in YEARS];return math.sqrt(sum(x*x for x in v)/len(v))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def boundary_mass_fraction(npz_path,params):
 from pydynamicforest.numerics import product_trapezoidal_weights
 with np.load(npz_path,allow_pickle=False) as z: U=np.array(z['U'],float)
 mass=U*product_trapezoidal_weights(params);total=float(mass.sum())
 return float(mass[-2:,:].sum()/total),float(mass[:,-2:].sum()/total)

def main():
 p=argparse.ArgumentParser();p.add_argument('--runner',type=Path,required=True);p.add_argument('--initial-state',type=Path,required=True);p.add_argument('--target-state-dir',type=Path,required=True);p.add_argument('--baseline-dir',type=Path,required=True);p.add_argument('--output-root',type=Path,required=True);a=p.parse_args()
 root=Path.cwd().resolve();sys.path.insert(0,str(root))
 from simulations.article.config import ARTICLE_CONFIG
 from simulations.article.parameters import build_parameters as canonical
 from pydynamicforest.initial_conditions import build_initial_state
 from pydynamicforest.solver import advance_one_step_sparse_legacy
 from pydynamicforest.types import OutputSpecification,SimulationContext
 out=a.output_root.resolve()
 if out.exists():raise FileExistsError(out)
 out.mkdir(parents=True)
 runner_path=a.runner.resolve();base_dir=a.baseline_dir.resolve()
 scenarios=[]
 base_rows=read(base_dir/'ecouves_a5_frozen_1985_2020_comparison.csv');scenarios.append((BASELINE,base_dir,base_rows))
 smoke={}
 for value in VALUES:
  config=copy.deepcopy(ARTICLE_CONFIG);config['model']['mortality']['value']=K;config['model']['dbh_growth']['physical_rate']=CPHI;config['model']['diffusion']['value']=value
  params=canonical(copy.deepcopy(config));runner=load(runner_path,f'runner_D_{str(value).replace(".","_")}')
  # D=0 smoke test before the full run.
  if value==0.0:
   x0,_=runner.load_initial(a.initial_state.resolve(),params)
   context=SimulationContext('diffusion_zero_smoke',37.0,72.0,OutputSpecification(observation_ages=[37.0],save_full_trajectory=False))
   state=build_initial_state(x0,params,context)
   next_state=advance_one_step_sparse_legacy(state,params)
   ok=bool(np.all(np.isfinite(next_state.U)) and np.min(next_state.U)>=-params.numerics.positivity_tolerance)
   smoke={'accepted':ok,'minimum_density_after_one_step':float(np.min(next_state.U)),'mass_before':float(state.U.sum()),'mass_after':float(next_state.U.sum())}
   if not ok:raise RuntimeError('D=0 smoke test failed')
  def build(_config=None,frozen=config):return canonical(copy.deepcopy(frozen))
  runner.build_parameters=build
  d=out/f'D_{value:.7f}'
  code=runner.main(['--initial-state',str(a.initial_state.resolve()),'--target-state-dir',str(a.target_state_dir.resolve()),'--output-dir',str(d),'--no-progress'])
  if code:raise RuntimeError(code)
  comp=read(d/'ecouves_a5_frozen_1985_2020_comparison.csv')
  meta=d/'ecouves_a5_frozen_1985_2020_metadata.json';m=json.loads(meta.read_text());m.update({'dynamic_parameters_recalibrated':True,'calibrated_parameters':['mortality.value','dbh_growth.physical_rate','diffusion.value'],'mortality_coefficient_per_year':K,'dbh_growth_physical_rate_m_per_year':CPHI,'diffusion_value_normalized_coordinates':value,'diffusion_screen_role':'diagnostic and calibration on DBH dispersion'});meta.write_text(json.dumps(m,indent=2)+'\n')
  scenarios.append((value,d,comp))
 rows=[]
 for value,d,comp in scenarios:
  params_config=copy.deepcopy(ARTICLE_CONFIG);params_config['model']['mortality']['value']=K;params_config['model']['dbh_growth']['physical_rate']=CPHI;params_config['model']['diffusion']['value']=value;params=canonical(params_config)
  r={'diffusion_value':value,'sigma_D_log_score':logscore(comp,'sigma_D'),'output_directory':str(d)}
  for metric in METRICS:r[f'{metric}_relative_rmse']=rr(comp,metric)
  for year in YEARS:
   npz=d/(f'ecouves_a5_frozen_state_{year}.npz' if value==BASELINE else f'ecouves_a5_frozen_state_{year}.npz')
   ph,pd=boundary_mass_fraction(npz,params);r[f'height_upper2_mass_fraction_{year}']=ph;r[f'dbh_upper2_mass_fraction_{year}']=pd
  rows.append(r)
 rows.sort(key=lambda r:r['sigma_D_log_score'])
 path=out/'diffusion_screen_summary.csv'
 with path.open('w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 best=rows[0]
 report=['# Diffusion screening, Ecouves A5 1985--2020','',f'K={K}, c_phi={CPHI}.','',f'D=0 smoke test accepted: **{smoke.get("accepted")}**.','', '| D | sigma_D score | sigma_D RMSE | Dm RMSE | N RMSE | H0-Hm RMSE | rho_HD RMSE | max upper-height mass fraction | max upper-DBH mass fraction |','|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
 for r in rows:report.append(f"| {r['diffusion_value']:.7g} | {r['sigma_D_log_score']:.8f} | {100*r['sigma_D_relative_rmse']:.3f}% | {100*r['Dm_relative_rmse']:.3f}% | {100*r['N_relative_rmse']:.3f}% | {100*r['H0_minus_Hm_relative_rmse']:.3f}% | {100*r['rho_HD_relative_rmse']:.3f}% | {max(r[f'height_upper2_mass_fraction_{y}'] for y in YEARS):.3e} | {max(r[f'dbh_upper2_mass_fraction_{y}'] for y in YEARS):.3e} |")
 report += ['',f"Selected by sigma_D criterion: **D={best['diffusion_value']:.7g}**.",'','D=0 is a diagnostic endpoint. Retain it as the article value only if numerical validity, boundary masses and the other distributed diagnostics remain acceptable.']
 (out/'diffusion_screen_report.md').write_text('\n'.join(report)+'\n')
 manifest={'fixed_K':K,'fixed_cphi':CPHI,'tested_diffusion':[BASELINE,*VALUES],'criterion':'sum squared log DBH-standard-deviation residuals','selected_diffusion':best['diffusion_value'],'D_zero_smoke_test':smoke,'runner':str(runner_path),'baseline_sha256':sha(base_dir/'ecouves_a5_frozen_1985_2020_comparison.csv')}
 (out/'diffusion_screen_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 print(f'[OK] {path}');print(f"[VERDICT] D_zero_accepted={smoke.get('accepted')} selected_D={best['diffusion_value']:.7g} sigma_D_log_score={best['sigma_D_log_score']:.8f}")
if __name__=='__main__':main()
