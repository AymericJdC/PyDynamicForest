#!/usr/bin/env python3
"""Build a deterministic height-regularized 1985 native initial state.

The script keeps observed DBH values and expansion weights, but replaces the
single deterministically imputed height at each DBH by a centred empirical
residual distribution estimated from measured height--DBH pairs.

Expected clean input columns
----------------------------
Tree cloud: dbh_cm, weight_ha
Measured sample: dbh_cm, height_m

No random draw is used. Each tree mass is distributed over every centred
empirical residual and projected bilinearly to the existing native grid.
"""
from __future__ import annotations
import argparse, csv, hashlib, json, math
from pathlib import Path
import numpy as np


def sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''): h.update(b)
    return h.hexdigest()

def load_csv(path: Path, required: tuple[str,...]):
    with path.open(newline='',encoding='utf-8-sig') as f: rows=list(csv.DictReader(f))
    missing=set(required)-set(rows[0] if rows else {})
    if missing: raise KeyError(f'{path}: missing columns {sorted(missing)}')
    out={k:np.array([float(r[k]) for r in rows],float) for k in required}
    if not all(np.all(np.isfinite(v)) for v in out.values()): raise ValueError(f'{path}: non-finite values')
    return out

def projection_weights(nodes: np.ndarray, value: float):
    """Linear conservative weights on a monotone nodal axis."""
    if value <= nodes[0]: return [(0,1.0)], True
    if value >= nodes[-1]: return [(len(nodes)-1,1.0)], True
    j=int(np.searchsorted(nodes,value))
    lo,hi=j-1,j
    lam=(value-nodes[lo])/(nodes[hi]-nodes[lo])
    return [(lo,1-lam),(hi,lam)], False

