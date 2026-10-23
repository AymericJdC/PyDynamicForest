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
from simulations.article.ecouves_a5.status_shape_mass_balance import GAMMAS,run_mass_balance

def main(argv=None):
 p=argparse.ArgumentParser();p.add_argument('--initial-state',type=Path,default=ROOT/'outputs/article_scenarios/ecouves_a5_solver_compatibility/ecouves_a5_native_initial_state_1992.npz');p.add_argument('--output-dir',type=Path,default=ROOT/'outputs/article_scenarios/ecouves_a5_status_shape_mass_balance');p.add_argument('--short',action='store_true',help='stop at age 46 for quick diagnosis');a=p.parse_args(argv);a.output_dir.mkdir(parents=True,exist_ok=True)
 all_rows=[];summaries=[]
 for gamma in GAMMAS:
  rows,first,summary=run_mass_balance(a.initial_state,gamma,final_age=46.0 if a.short else 73.0);all_rows.extend(rows);summaries.append(summary)
 with (a.output_dir/'ecouves_a5_status_shape_mass_balance.csv').open('w',encoding='utf-8',newline='') as f:w=csv.DictWriter(f,fieldnames=list(all_rows[0]));w.writeheader();w.writerows(all_rows)
 (a.output_dir/'ecouves_a5_status_shape_mass_balance_summary.json').write_text(json.dumps(summaries,indent=2)+'\n',encoding='utf-8')
 lines=['# Q-9F.7 - Diagnostic du bilan de masse','',
 'Les intégrales instantanées sont descriptives. Le pas implicite couple transport, diffusion et mortalité; elles ne sont pas présentées comme une décomposition additive exacte de la variation réalisée.','',
 '| Gamma | Densité initiale | Densité finale | Première alerte | Âge de l’alerte | Variation cumulée à l’alerte |','|---:|---:|---:|:---|---:|---:|']
 for s in summaries:
  alert = s["first_alert"]
  alert_label = "non" if alert is None else "oui"
  alert_age = "" if alert is None else f"{alert['age']:.8g}"
  alert_change = (
   ""
   if alert is None
   else f"{alert['cumulative_density_change']:+.8g}"
  )
  lines.append(
   f"| {s['gamma']:.2f} | "
   f"{s['initial_density']:.8g} | "
   f"{s['final_density']:.8g} | "
   f"{alert_label} | {alert_age} | {alert_change} |"
  )
 lines += ['','Le tableau CSV compare aussi, à chaque point enregistré, le pas alternatif au pas de référence construit depuis exactement le même état avant le pas.','']
 (a.output_dir/'ecouves_a5_status_shape_mass_balance_report.md').write_text('\n'.join(lines),encoding='utf-8');print(f'Q-9F.7 diagnostic outputs written to {a.output_dir}')
if __name__=='__main__':main()
