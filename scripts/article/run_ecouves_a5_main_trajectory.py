#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,hashlib,json,platform,subprocess,sys
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

import numpy as np
import scipy
def root():
 here=Path(__file__).resolve()
 for p in [Path.cwd(),*Path.cwd().parents,*here.parents]:
  if (p/'simulations/article/ecouves_a5').exists():return p
 raise RuntimeError('cannot locate repository root')
ROOT=root();sys.path.insert(0,str(ROOT))

def git_value(*args):
 try:return subprocess.check_output(['git',*args],cwd=ROOT,text=True,stderr=subprocess.DEVNULL).strip()
 except (OSError,subprocess.CalledProcessError):return 'unavailable'

def tracked_worktree_clean():
 try:return subprocess.run(['git','diff','--quiet','--ignore-submodules','HEAD','--'],cwd=ROOT,check=False).returncode==0
 except OSError:return None

def sha256(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
 return h.hexdigest()

def refuse_nonempty_output(path,overwrite):
 path=Path(path)
 if path.exists() and any(path.iterdir()) and not overwrite:
  raise FileExistsError(f'Refusing to overwrite non-empty Q-9F.2 directory: {path}')
 path.mkdir(parents=True,exist_ok=True)

def completed_full_horizon(final_age,target_age,dt):
 return float(final_age)>=float(target_age)-0.5*float(dt)
from simulations.article.ecouves_a5.main_dynamic_trajectory import run_main_trajectory,TARGET_YEARS

def main(argv=None):
 p=argparse.ArgumentParser();base=ROOT/'outputs/article_scenarios/ecouves_a5_solver_compatibility';p.add_argument('--initial-state',type=Path,default=base/'ecouves_a5_native_initial_state_1992.npz');p.add_argument('--native-state-dir',type=Path,default=base);p.add_argument('--output-dir',type=Path,default=ROOT/'outputs/article_scenarios/ecouves_a5_main_trajectory_1992_2020');p.add_argument('--no-progress',action='store_true');p.add_argument('--overwrite',action='store_true');a=p.parse_args(argv)
 progress=None
 if not a.no_progress:
  from tqdm import tqdm;progress=tqdm
 refuse_nonempty_output(a.output_dir,a.overwrite)
 started_at=datetime.now(timezone.utc).isoformat();clean_at_start=tracked_worktree_clean();start=perf_counter();x0,params,context,final,saved,targets,time_rows,comparisons,valid=run_main_trajectory(a.initial_state,a.native_state_dir,progress=progress);elapsed=perf_counter()-start
 def writecsv(name,rows):
  rows=list(rows)
  with (a.output_dir/name).open('w',encoding='utf-8',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 writecsv('ecouves_a5_main_trajectory_time_series.csv',time_rows);writecsv('ecouves_a5_main_trajectory_comparison.csv',comparisons)
 for year,state in saved.items():
  np.savez_compressed(a.output_dir/f'ecouves_a5_simulated_state_{year}.npz',U=state.U,year=year,requested_age={1992:45,1998:51,2016:69,2020:73}[year],actual_age=state.age,step_index=state.step_index,time=state.time)
 metadata={'purpose':'Q-9F.2 main unchanged-parameter trajectory from reconstructed 1992 state','initial_year':1992,'initial_age':45.0,'final_year':2020,'final_age_requested':73.0,'final_age_actual':final.age,'completed_full_horizon':completed_full_horizon(final.age,73.0,params.numerics.time.dt),'steps_run':final.step_index,'dt':params.numerics.time.dt,'elapsed_seconds':elapsed,'started_at_utc':started_at,'dynamic_parameters_recalibrated':False,'height_provider_id':'savine-douglas-fixed-effects','height_provider_replaceable':True,'height_values_are_measured':False,'height_reconstruction':'deterministic provisional reconstruction from the Savine Douglas fixed-effects relation; no residual dispersion simulated','aggregate_observation_source':'GIS Coop stand-level series used by the article workflow','individual_inventory_source':'Ecouves A5 individual-tree inventories transmitted by Francois Ningre','source_discrepancy_policy':'small source differences, including age-label differences, are retained and documented; no silent reconciliation or averaging','age_convention':'GIS Coop convention for simulation ages; individual-inventory labels may differ by about one year','target_years':list(TARGET_YEARS),'numerical_validity':valid,'initial_state_path':str(a.initial_state.resolve()),'initial_state_sha256':sha256(a.initial_state)}
 (a.output_dir/'ecouves_a5_main_trajectory_metadata.json').write_text(json.dumps(metadata,indent=2)+'\n',encoding='utf-8')
 configuration={'scenario':'q9f2_ecouves_a5_main_1992_2020','initial_state_path':str(a.initial_state.resolve()),'native_state_dir':str(a.native_state_dir.resolve()),'output_dir':str(a.output_dir.resolve()),'initial_year':1992,'final_year':2020,'initial_age':45.0,'final_age_target':73.0,'dt':params.numerics.time.dt,'target_years':list(TARGET_YEARS),'dynamic_parameters_recalibrated':False,'height_provider_id':'savine-douglas-fixed-effects'}
 (a.output_dir/'configuration.json').write_text(json.dumps(configuration,indent=2)+'\n',encoding='utf-8')
 reproducibility={'git_branch':git_value('branch','--show-current'),'git_commit':git_value('rev-parse','HEAD'),'tracked_worktree_clean_at_start':clean_at_start,'tracked_worktree_clean_at_end':tracked_worktree_clean(),'python_version':sys.version,'platform':platform.platform(),'numpy_version':np.__version__,'scipy_version':scipy.__version__,'command':' '.join(sys.argv),'started_at_utc':started_at,'elapsed_seconds':elapsed,'initial_state_path':str(a.initial_state.resolve()),'initial_state_sha256':sha256(a.initial_state),'runner_path':str(Path(__file__).resolve()),'runner_sha256':sha256(Path(__file__))}
 (a.output_dir/'reproducibility.json').write_text(json.dumps(reproducibility,indent=2)+'\n',encoding='utf-8')
 indexed={(r['year'],r['metric']):r for r in comparisons};metrics=('N','G','Dm','Dg','Hm','Hq','H0','rho_HD','cumulative_stem_loss')
 lines=['# Q-9F.2 - Trajectoire principale 1992-2020 sans recalibration','',f"- Pas exécutés : {final.step_index};",f"- âge final simulé : {final.age:.8g} ans;",f"- validité numérique : {'oui' if valid else 'non'};",'- paramètres dynamiques recalibrés : non;','- hauteurs cibles : reconstructions provisoires, fournisseur remplaçable.','','| Année | Âge | Variable | Simulation | Cible reconstruite | Résidu relatif |','|---:|---:|:---|---:|---:|---:|']
 for year in TARGET_YEARS:
  for m in metrics:
   r=indexed[(year,m)];rr=r['relative_residual'];lines.append(f"| {year} | {r['requested_age']:g} | {m} | {r['simulated_value']:.8g} | {r['reconstructed_target_value']:.8g} | {'' if rr is None else f'{100*rr:+.3f}%'} |")
 lines += ['','Les écarts mélangent la dynamique du modèle et les limites de la reconstruction provisoire des hauteurs. Aucun coefficient n’est ajusté dans ce lot.','']
 (a.output_dir/'ecouves_a5_main_trajectory_report.md').write_text('\n'.join(lines),encoding='utf-8')
 if not valid:raise RuntimeError('Q-9F.2 failed numerical validity checks')
 print(f'Q-9F.2 outputs written to {a.output_dir}');print(f'steps={final.step_index} elapsed_seconds={elapsed:.3f}')
if __name__=='__main__':main()
