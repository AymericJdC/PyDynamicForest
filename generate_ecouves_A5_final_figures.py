#!/usr/bin/env python3
"""Generate the three final Ecouves A5 manuscript figures.

Run from the PyDynamicForest repository root. The script reads only frozen
outputs and reconstructed target states. It does not run the dynamic model.
"""
from __future__ import annotations
import argparse, csv, json, sys
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np

YEARS=(1985,1992,1998,2016,2020)
AGES={1985:37,1992:44,1998:50,2016:68,2020:72}

def load_npz_u(path):
    with np.load(path,allow_pickle=False) as z:
        key='U0' if 'U0' in z.files else 'U'
        return np.array(z[key],float,copy=True)

def read_comparison(path):
    with path.open(newline='',encoding='utf-8-sig') as f: rows=list(csv.DictReader(f))
    return {(int(float(r['year'])),r['metric']):r for r in rows}

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--frozen-dir',type=Path,required=True)
    p.add_argument('--initial-state',type=Path,required=True)
    p.add_argument('--target-state-dir',type=Path,required=True)
    p.add_argument('--output-dir',type=Path,required=True)
    a=p.parse_args()
    root=Path.cwd().resolve();sys.path.insert(0,str(root))
    from simulations.article.parameters import build_parameters
    from pydynamicforest.numerics import product_trapezoidal_weights
    from pydynamicforest.observation_operators import physical_height_nodes,physical_dbh_nodes
    params=build_parameters()
    h=physical_height_nodes(params);d=physical_dbh_nodes(params,unit='cm');w=product_trapezoidal_weights(params)
    out=a.output_dir.resolve()
    if out.exists(): raise FileExistsError(f'refusing existing output directory: {out}')
    out.mkdir(parents=True)
    frozen=a.frozen_dir.resolve();target=a.target_state_dir.resolve()

    targets={1985:load_npz_u(a.initial_state.resolve())}
    simulated={}
    for year in YEARS:
        simulated[year]=load_npz_u(frozen/f'ecouves_a5_frozen_state_{year}.npz')
        if year!=1985: targets[year]=load_npz_u(target/f'ecouves_a5_native_initial_state_{year}.npz')

    # Figure 1: quadrature weighted stem masses, common log scale.
    masses=[U*w for U in list(targets.values())+list(simulated.values())]
    positive=np.concatenate([m[m>0] for m in masses])
    vmin=max(float(np.percentile(positive,2)),1e-10);vmax=float(np.max(positive))
    fig,axes=plt.subplots(2,len(YEARS),figsize=(14,6),sharex=True,sharey=True,constrained_layout=True)
    im=None
    for j,year in enumerate(YEARS):
        for i,(label,U) in enumerate((('Reconstructed target',targets[year]),('Simulation',simulated[year]))):
            mass=U*w
            shown=np.ma.masked_where(mass<=0,mass)
            im=axes[i,j].pcolormesh(d,h,shown,shading='auto',norm=__import__('matplotlib').colors.LogNorm(vmin=vmin,vmax=vmax))
            axes[i,j].set_title(f'{year} (age {AGES[year]})')
            if j==0: axes[i,j].set_ylabel(f'{label}\nHeight (m)')
            if i==1: axes[i,j].set_xlabel('DBH (cm)')
    fig.colorbar(im,ax=axes.ravel().tolist(),label='Quadrature-weighted stem number (trees ha$^{-1}$)')
    fig.savefig(out/'figure_1_joint_states.pdf',bbox_inches='tight')
    fig.savefig(out/'figure_1_joint_states.png',dpi=300,bbox_inches='tight');plt.close(fig)

    comp=read_comparison(frozen/'ecouves_a5_frozen_1985_2020_comparison.csv')
    plot_years=[1992,1998,2016,2020]
    def series(metric,field): return [float(comp[y,metric][field]) for y in plot_years]
    target_field='reconstructed_target_value';sim_field='simulated_value'

    # Figure 2: conventional stand variables.
    panels=[('N','Stand density (trees ha$^{-1}$)'),('G','Basal area (m$^2$ ha$^{-1}$)'),('Dm','Mean DBH (cm)'),('Dg','Quadratic mean DBH (cm)'),('Hm','Mean height (m)'),('H0','Dominant height (m)')]
    fig,axes=plt.subplots(2,3,figsize=(11,7),sharex=True,constrained_layout=True)
    for ax,(metric,ylabel) in zip(axes.ravel(),panels):
        ax.plot(plot_years,series(metric,sim_field),'-',label='Simulation')
        ax.plot(plot_years,series(metric,target_field),'o',fillstyle='none',label='Reconstructed target')
        ax.set_ylabel(ylabel);ax.set_xticks(plot_years);ax.grid(True,alpha=.25)
    for ax in axes[1]: ax.set_xlabel('Inventory year')
    handles,labels=axes[0,0].get_legend_handles_labels();fig.legend(handles,labels,loc='outside upper center',ncol=2)
    fig.savefig(out/'figure_2_stand_trajectories.pdf',bbox_inches='tight')
    fig.savefig(out/'figure_2_stand_trajectories.png',dpi=300,bbox_inches='tight');plt.close(fig)

    # Figure 3: distributed-structure diagnostics.
    panels=[('sigma_D','DBH standard deviation (cm)'),('Hm','Mean height (m)'),('H0_minus_Hm','$H_0-H_m$ (m)'),('rho_HD','Height–DBH correlation')]
    fig,axes=plt.subplots(2,2,figsize=(9,7),sharex=True,constrained_layout=True)
    for ax,(metric,ylabel) in zip(axes.ravel(),panels):
        ax.plot(plot_years,series(metric,sim_field),'-',label='Simulation')
        ax.plot(plot_years,series(metric,target_field),'o',fillstyle='none',label='Reconstructed target')
        ax.set_ylabel(ylabel);ax.set_xticks(plot_years);ax.grid(True,alpha=.25)
    for ax in axes[1]: ax.set_xlabel('Inventory year')
    handles,labels=axes[0,0].get_legend_handles_labels();fig.legend(handles,labels,loc='outside upper center',ncol=2)
    fig.savefig(out/'figure_3_structural_diagnostics.pdf',bbox_inches='tight')
    fig.savefig(out/'figure_3_structural_diagnostics.png',dpi=300,bbox_inches='tight');plt.close(fig)

    captions='''# Final figure captions\n\n## Figure 1\nReconstructed empirical targets and simulated joint height--DBH states for Écouves A5 in 1985, 1992, 1998, 2016 and 2020. Colours represent quadrature-weighted stem number on a common logarithmic scale. The 1985 agreement is imposed by construction. Individual heights in the reconstructed targets are deterministic estimates from DBH.\n\n## Figure 2\nReconstructed empirical targets and simulated stand trajectories for density, basal area, mean DBH, quadratic mean DBH, mean height and dominant height. Dynamic parameters K and c_phi were calibrated sequentially on stand density and mean DBH, respectively; the height variables were not included in calibration.\n\n## Figure 3\nStructural diagnostics for the calibrated Écouves A5 trajectory. DBH standard deviation, mean height, dominant-minus-mean height contrast and height--DBH correlation are compared with reconstructed empirical targets. Height-based targets depend on deterministic height reconstruction and are therefore internal diagnostics rather than independent measurements.\n'''
    (out/'figure_captions.md').write_text(captions,encoding='utf-8')
    manifest={'frozen_dir':str(frozen),'initial_state':str(a.initial_state.resolve()),'target_state_dir':str(target),'years':list(YEARS),'K_per_year':0.0377,'cphi_m_per_year':0.0165,'outputs':sorted(p.name for p in out.iterdir())}
    (out/'figure_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('[OK] three final figures generated')
    for path in sorted(out.iterdir()): print(path.name)
if __name__=='__main__': main()
