#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,json,sys
from pathlib import Path
def root():
 here=Path(__file__).resolve()
 for p in [Path.cwd(),*Path.cwd().parents,*here.parents]:
  if (p/'simulations/article/ecouves_a5').exists():return p
 raise RuntimeError('cannot locate repository root')
ROOT=root();sys.path.insert(0,str(ROOT))
from simulations.article.ecouves_a5.height_growth_allocation_audit import run_allocation_audit,YEARS

def writecsv(path,rows):
 rows=list(rows)
 with path.open('w',encoding='utf-8',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def main(argv=None):
 p=argparse.ArgumentParser();p.add_argument('--simulated-dir',type=Path,default=ROOT/'outputs/article_scenarios/ecouves_a5_main_trajectory_1992_2020');p.add_argument('--target-dir',type=Path,default=ROOT/'outputs/article_scenarios/ecouves_a5_solver_compatibility');p.add_argument('--output-dir',type=Path,default=ROOT/'outputs/article_scenarios/ecouves_a5_height_growth_allocation_audit');a=p.parse_args(argv)
 rows,summaries=run_allocation_audit(a.simulated_dir,a.target_dir);a.output_dir.mkdir(parents=True,exist_ok=True);writecsv(a.output_dir/'ecouves_a5_height_growth_allocation_by_class.csv',rows);writecsv(a.output_dir/'ecouves_a5_height_growth_allocation_summary.csv',summaries)
 indexed={(r['year'],r['hierarchy_class']):r for r in rows}
 lines=['# Q-9F.6 - Audit de l’allocation hiérarchique de la croissance en hauteur','',
 'Dans le schéma legacy, le flux vertical transporte `S[U] × U` avec le champ de croissance en hauteur comme vitesse. Le statut `S[U]` est la fonction de répartition cumulée jointe hauteur-diamètre normalisée, et non un simple rang diamétrique.','',
 '| Année | Classe D/Dg | Statut moyen | Croissance moyenne | Vitesse effective | Covariance croissance-statut | Part de densité |','|---:|:---|---:|---:|---:|---:|---:|']
 for year in YEARS:
  for label in ('very_suppressed','suppressed','subordinate','co_dominant','dominant','very_dominant'):
   r=indexed[(year,label)]
   lines.append(
    f"| {year} | {label} | {r['mean_status']:.6f} | "
    f"{r['mean_height_growth_field']:.6g} | "
    f"{r['mean_effective_height_velocity']:.6g} | "
    f"{r['growth_status_covariance']:+.6g} | "
    f"{r['density_share']:.5f} |"
   )
 lines += ['','Cet audit sépare le champ de croissance, le statut et leur covariance, sans modifier ni simuler une formulation alternative. Le terme de transport intégré est un diagnostic numérique, pas une croissance moyenne individuelle.','']
 (a.output_dir/'ecouves_a5_height_growth_allocation_report.md').write_text('\n'.join(lines),encoding='utf-8');(a.output_dir/'ecouves_a5_height_growth_allocation_metadata.json').write_text(json.dumps({'purpose':'Q-9F.6 audit only','dynamic_parameters_modified':False,'alternative_status_function_simulated':False,'status_definition':'normalized joint lower-tail cumulative distribution in height and DBH'},indent=2)+'\n',encoding='utf-8');print(f'Q-9F.6 outputs written to {a.output_dir}')
if __name__=='__main__':main()
