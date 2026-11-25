#!/usr/bin/env python3
"""Build five regularized Écouves A5 empirical target states.

Run from the PyDynamicForest repository root. The script:
1. reads the complete Q-9E.1 A5 populations;
2. fits ad hoc log-DBH allometries from measured total heights on A1+A2+A5;
3. keeps measured A5 heights when available;
4. distributes each missing-height tree weight over centered empirical residuals;
5. writes a Q-9E.3-compatible assigned-height table;
6. calls the existing Q-9E.4 projection and Q-9E.5 native conversion scripts.

1998 has no measured total heights and uses the 2001 allometry/residual sample.
HbH/ht_vv is never used as total height.
"""
from __future__ import annotations
import argparse, csv, hashlib, json, math, subprocess, sys
from pathlib import Path
import numpy as np
import pandas as pd

TARGET_YEARS=(1985,1992,1998,2016,2020)
ALLOMETRY_SOURCE_YEAR={1985:1985,1992:1992,1998:2001,2016:2016,2020:2020}
PLOT_CODES={'A1':10780,'A2':10781,'A5':10784}
FR_SUFFIX={2001:'01',2016:'16',2020:'20'}
ASSIGNMENT_COLUMNS=(
 'site','plot','year','age','tree_id','diameter_cm','circumference_cm','weight_ha',
 'status','series_status','inclusion_rule','height_m','is_missing','missing_reason',
 'provider_id','provider_category','source','uncertainty_kind',
 'uncertainty_standard_deviation_m','uncertainty_lower_m','uncertainty_upper_m',
 'uncertainty_confidence_level','provider_version','variant','domain_status',
 'domain_reasons','quadratic_mean_diameter_cm','basal_area_m2_ha',
 'local_effect_lambda','height_component_kind','residual_component_m','component_index',
 'component_count','measured_height_available'
)

