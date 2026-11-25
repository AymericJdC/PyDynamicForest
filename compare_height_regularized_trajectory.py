#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,json,math
from pathlib import Path
METRICS=('N','G','Dm','Dg','sigma_D','Hm','H0','H0_minus_Hm','rho_HD')
def read(path):
 with path.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def index(rows):return {(int(float(r['year'])),r['metric']):r for r in rows}
def find_csv(d):
 xs=list(d.glob('*comparison.csv'))
 if len(xs)!=1: raise RuntimeError(f'{d}: expected one comparison CSV, found {len(xs)}')
 return xs[0]
def main():
 p=argparse.ArgumentParser();p.add_argument('--baseline-dir',type=Path,required=True);p.add_argument('--regularized-dir',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True);a=p.parse_args()
 out=a.output_dir.resolve()
 if out.exists(): raise FileExistsError(out)
 out.mkdir(parents=True)
 b=index(read(find_csv(a.baseline_dir.resolve()))); r=index(read(find_csv(a.regularized_dir.resolve())))
 rows=[]
 for key in sorted(set(b)&set(r)):
  y,m=key
  if m not in METRICS: continue
  bv=float(b[key]['simulated_value']);rv=float(r[key]['simulated_value']);target=float(r[key]['reconstructed_target_value'])
  rows.append({'year':y,'metric':m,'baseline_simulation':bv,'regularized_simulation':rv,'regularized_minus_baseline':rv-bv,'relative_change_vs_baseline':(rv-bv)/bv if bv else float('nan'),'target':target,'baseline_residual':bv-target,'regularized_residual':rv-target})
 path=out/'height_regularized_trajectory_comparison.csv'
 with path.open('w',newline='',encoding='utf-8-sig') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 summary={}
 for m in METRICS:
  x=[q for q in rows if q['metric']==m]
  if not x: continue
  summary[m]={'max_abs_relative_change_vs_baseline':max(abs(q['relative_change_vs_baseline']) for q in x),'regularized_relative_rmse_vs_target':math.sqrt(sum(((q['regularized_simulation']-q['target'])/q['target'])**2 for q in x)/len(x))}
 (out/'height_regularized_trajectory_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
 report=['# Height-regularized trajectory sensitivity','', '| Metric | Maximum absolute trajectory change | Relative RMSE after regularization |','|---|---:|---:|']
 for m,v in summary.items():report.append(f"| `{m}` | {100*v['max_abs_relative_change_vs_baseline']:.3f}% | {100*v['regularized_relative_rmse_vs_target']:.3f}% |")
 (out/'height_regularized_trajectory_report.md').write_text('\n'.join(report)+'\n')
 print(f'[OK] {path}')
 print('[VERDICT] maximum changes: '+', '.join(f"{m}={100*v['max_abs_relative_change_vs_baseline']:.3f}%" for m,v in summary.items()))
if __name__=='__main__':main()
