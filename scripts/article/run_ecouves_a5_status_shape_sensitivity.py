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
from simulations.article.ecouves_a5.status_shape_sensitivity import selected_cases,run_case

def writecsv(path,rows):
 rows=list(rows)
 with path.open('w',encoding='utf-8',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def main(argv=None):
 base=ROOT/'outputs/article_scenarios/ecouves_a5_solver_compatibility';p=argparse.ArgumentParser();p.add_argument('--initial-state',type=Path,default=base/'ecouves_a5_native_initial_state_1992.npz');p.add_argument('--native-state-dir',type=Path,default=base);p.add_argument('--output-dir',type=Path,default=ROOT/'outputs/article_scenarios/ecouves_a5_status_shape_sensitivity');p.add_argument('--no-progress',action='store_true');a=p.parse_args(argv)
 progress=None
 if not a.no_progress:
  from tqdm import tqdm;progress=tqdm
 start=perf_counter();rows=[];hierarchy=[]
 for case in selected_cases():
  r,h=run_case(case,a.initial_state,a.native_state_dir,progress);rows.extend(r);hierarchy.extend(h)
 elapsed=perf_counter()-start;a.output_dir.mkdir(parents=True,exist_ok=True);writecsv(a.output_dir/'ecouves_a5_status_shape_cases.csv',rows);writecsv(a.output_dir/'ecouves_a5_status_shape_hierarchy.csv',hierarchy)
 indexed={(r['gamma'],r['year'],r['metric']):r for r in rows};metrics=('N','G','Dm','Dg','Hm','H0','rho_HD','W1_dbh_cm','W1_height_m','KS_height')
 lines=['# Q-9F.7 - Sensibilité à la forme de l’allocation par le statut','',
 'La transformation `S^gamma` est appliquée uniquement au transport en hauteur. Le transport diamétrique et le terme de mortalité conservent le statut de référence. Gamma = 1 reproduit exactement le solveur de référence.','',
 '| Gamma | Année | Variable | Simulation | Cible | Résidu relatif |','|---:|---:|:---|---:|---:|---:|']
 for gamma in (0.75,1.0,1.25):
  for year in (1998,2016,2020):
   for metric in metrics:
    r=indexed[(gamma,year,metric)];rr=r['relative_residual'];lines.append(f"| {gamma:.2f} | {year} | {metric} | {r['value']:.8g} | {r['target']:.8g} | {'' if rr is None else f'{100*rr:+.3f}%'} |")
 lines += ['','Aucun gamma n’est sélectionné comme nouveau paramètre. Le scénario gamma = 1 est un contrôle de non-régression; gamma < 1 relève préférentiellement les faibles statuts dans le seul flux vertical.','']
 (a.output_dir/'ecouves_a5_status_shape_sensitivity_report.md').write_text('\n'.join(lines),encoding='utf-8');(a.output_dir/'ecouves_a5_status_shape_sensitivity_metadata.json').write_text(json.dumps({'purpose':'Q-9F.7 controlled status-shape sensitivity','gammas':[0.75,1.0,1.25],'height_transport_only':True,'dbh_transport_modified':False,'mortality_status_modified':False,'calibration':False,'elapsed_seconds':elapsed},indent=2)+'\n',encoding='utf-8');print(f'Q-9F.7 outputs written to {a.output_dir}');print(f'elapsed_seconds={elapsed:.3f}')
if __name__=='__main__':main()