def moments(mass,h,d):
    total=float(mass.sum())
    H,D=np.meshgrid(h,d,indexing='ij')
    mh=float((mass*H).sum()/total); md=float((mass*D).sum()/total)
    vh=float((mass*(H-mh)**2).sum()/total); vd=float((mass*(D-md)**2).sum()/total)
    cov=float((mass*(H-mh)*(D-md)).sum()/total)
    return {'N':total,'Hm':mh,'Dm':md,'sigma_H':math.sqrt(max(vh,0)),'sigma_D':math.sqrt(max(vd,0)),'rho_HD':cov/math.sqrt(vh*vd) if vh>0 and vd>0 else float('nan')}

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--tree-cloud',type=Path,required=True,help='CSV with dbh_cm and weight_ha')
    p.add_argument('--measured-heights',type=Path,required=True,help='CSV with dbh_cm and height_m')
    p.add_argument('--template-state',type=Path,required=True,help='validated native NPZ used as schema/grid template')
    p.add_argument('--output-dir',type=Path,required=True)
    p.add_argument('--residual-scale',type=float,default=1.0,help='sensitivity multiplier; default 1')
    a=p.parse_args()
    if a.residual_scale < 0: raise ValueError('residual scale must be non-negative')
    out=a.output_dir.resolve()
    if out.exists(): raise FileExistsError(f'refusing existing directory: {out}')
    out.mkdir(parents=True)

    trees=load_csv(a.tree_cloud.resolve(),('dbh_cm','weight_ha'))
    measured=load_csv(a.measured_heights.resolve(),('dbh_cm','height_m'))
    if np.any(trees['weight_ha']<=0) or np.any(trees['dbh_cm']<=0): raise ValueError('tree DBH and weights must be positive')
    if np.any(measured['dbh_cm']<=0): raise ValueError('measured DBH must be positive')

    X=np.column_stack([np.ones(len(measured['dbh_cm'])),np.log(measured['dbh_cm'])])
    beta=np.linalg.lstsq(X,measured['height_m'],rcond=None)[0]
    fitted=X@beta
    residuals=measured['height_m']-fitted
    residuals=residuals-residuals.mean()  # exact centre before scaling
    residuals=a.residual_scale*residuals

    with np.load(a.template_state.resolve(),allow_pickle=False) as z:
        payload={k:np.array(z[k],copy=True) for k in z.files}
    h=np.asarray(payload['height_m'],float)
    d=np.asarray(payload['diameter_cm'],float)
    q=np.asarray(payload['quadrature_weights'],float)
    if q.shape!=(len(h),len(d)): raise ValueError('quadrature weight shape mismatch')

    mass=np.zeros_like(q,float); clipped_h=0.0; clipped_d=0.0
    empirical_factor=1.0/len(residuals)
    for dbh,w in zip(trees['dbh_cm'],trees['weight_ha']):
        mu=float(beta[0]+beta[1]*math.log(dbh))
        dw,dclip=projection_weights(d,float(dbh))
        for eps in residuals:
            hw,hclip=projection_weights(h,mu+float(eps))
            m=float(w)*empirical_factor
            for ih,wh in hw:
                for jd,wd in dw:
                    mass[ih,jd]+=m*wh*wd
            if hclip: clipped_h+=m
        if dclip: clipped_d+=float(w)

    U0=np.divide(mass,q,out=np.zeros_like(mass),where=q>0)
    old_mass=np.asarray(payload.get('native_nodal_mass_ha',payload['U0']*q),float)
    before=moments(old_mass,h,d); after=moments(mass,h,d)

    payload['U0']=U0
    payload['native_nodal_mass_ha']=mass
    payload['height_regularization_residuals_m']=residuals
    state=out/'ecouves_A5_1985_height_regularized_initial_state.npz'
    np.savez_compressed(state,**payload)

    manifest={
      'method':'deterministic empirical-residual conditional height regularization',
      'allometry':{'intercept_m':float(beta[0]),'log_dbh_slope_m':float(beta[1]),'measured_pairs':int(len(residuals)),'residual_scale':a.residual_scale,'residual_sd_m':float(np.std(residuals,ddof=1))},
      'inputs':{'tree_cloud':str(a.tree_cloud.resolve()),'tree_cloud_sha256':sha256(a.tree_cloud.resolve()),'measured_heights':str(a.measured_heights.resolve()),'measured_heights_sha256':sha256(a.measured_heights.resolve()),'template_state':str(a.template_state.resolve()),'template_state_sha256':sha256(a.template_state.resolve())},
      'checks':{'mass_absolute_difference':after['N']-before['N'],'mean_dbh_difference_cm':after['Dm']-before['Dm'],'mean_height_difference_m':after['Hm']-before['Hm'],'height_boundary_mass_fraction':clipped_h/after['N'],'dbh_boundary_mass_fraction':clipped_d/after['N']},
      'template_moments':before,'regularized_moments':after,'output_state':str(state)
    }
    (out/'height_regularization_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    lines=['# Ecouves A5 1985 height regularization','',f"- Measured height--DBH pairs: **{len(residuals)}**.",f"- Fitted allometry: `H = {beta[0]:.6g} + {beta[1]:.6g} log(DBH_cm)`.",f"- Centred residual SD: **{np.std(residuals,ddof=1):.4f} m**.",f"- Mass difference: **{after['N']-before['N']:.3e} trees ha-1**.",f"- Mean DBH difference: **{after['Dm']-before['Dm']:.3e} cm**.",f"- Mean height difference: **{after['Hm']-before['Hm']:.4f} m**.",f"- Height boundary mass fraction: **{clipped_h/after['N']:.3e}**.",'',f"- Conditional vertical dispersion introduced: sigma_H `{before['sigma_H']:.4f}` -> `{after['sigma_H']:.4f}` m.",f"- Height--DBH correlation: `{before['rho_HD']:.4f}` -> `{after['rho_HD']:.4f}`."]
    (out/'height_regularization_report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(f'[OK] {state}')
    print(f"[VERDICT] mass_diff={after['N']-before['N']:.3e} dbh_mean_diff={after['Dm']-before['Dm']:.3e} height_mean_diff={after['Hm']-before['Hm']:.4f} residual_sd={np.std(residuals,ddof=1):.4f}")
if __name__=='__main__': main()
