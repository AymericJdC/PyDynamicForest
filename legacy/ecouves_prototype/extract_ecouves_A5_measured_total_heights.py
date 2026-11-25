#!/usr/bin/env python3
"""Extract measured total-height/DBH pairs for Ecouves A5 by inventory.

Source: GIS Coop workbook sheets Placette, Mesure, Arbre.
Height used: hauteur_ech only. ht_vv is explicitly excluded because it is the
height of the first living whorl / functional crown base, not total height.

The private long CSV contains individual identifiers. Public audit outputs are
aggregate only. Source files are never modified.
"""
from __future__ import annotations
import argparse, csv, hashlib, json, math, re
from pathlib import Path
import numpy as np
import pandas as pd

TARGET_YEARS=(1985,1992,1998,2016,2020)

def norm(x): return re.sub(r'[^a-z0-9]+','_',str(x).strip().lower()).strip('_')
def sha256(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''): h.update(b)
 return h.hexdigest()
def choose(cols, names, contains=()):
 mapping={norm(c):c for c in cols}
 for n in names:
  if n in mapping:return mapping[n]
 matches=[c for c in cols if any(t in norm(c) for t in contains)]
 return matches[0] if len(matches)==1 else None
def positive(v):
 try:
  x=float(v); return x if math.isfinite(x) and x>0 else None
 except Exception:return None
def year_from(v):
 if pd.isna(v):return None
 if isinstance(v,pd.Timestamp):return int(v.year)
 s=str(v).strip()
 # Excel datetimes, ISO strings, or bare years.
 m=re.search(r'(?<!\d)(19\d{2}|20\d{2})(?!\d)',s)
 if m:return int(m.group(1))
 try:
  x=float(v)
  if 1900<=x<=2100:return int(round(x))
 except Exception:pass
 return None

