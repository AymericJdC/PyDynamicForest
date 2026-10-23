#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,sys
from pathlib import Path
def root():
 here=Path(__file__).resolve()
 for p in [Path.cwd(),*Path.cwd().parents,*here.parents]:
  if (p/'simulations/article/ecouves_a5').exists():return p
 raise RuntimeError('cannot locate repository root')
ROOT=root();sys.path.insert(0,str(ROOT))
from simulations.article.ecouves_a5.distributional_diagnostics import run_distributional_diagnostics,YEARS

def writecsv(path,rows):
 rows=list(rows)
 with path.open('w',encoding='utf-8',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def main(argv=None):
 p=argparse.ArgumentParser();p.add_argument('--simulated-dir',type=Path,default=ROOT/'outputs/article_scenarios/ecouves_a5_main_trajectory_1992_2020');p.add_argument('--target-dir',type=Path,default=ROOT/'outputs/article_scenarios/ecouves_a5_solver_compatibility');p.add_argument('--output-dir',type=Path,default=ROOT/'outputs/article_scenarios/ecouves_a5_distributional_diagnostics');a=p.parse_args(argv)
 comps,joints,quantiles,marginals,cells=run_distributional_diagnostics(a.simulated_dir,a.target_dir);a.output_dir.mkdir(parents=True,exist_ok=True)
 writecsv(a.output_dir/'ecouves_a5_distribution_metrics.csv',comps);writecsv(a.output_dir/'ecouves_a5_joint_structure_metrics.csv',joints);writecsv(a.output_dir/'ecouves_a5_distribution_quantiles.csv',quantiles);writecsv(a.output_dir/'ecouves_a5_marginal_distributions.csv',marginals);writecsv(a.output_dir/'ecouves_a5_joint_mass_differences.csv',cells)
 by={(r['year'],r['dimension']):r for r in comps};joint={r['year']:r for r in joints}
 lines=['# Q-9F.3 - Diagnostic distributionnel sans calibration','',
 'Les cibles en hauteur restent des reconstructions provisoires. Les écarts en diamètre sont directement ancrés dans les inventaires individuels. Les excès et déficits de masse par cellule sont descriptifs et ne sont pas assimilés à une mortalité observée.','',
 '| Année | W1 diamètre (cm) | KS diamètre | W1 hauteur (m) | KS hauteur | Δ corrélation H-D | Δ élancement moyen |','|---:|---:|---:|---:|---:|---:|---:|']
 for y in YEARS:
  d=by[(y,'dbh_cm')];h=by[(y,'height_m')];j=joint[y];lines.append(f"| {y} | {d['wasserstein_1']:.4f} | {d['cdf_max_distance']:.4f} | {h['wasserstein_1']:.4f} | {h['cdf_max_distance']:.4f} | {j['correlation_simulated']-j['correlation_target']:+.4f} | {j['mean_slenderness_simulated']-j['mean_slenderness_target']:+.4f} |")
 lines += ['','Aucun paramètre n’est ajusté. Ce lot localise les écarts avant toute analyse de sensibilité ou calibration.','']
 (a.output_dir/'ecouves_a5_distributional_diagnostics_report.md').write_text('\n'.join(lines),encoding='utf-8')
 print(f'Q-9F.3 outputs written to {a.output_dir}')
if __name__=='__main__':main()
