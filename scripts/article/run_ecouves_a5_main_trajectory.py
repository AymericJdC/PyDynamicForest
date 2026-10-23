#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,json,sys
from pathlib import Path
from time import perf_counter
def root():
 here=Path(__file__).resolve()
 for p in [Path.cwd(),*Path.cwd().parents,*here.parents]:
  if (p/'simulations/article/ecouves_a5').exists():return p
 raise RuntimeError('cannot locate repository root')
ROOT=root();sys.path.insert(0,str(ROOT))
from simulations.article.ecouves_a5.main_dynamic_trajectory import run_main_trajectory,TARGET_YEARS

def main(argv=None):
 p=argparse.ArgumentParser();base=ROOT/'outputs/article_scenarios/ecouves_a5_solver_compatibility';p.add_argument('--initial-state',type=Path,default=base/'ecouves_a5_native_initial_state_1992.npz');p.add_argument('--native-state-dir',type=Path,default=base);p.add_argument('--output-dir',type=Path,default=ROOT/'outputs/article_scenarios/ecouves_a5_main_trajectory_1992_2020');p.add_argument('--no-progress',action='store_true');a=p.parse_args(argv)
 progress=None
 if not a.no_progress:
  from tqdm import tqdm;progress=tqdm
 start=perf_counter();x0,params,context,final,saved,targets,time_rows,comparisons,valid=run_main_trajectory(a.initial_state,a.native_state_dir,progress=progress);elapsed=perf_counter()-start;a.output_dir.mkdir(parents=True,exist_ok=True)
 def writecsv(name,rows):
  rows=list(rows)
  with (a.output_dir/name).open('w',encoding='utf-8',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 writecsv('ecouves_a5_main_trajectory_time_series.csv',time_rows);writecsv('ecouves_a5_main_trajectory_comparison.csv',comparisons)
 for year,state in saved.items():
  import numpy as np;np.savez_compressed(a.output_dir/f'ecouves_a5_simulated_state_{year}.npz',U=state.U,year=year,requested_age={1992:45,1998:51,2016:69,2020:73}[year],actual_age=state.age,step_index=state.step_index,time=state.time)
 metadata={'purpose':'Q-9F.2 main unchanged-parameter trajectory from reconstructed 1992 state','initial_year':1992,'initial_age':45.0,'final_year':2020,'final_age_requested':73.0,'final_age_actual':final.age,'steps_run':final.step_index,'dt':params.numerics.time.dt,'elapsed_seconds':elapsed,'dynamic_parameters_recalibrated':False,'height_provider_id':'savine-douglas-fixed-effects','height_provider_replaceable':True,'target_years':list(TARGET_YEARS),'numerical_validity':valid}
 (a.output_dir/'ecouves_a5_main_trajectory_metadata.json').write_text(json.dumps(metadata,indent=2)+'\n',encoding='utf-8')
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
