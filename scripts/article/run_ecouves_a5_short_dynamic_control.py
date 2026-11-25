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
from simulations.article.ecouves_a5.short_dynamic_control import run_short_dynamic_control

def main(argv=None):
 p=argparse.ArgumentParser();p.add_argument('--initial-state',type=Path,default=ROOT/'outputs/article_scenarios/ecouves_a5_solver_compatibility/ecouves_a5_native_initial_state_1992.npz');p.add_argument('--output-dir',type=Path,default=ROOT/'outputs/article_scenarios/ecouves_a5_short_dynamic_control');p.add_argument('--steps',type=int,default=5);a=p.parse_args(argv)
 x0,params,context,final,rows=run_short_dynamic_control(a.initial_state,n_steps=a.steps,provider_id='savine-douglas-fixed-effects');a.output_dir.mkdir(parents=True,exist_ok=True)
 records=[r.record() for r in rows]
 with (a.output_dir/'ecouves_a5_short_control_time_series.csv').open('w',encoding='utf-8',newline='') as f:w=csv.DictWriter(f,fieldnames=list(records[0]));w.writeheader();w.writerows(records)
 initial,ending=records[0],records[-1]
 keys=('stand_density','mean_height_m','mean_dbh_cm','quadratic_mean_dbh_cm','basal_area_m2_ha','dominant_height_m','height_dbh_correlation')
 changes={k:{'initial':initial[k],'final':ending[k],'absolute_change':ending[k]-initial[k]} for k in keys}
 valid=all(r['minimum_density']>=-params.numerics.positivity_tolerance and r['status_minimum']>=-1e-12 and r['status_maximum']<=1+1e-12 for r in records)
 metadata={'purpose':'Q-9F.1 short dynamic control from reconstructed 1992 state','inventory_year':1992,'initial_age':45.0,'steps':a.steps,'dt':params.numerics.time.dt,'final_age':final.age,'solver':'sparse_legacy','dynamic_parameters_recalibrated':False,'height_provider_id':'savine-douglas-fixed-effects','height_provider_replaceable':True,'initial_state_source':str(a.initial_state),'numerical_validity':valid,'changes':changes}
 (a.output_dir/'ecouves_a5_short_control_metadata.json').write_text(json.dumps(metadata,indent=2)+'\n',encoding='utf-8')
 lines=['# Q-9F.1 - Contrôle dynamique court depuis 1992','',f"- Pas exécutés : {a.steps};",f"- pas de temps : {params.numerics.time.dt:.8g} an;",f"- âge final : {final.age:.8g} ans;",f"- validité numérique : {'oui' if valid else 'non'};",'- paramètres dynamiques recalibrés : non;','- fournisseur de hauteurs remplaçable : oui.','','| Variable | Initiale | Finale | Variation |','|:---|---:|---:|---:|']
 for k,v in changes.items():lines.append(f"| {k} | {v['initial']:.10g} | {v['final']:.10g} | {v['absolute_change']:+.6g} |")
 lines += ['','Ce contrôle ne constitue pas une validation biologique et ne remplace pas la trajectoire principale 45-73 ans.','']
 (a.output_dir/'ecouves_a5_short_control_report.md').write_text('\n'.join(lines),encoding='utf-8')
 if not valid:raise RuntimeError('short dynamic control failed positivity or status bounds')
 print(f'Q-9F.1 outputs written to {a.output_dir}')
if __name__=='__main__':main()