def main():
 p=argparse.ArgumentParser()
 p.add_argument('--workbook',type=Path,required=True)
 p.add_argument('--output-dir',type=Path,required=True)
 p.add_argument('--plot-code',type=int,default=10784)
 a=p.parse_args(); wb=a.workbook.resolve(); out=a.output_dir.resolve()
 if out.exists():raise FileExistsError(f'refusing existing output directory: {out}')
 out.mkdir(parents=True)

 plac=pd.read_excel(wb,'Placette',engine='xlrd')
 mes=pd.read_excel(wb,'Mesure',engine='xlrd')
 arb=pd.read_excel(wb,'Arbre',engine='xlrd')

 # Known core fields plus guarded fallbacks.
 plot_key=choose(plac.columns,('co_placette',),('co_placette',))
 mes_plot=choose(mes.columns,('co_placette',),('co_placette',))
 arb_plot=choose(arb.columns,('co_placette',),('co_placette',))
 tree_col=choose(arb.columns,('no_arb',),('no_arb','numero_arbre'))
 h_col=choose(arb.columns,('hauteur_ech',),())
 circ_col=choose(arb.columns,('circonference130','circonference_130','circumference130','circumference_cm'),('circonference130','circumference130'))
 dbh_col=choose(arb.columns,('dbh_cm','diametre130','diametre_130'),('dbh','diametre130'))

 # Find a measurement/inventory key shared by Mesure and Arbre, excluding plot.
 common=[c for c in mes.columns if c in arb.columns and c not in {mes_plot,arb_plot}]
 preferred=('co_mesure','no_mesure','id_mesure','co_inventaire','no_inventaire')
 measure_key=None
 for name in preferred:
  for c in common:
   if norm(c)==name:measure_key=c;break
  if measure_key:break
 if not measure_key:
  candidates=[]
  for c in common:
   n=norm(c)
   if any(t in n for t in ('mesure','invent','campagne')):
    overlap=len(set(mes[c].dropna()).intersection(set(arb[c].dropna())))
    candidates.append((overlap,c))
  if candidates:
   candidates.sort(reverse=True);measure_key=candidates[0][1]

 # Find temporal field in Mesure by actual extractable year coverage.
 year_candidates=[]
 for c in mes.columns:
  ys=[year_from(v) for v in mes[c]]
  score=sum(y in TARGET_YEARS for y in ys)
  if score:year_candidates.append((score,c,ys))
 year_candidates.sort(reverse=True,key=lambda x:x[0])
 year_col=year_candidates[0][1] if year_candidates else None

 required={'Placette.co_placette':plot_key,'Mesure.co_placette':mes_plot,'Arbre.co_placette':arb_plot,'measurement key':measure_key,'year/date field':year_col,'no_arb':tree_col,'hauteur_ech':h_col}
 missing=[k for k,v in required.items() if v is None]
 if missing:
  raise RuntimeError('could not resolve required fields: '+', '.join(missing)+f'\nCommon Mesure/Arbre columns: {common}')
 if circ_col is None and dbh_col is None:raise RuntimeError('neither circumference nor DBH field found in Arbre')

 # Select the plot strictly by stable code.
 if not (plac[plot_key]==a.plot_code).any():raise RuntimeError(f'plot code {a.plot_code} absent from Placette')
 mes_a5=mes[mes[mes_plot]==a.plot_code].copy()
 mes_a5['_inventory_year']=[year_from(v) for v in mes_a5[year_col]]
 mes_a5=mes_a5[mes_a5['_inventory_year'].isin(TARGET_YEARS)]
 if mes_a5.empty:raise RuntimeError('no A5 measurements found for target years')

 # Ensure one year per measurement key.
 key_year=mes_a5[[measure_key,'_inventory_year']].dropna().drop_duplicates()
 conflicts=key_year.groupby(measure_key)['_inventory_year'].nunique()
 if (conflicts>1).any():raise RuntimeError('a measurement key maps to several years')

 # Join A5 trees to inventory year.
 trees=arb[arb[arb_plot]==a.plot_code].copy()
 merged=trees.merge(key_year,on=measure_key,how='inner',validate='many_to_one')
 records=[]
 for _,r in merged.iterrows():
  h=positive(r[h_col])
  if h is None:continue
  if h>100: h=h/100.0  # hauteur_ech may be stored in cm
  if not (2<=h<=60):continue
  if dbh_col is not None:
   d=positive(r[dbh_col])
   # Guard against DBH stored in mm.
   if d is not None and d>100:d=d/10.0
  else:d=None
  c=positive(r[circ_col]) if circ_col is not None else None
  if d is None and c is not None:d=c/math.pi
  if d is None or not (1<=d<=100):continue
  records.append({'plot':'A5','plot_code':a.plot_code,'inventory_year':int(r['_inventory_year']),'measurement_key':str(r[measure_key]),'no_arb':str(r[tree_col]),'dbh_cm':d,'height_m':h,'height_source':'hauteur_ech'})

 # Duplicate guard and inventory summaries.
 ids=[(r['inventory_year'],r['measurement_key'],r['no_arb']) for r in records]
 if len(ids)!=len(set(ids)):raise RuntimeError('duplicate tree records after join')
 private=out/'PRIVATE_ecouves_A5_measured_total_heights_by_inventory.csv'
 with private.open('w',newline='',encoding='utf-8-sig') as f:
  w=csv.DictWriter(f,fieldnames=list(records[0]));w.writeheader();w.writerows(sorted(records,key=lambda r:(r['inventory_year'],r['measurement_key'],r['no_arb'])))

 summary=[]
 for year in TARGET_YEARS:
  x=[r for r in records if r['inventory_year']==year]
  all_tree_count=int((merged['_inventory_year']==year).sum())
  summary.append({'inventory_year':year,'all_tree_rows_after_join':all_tree_count,'measured_total_heights':len(x),'coverage_fraction':len(x)/all_tree_count if all_tree_count else 0.0,'mean_dbh_cm':float(np.mean([r['dbh_cm'] for r in x])) if x else None,'mean_height_m':float(np.mean([r['height_m'] for r in x])) if x else None,'min_height_m':min([r['height_m'] for r in x]) if x else None,'max_height_m':max([r['height_m'] for r in x]) if x else None})
 summary_path=out/'ecouves_A5_measured_total_heights_summary.csv'
 with summary_path.open('w',newline='',encoding='utf-8-sig') as f:
  w=csv.DictWriter(f,fieldnames=list(summary[0]));w.writeheader();w.writerows(summary)
 manifest={'purpose':'measured total-height/DBH pairs for Ecouves A5 by inventory','source_workbook':str(wb),'source_sha256':sha256(wb),'plot_code':a.plot_code,'height_variable':'hauteur_ech','excluded_variable':'ht_vv (first living whorl / functional crown base; not total height)','resolved_columns':required|{'circumference':circ_col,'dbh':dbh_col},'target_years':TARGET_YEARS,'records':len(records),'summary':summary,'private_output':private.name}
 (out/'ecouves_A5_measured_total_heights_manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
 lines=['# Hauteurs totales mesurées, Écouves A5','','Variable retenue : `hauteur_ech`. `ht_vv` est exclue car elle représente la hauteur du premier verticille vivant / la base du houppier fonctionnel, et non la hauteur totale.','', '| Année | Arbres joints | Hauteurs totales mesurées | Couverture |','|---:|---:|---:|---:|']
 for s in summary:lines.append(f"| {s['inventory_year']} | {s['all_tree_rows_after_join']} | {s['measured_total_heights']} | {100*s['coverage_fraction']:.1f}% |")
 (out/'ecouves_A5_measured_total_heights_report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
 print(f'[OK] private extraction: {private}')
 for s in summary:print(f"[SUMMARY] {s['inventory_year']}: measured={s['measured_total_heights']} joined={s['all_tree_rows_after_join']} coverage={100*s['coverage_fraction']:.1f}%")
 print('[FIELDS] '+json.dumps(required|{'circumference':circ_col,'dbh':dbh_col},ensure_ascii=False))
if __name__=='__main__':main()