def sha256(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def pos(v):
 try:
  x=float(v);return x if math.isfinite(x) and x>0 else None
 except Exception:return None
def key(v):
 try:return str(int(float(v)))
 except Exception:return str(v).strip()
def fit(sample):
 d=sample.dbh_cm.to_numpy(float);h=sample.height_m.to_numpy(float)
 X=np.column_stack([np.ones(len(d)),np.log(d)])
 b=np.linalg.lstsq(X,h,rcond=None)[0];pred=X@b;res=h-pred;res=res-res.mean()
 return {'beta0':float(b[0]),'beta1':float(b[1]),'residuals':res,
         'n':len(d),'rmse':float(np.sqrt(np.mean(res**2))),
         'sd':float(np.std(res,ddof=1))}
def extract_gis_measured(gis):
 mes=pd.read_excel(gis,'Mesure',engine='xlrd')
 arb=pd.read_excel(gis,'Arbre',engine='xlrd')
 z=arb.merge(mes[['co_placette','no_mesure','an_mesure']],on=['co_placette','no_mesure'],how='left',validate='many_to_one')
 rows=[]
 for plot,code in PLOT_CODES.items():
  for year in (1985,1992):
   q=z[(z.co_placette==code)&(z.an_mesure==year)]
   for _,r in q.iterrows():
    c=pos(r.circonference130);h=pos(r.hauteur_ech)
    if c is None or h is None:continue
    if h>100:h/=100
    rows.append({'plot':plot,'tree_id':key(r.no_arb),'year':year,'dbh_cm':c/math.pi,'height_m':h,'origin':'GIS_hauteur_ech'})
 return pd.DataFrame(rows)
def extract_francois_measured(path):
 rows=[]
 for plot in PLOT_CODES:
  f=pd.read_excel(path,plot,engine='xlrd')
  for year,s in FR_SUFFIX.items():
   for _,r in f.iterrows():
    c=pos(r.get(f'c{s}'));h=pos(r.get(f'Ht{s}'))
    if c is None or h is None:continue
    if h>100:h/=100
    rows.append({'plot':plot,'tree_id':key(r.Num),'year':year,'dbh_cm':c/math.pi,'height_m':h,'origin':f'Francois_Ht{s}'})
 return pd.DataFrame(rows)
def truth(v):return str(v).strip().lower() in {'true','1','yes'}
def run_command(command,log):
 with log.open('w',encoding='utf-8') as stream:
  p=subprocess.run(command,text=True,stdout=stream,stderr=subprocess.STDOUT)
 if p.returncode:raise RuntimeError(f"command failed ({p.returncode}); see {log}: {' '.join(map(str,command))}")
def main():
 p=argparse.ArgumentParser()
 p.add_argument('--inventory-long',type=Path,required=True)
 p.add_argument('--gis',type=Path,required=True)
 p.add_argument('--francois',type=Path,required=True)
 p.add_argument('--output-root',type=Path,required=True)
 p.add_argument('--allow-clip',action='store_true')
 a=p.parse_args();repo=Path.cwd().resolve();out=a.output_root.resolve()
 for x in (a.inventory_long,a.gis,a.francois):
  if not x.is_file():raise FileNotFoundError(x)
 if out.exists():raise FileExistsError(f'refusing existing output root: {out}')
 assigned_dir=out/'01_assigned_heights';grid_dir=out/'02_grid_states';native_dir=out/'03_native_states';logs=out/'logs'
 for d in (assigned_dir,grid_dir,native_dir,logs):d.mkdir(parents=True)
 inv=pd.read_csv(a.inventory_long,encoding='utf-8-sig')
 inv=inv[(inv['plot'].astype(str)=='Ecouves A5')&inv['included_in_reference_state'].map(truth)&pd.to_numeric(inv.diameter_cm,errors='coerce').gt(0)&pd.to_numeric(inv.year,errors='coerce').isin(TARGET_YEARS)].copy()
 inv['tree_key']=inv.tree_id.map(key);inv['year']=pd.to_numeric(inv.year).astype(int)
 if not set(TARGET_YEARS).issubset(set(inv.year)):raise RuntimeError(f'missing target years; found {sorted(inv.year.unique())}')
 measured=pd.concat([extract_gis_measured(a.gis),extract_francois_measured(a.francois)],ignore_index=True)
 if measured.duplicated(['plot','tree_id','year']).any():raise RuntimeError('duplicate measured height keys')
 models={}
 for target,source_year in ALLOMETRY_SOURCE_YEAR.items():
  sample=measured[measured.year==source_year]
  if len(sample)<10:raise RuntimeError(f'insufficient measured pairs for {source_year}: {len(sample)}')
  models[target]=fit(sample)
 # A5 measured lookup by year/tree.
 look={(int(r.year),key(r.tree_id)):r for r in measured.loc[measured["plot"] == "A5"].itertuples()}
 assigned=[];summary=[]
 for year in TARGET_YEARS:
  pop=inv[inv.year==year].copy();model=models[year];res=model['residuals'];predicted=measured_count=0
  for r in pop.itertuples():
   d=float(r.diameter_cm);w=float(r.expansion_factor_ha);m=look.get((year,key(r.tree_id)))
   base={
    'site':'Ecouves','plot':'Ecouves A5','year':year,'age':int(round(float(r.age))),'tree_id':key(r.tree_id),
    'diameter_cm':d,'circumference_cm':float(r.circumference_cm) if pd.notna(r.circumference_cm) else math.pi*d,
    'status':r.status,'series_status':r.series_status,'inclusion_rule':r.inclusion_rule,
    'is_missing':False,'missing_reason':'','provider_id':f'ecouves-log-dbh-{ALLOMETRY_SOURCE_YEAR[year]}-empirical-residuals',
    'provider_category':'callable','source':'GIS_Coop_population_and_measured_height_sources',
    'uncertainty_kind':'empirical_centered_residual_distribution','uncertainty_standard_deviation_m':model['sd'],
    'uncertainty_lower_m':float(np.min(res)),'uncertainty_upper_m':float(np.max(res)),
    'uncertainty_confidence_level':'','provider_version':'multiyear-regularized-v1','variant':'article_target',
    'domain_status':'inside','domain_reasons':'','quadratic_mean_diameter_cm':'','basal_area_m2_ha':'',
    'local_effect_lambda':'','component_count':1 if m is not None else len(res),
    'measured_height_available':m is not None,
   }
   if m is not None:
    measured_count+=1
    assigned.append({**base,'weight_ha':w,'height_m':float(m.height_m),'height_component_kind':'measured_total_height','residual_component_m':0.0,'component_index':0})
   else:
    predicted+=1;mu=model['beta0']+model['beta1']*math.log(d)
    for j,e in enumerate(res):
     assigned.append({**base,'weight_ha':w/len(res),'height_m':mu+float(e),'height_component_kind':'imputed_empirical_residual_component','residual_component_m':float(e),'component_index':j})
  summary.append({'year':year,'population_trees':len(pop),'measured_A5_heights_matched':measured_count,'imputed_trees':predicted,'allometry_source_year':ALLOMETRY_SOURCE_YEAR[year],'allometry_sample_n':model['n'],'beta0':model['beta0'],'beta1':model['beta1'],'residual_sd_m':model['sd'],'assigned_components':sum(1 for x in assigned if x['year']==year),'N_input':float(pop.expansion_factor_ha.sum()),'N_assigned':sum(x['weight_ha'] for x in assigned if x['year']==year)})
 assigned_path=assigned_dir/'ecouves_a5_assigned_heights_regularized.csv'
 with assigned_path.open('w',newline='',encoding='utf-8') as f:
  wr=csv.DictWriter(f,fieldnames=ASSIGNMENT_COLUMNS,extrasaction='ignore');wr.writeheader();wr.writerows(assigned)
 pd.DataFrame(summary).to_csv(out/'regularized_targets_summary.csv',index=False,encoding='utf-8-sig')
 # Existing Q-9E.4 and Q-9E.5 scripts provide the authoritative grid/native schemas.
 run_command([sys.executable,str(repo/'scripts/article/project_ecouves_a5_heights_to_grid.py'),'--assigned-heights',str(assigned_path),'--output-dir',str(grid_dir)],logs/'projection.log')
 # Q-9E.5 accepts one --year value per invocation. Convert the five
 # selected targets separately while retaining all NPZ files in one directory.
 native_logs = []
 for year in TARGET_YEARS:
  validate=[sys.executable,str(repo/'scripts/article/validate_ecouves_a5_initial_states.py'),'--input-dir',str(grid_dir),'--output-dir',str(native_dir),'--year',str(year)]
  if a.allow_clip:validate.append('--allow-clip')
  year_log=logs/f'native_conversion_{year}.log'
  run_command(validate,year_log)
  native_logs.append(str(year_log))
 expected=[native_dir/f'ecouves_a5_native_initial_state_{y}.npz' for y in TARGET_YEARS]
 missing=[str(x) for x in expected if not x.is_file()]
 if missing:raise RuntimeError('missing native states: '+', '.join(missing))
 manifest={'purpose':'five regularized empirical targets for joint height-DBH comparison','target_years':TARGET_YEARS,'allometry_source_year':ALLOMETRY_SOURCE_YEAR,'1998_policy':'2001 ad hoc allometry and empirical residuals','height_policy':'measured A5 heights kept; missing heights integrated over centered empirical residuals','HbH_policy':'excluded from total height','inputs':{str(x.resolve()):sha256(x) for x in (a.inventory_long,a.gis,a.francois)},'outputs':[str(x) for x in expected],'native_conversion_logs':native_logs}
 (out/'regularized_targets_manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
 report=['# Construction des cinq cibles régularisées','', '| Année | Arbres | H mesurées appariées | Arbres imputés | Source allométrique | n allométrie | SD résiduelle | Conservation N |','|---:|---:|---:|---:|---:|---:|---:|---:|']
 for s in summary:report.append(f"| {s['year']} | {s['population_trees']} | {s['measured_A5_heights_matched']} | {s['imputed_trees']} | {s['allometry_source_year']} | {s['allometry_sample_n']} | {s['residual_sd_m']:.4f} m | {s['N_assigned']-s['N_input']:.3e} |")
 report += ['','Les cinq états natifs ont été créés dans `03_native_states`. Les hauteurs `HbH`/`ht_vv` n’ont pas été utilisées.']
 (out/'regularized_targets_report.md').write_text('\n'.join(report)+'\n',encoding='utf-8')
 print('[OK]',out/'regularized_targets_report.md')
if __name__=='__main__':main()
