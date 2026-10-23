#!/usr/bin/env python3
"""Project Q-9E.3 assigned heights onto a conservative tensor grid."""
from __future__ import annotations
import argparse,csv,sys
from pathlib import Path
import numpy as np

def root():
    here=Path(__file__).resolve()
    for p in [Path.cwd(),*Path.cwd().parents,*here.parents]:
        if (p/"simulations/article/ecouves_a5").exists():return p
    raise RuntimeError("cannot locate repository root")
ROOT=root();sys.path.insert(0,str(ROOT))
from simulations.article.ecouves_a5.height_types import *
from simulations.article.ecouves_a5.grid_projection import *
from simulations.article.ecouves_a5.grid_reconstruction import reconstruct_grid_state

def read_rows(path):
    with path.open(encoding="utf-8",newline="") as f:return list(csv.DictReader(f))
def main(argv=None):
    p=argparse.ArgumentParser();p.add_argument("--assigned-heights",type=Path,default=ROOT/"outputs/article_scenarios/ecouves_a5_height_reconstruction/ecouves_a5_assigned_heights.csv");p.add_argument("--output-dir",type=Path,default=ROOT/"outputs/article_scenarios/ecouves_a5_grid_reconstruction");p.add_argument("--height-min",type=float,default=0.0);p.add_argument("--height-max",type=float,default=50.0);p.add_argument("--height-step",type=float,default=0.5);p.add_argument("--diameter-min",type=float,default=0.0);p.add_argument("--diameter-max",type=float,default=160.0);p.add_argument("--diameter-step",type=float,default=1.0);p.add_argument("--boundary-policy",choices=[x.value for x in BoundaryPolicy],default="strict");a=p.parse_args(argv)
    if not a.assigned_heights.exists():p.error(f"input not found: {a.assigned_heights}")
    rows=read_rows(a.assigned_heights);out=a.output_dir;out.mkdir(parents=True,exist_ok=True)
    hnodes=np.arange(a.height_min,a.height_max+a.height_step/2,a.height_step);dnodes=np.arange(a.diameter_min,a.diameter_max+a.diameter_step/2,a.diameter_step)
    diag=[];index=[]
    for year in sorted({int(r['year']) for r in rows}):
        yr=[r for r in rows if int(r['year'])==year];first=yr[0]
        context=StandContext(first['site'],first['plot'],year,int(first['age']),0.1216,first['series_status'],first['inclusion_rule'])
        trees=[];heights=[]
        for r in yr:
            t=TreeRecord(r['tree_id'],year,int(r['age']),float(r['diameter_cm']),float(r['weight_ha']),float(r['circumference_cm']),r['status'],r['series_status'],r['inclusion_rule'],r['site'],r['plot']);trees.append(t)
            missing=r['is_missing'].lower()=='true';hm=None if missing or r['height_m']=='' else float(r['height_m'])
            heights.append(AssignedHeight(t.tree_id,year,hm,missing,r['missing_reason'] or ("missing" if missing else None),r['provider_id'],ProviderCategory(r['provider_category']),r['source'] or None))
        provider=HeightProviderMetadata("q9e3-import","Q-9E.3 imported assignments","1",ProviderCategory.CALLABLE,True)
        assignment=HeightAssignment(context,provider,tuple(heights));result=reconstruct_grid_state(tuple(trees),assignment,hnodes,dnodes,BoundaryPolicy(a.boundary_policy))
        fn=f"ecouves_a5_grid_state_{year}.npz";np.savez_compressed(out/fn,height_m=hnodes,diameter_cm=dnodes,density_ha_per_m_per_cm=result.state.density_ha_per_m_per_cm,nodal_mass_ha=result.state.nodal_mass_ha)
        diag.append({"year":year,**result.diagnostics.__dict__});index.append({"year":year,"file":fn,"height_nodes":len(hnodes),"diameter_nodes":len(dnodes),"boundary_policy":a.boundary_policy})
    def write(name,rows,fields):
        with (out/name).open('w',encoding='utf-8',newline='') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
    write('ecouves_a5_grid_projection_diagnostics.csv',diag,list(diag[0]));write('ecouves_a5_grid_state_index.csv',index,list(index[0]))
    lines=["# Q-9E.4 - Projection conservative sur la grille","","Projection bilinéaire compacte. La masse et les premiers moments en hauteur et diamètre sont conservés par la quadrature trapézoïdale.","","| Année | Écart N | Écart H moyen | Écart D moyen | Dg individuel | Dg grille | H0 individuel | H0 grille |","|---:|---:|---:|---:|---:|---:|---:|---:|"]
    def f(x):return 'NA' if x is None else f'{x:.8g}'
    for r in diag:lines.append(f"| {r['year']} | {f(r['mass_difference_ha'])} | {f(r['mean_height_difference_m'])} | {f(r['mean_diameter_difference_cm'])} | {f(r['quadratic_mean_diameter_input_cm'])} | {f(r['quadratic_mean_diameter_grid_cm'])} | {f(r['dominant_height_input_m'])} | {f(r['dominant_height_grid_m'])} |")
    lines += ["","Les seconds moments, Dg, surface terrière et hauteur dominante sont diagnostiqués mais ne sont pas imposés. Aucun paramètre dynamique n'est modifié.",""]
    (out/'ecouves_a5_grid_projection_report.md').write_text('\n'.join(lines),encoding='utf-8')
    print(f"Q-9E.4 outputs written to {out}")
if __name__=='__main__':main()
