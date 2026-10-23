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
from simulations.article.ecouves_a5.mechanistic_sensitivity import selected_cases,run_case,centred_elasticities

def writecsv(path,rows):
 rows=list(rows)
 with path.open('w',encoding='utf-8',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def main(argv=None):
 base=ROOT/'outputs/article_scenarios/ecouves_a5_solver_compatibility';p=argparse.ArgumentParser();p.add_argument('--initial-state',type=Path,default=base/'ecouves_a5_native_initial_state_1992.npz');p.add_argument('--native-state-dir',type=Path,default=base);p.add_argument('--output-dir',type=Path,default=ROOT/'outputs/article_scenarios/ecouves_a5_mechanistic_sensitivity');p.add_argument('--no-progress',action='store_true');a=p.parse_args(argv)
 progress=None
 if not a.no_progress:
  from tqdm import tqdm;progress=tqdm
 start=perf_counter();rows=[]
 for case in selected_cases():rows.extend(run_case(case,a.initial_state,a.native_state_dir,progress))
 elasticities=centred_elasticities(rows);elapsed=perf_counter()-start;a.output_dir.mkdir(parents=True,exist_ok=True)
 writecsv(a.output_dir/'ecouves_a5_mechanistic_sensitivity_cases.csv',rows);writecsv(a.output_dir/'ecouves_a5_mechanistic_elasticities.csv',elasticities)
 focus=[r for r in elasticities if r['year']==2020 and r['metric'] in {'N','G','Dm','Hm','H0','rho_HD','W1_dbh_cm','W1_height_m'}]
 lines=['# Q-9F.4 - Analyse de sensibilité mécaniste ciblée','',
 'Criblage OAT centré ±20 % autour des paramètres dynamiques inchangés. Les élasticités sont descriptives, locales et ne constituent ni une calibration ni une attribution causale définitive.','',
 '| Mécanisme | Variable 2020 | Valeur basse | Valeur haute | Différence centrée | Élasticité |','|:---|:---|---:|---:|---:|---:|']
 for r in focus:
    elasticity = (
        ""
        if r["elasticity"] is None
        else f"{r['elasticity']:+.4f}"
    )
    lines.append(
        f"| {r['mechanism']} | {r['metric']} | "
        f"{r['low_value']:.8g} | {r['high_value']:.8g} | "
        f"{r['centred_difference']:+.6g} | {elasticity} |"
    )
 lines += ['','Les signatures doivent être lues conjointement aux diagnostics distributionnels Q-9F.3. Aucun scénario n’est sélectionné comme nouveau réglage.','']
 (a.output_dir/'ecouves_a5_mechanistic_sensitivity_report.md').write_text('\n'.join(lines),encoding='utf-8')
 metadata={'purpose':'Q-9F.4 centred OAT mechanistic screening','multipliers':[0.8,1.2],'cases':8,'dynamic_parameters_recalibrated':False,'height_provider_replaceable':True,'elapsed_seconds':elapsed}
 (a.output_dir/'ecouves_a5_mechanistic_sensitivity_metadata.json').write_text(json.dumps(metadata,indent=2)+'\n',encoding='utf-8')
 print(f'Q-9F.4 outputs written to {a.output_dir}');print(f'elapsed_seconds={elapsed:.3f}')
if __name__=='__main__':main()
