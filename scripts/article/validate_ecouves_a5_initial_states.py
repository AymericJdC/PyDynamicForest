#!/usr/bin/env python3
"""Validate Q-9E.4 states against native PyDynamicForest conventions."""
from __future__ import annotations
import argparse,csv,sys
from pathlib import Path

def root():
    here=Path(__file__).resolve()
    for p in [Path.cwd(),*Path.cwd().parents,*here.parents]:
        if (p/'simulations/article/ecouves_a5').exists():return p
    raise RuntimeError('cannot locate repository root')
ROOT=root();sys.path.insert(0,str(ROOT))
from simulations.article.parameters import build_parameters
from simulations.article.ecouves_a5.pydynamicforest_adapter import load_q9e4_grid_state,convert_q9e4_to_native
from simulations.article.ecouves_a5.state_compatibility import diagnose_native_compatibility

YEAR_TO_GIS_AGE={1965:18,1969:22,1975:28,1980:33,1985:38,1992:45,1998:51,2016:69,2020:73}

def main(argv=None):
    p=argparse.ArgumentParser();p.add_argument('--input-dir',type=Path,default=ROOT/'outputs/article_scenarios/ecouves_a5_grid_reconstruction');p.add_argument('--output-dir',type=Path,default=ROOT/'outputs/article_scenarios/ecouves_a5_solver_compatibility');p.add_argument('--year',action='append',type=int);p.add_argument('--allow-clip',action='store_true');a=p.parse_args(argv)
    params=build_parameters(); years=a.year or sorted(YEAR_TO_GIS_AGE); rows=[]; a.output_dir.mkdir(parents=True,exist_ok=True)
    for year in years:
        path=a.input_dir/f'ecouves_a5_grid_state_{year}.npz'; source=load_q9e4_grid_state(path); conversion=convert_q9e4_to_native(source,params,allow_clip=a.allow_clip); diag=diagnose_native_compatibility(source,conversion,params)
        row={'year':year,'gis_age':YEAR_TO_GIS_AGE.get(year,''),'main_initial_candidate':year==1992,**diag.record()};rows.append(row)
        npz=a.output_dir/f'ecouves_a5_native_initial_state_{year}.npz'
        import numpy as np
        np.savez_compressed(npz,U0=conversion.U0,year=year,gis_age=YEAR_TO_GIS_AGE.get(year,np.nan),axis_order='height_dbh',density_coordinates='normalized',height_provider_replaceable=True)
    csv_path=a.output_dir/'ecouves_a5_solver_state_compatibility.csv'
    with csv_path.open('w',encoding='utf-8',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    lines=['# Q-9E.5 - Validation de compatibilité avec PyDynamicForest','',
      'Les états Q-9E.4 sont redistribués par masses nodales sur la grille native. L’état U est ordonné hauteur × diamètre et exprimé par unité de surface normalisée. Le fournisseur de hauteurs reste remplaçable.','',
      '| Année | Âge GIS | Candidat principal | Statut | Écart N | Écart Hm | Écart Dm | Nœuds tronqués |','|---:|---:|:---:|:---|---:|---:|---:|---:|']
    for r in rows:lines.append(f"| {r['year']} | {r['gis_age']} | {'oui' if r['main_initial_candidate'] else 'non'} | {r['status']} | {r['mass_difference_ha']:.3e} | {r['mean_height_difference_m']:.3e} | {r['mean_dbh_difference_cm']:.3e} | {r['clipped_source_nodes']} |")
    lines += ['','Les écarts de Dg, G et H0 sont diagnostiqués mais non corrigés. Aucune simulation dynamique ni recalibration n’est réalisée.','']
    (a.output_dir/'ecouves_a5_solver_state_validation.md').write_text('\n'.join(lines),encoding='utf-8')
    print(f'Q-9E.5 outputs written to {a.output_dir}')
if __name__=='__main__':main()
