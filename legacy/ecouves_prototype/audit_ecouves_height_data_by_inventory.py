#!/usr/bin/env python3
"""Audit measured and reconstructed height information by Ecouves A5 inventory.

Read-only audit. It does not rebuild targets and does not modify source files.
Outputs only aggregate counts and summaries, never individual-tree records.
"""
from __future__ import annotations
import argparse, csv, json, math, re
from collections import Counter
from pathlib import Path
import numpy as np

YEARS=(1985,1992,1998,2016,2020)
HEIGHT_HINTS=('height','hauteur','htot','h_tot','hauteur_ech','hauteur_totale')
DBH_HINTS=('dbh','diam','diametre','diameter')
CIRC_HINTS=('circ','circonference','circumference')
YEAR_HINTS=('year','annee','inventory_year','an_mesure')
PLOT_HINTS=('plot','placette','parcelle','modalite')
SOURCE_HINTS=('source','height_source','origine')

def norm(x):
    return re.sub(r'[^a-z0-9]+','_',str(x).strip().lower()).strip('_')

def choose(cols,hints):
    n={c:norm(c) for c in cols}
    exact=[]; partial=[]
    for c,v in n.items():
        if v in hints: exact.append(c)
        elif any(h in v for h in hints): partial.append(c)
    return exact[0] if exact else (partial[0] if partial else None)

def num(x):
    try:
        if x is None or str(x).strip()=='': return None
        v=float(str(x).replace(',','.'))
        return v if math.isfinite(v) else None
    except Exception:return None

def read_csv(path):
    with path.open(newline='',encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))

def summarize_csv(path):
    rows=read_csv(path)
    cols=list(rows[0]) if rows else []
    year_col=choose(cols,YEAR_HINTS); plot_col=choose(cols,PLOT_HINTS)
    h_col=choose(cols,HEIGHT_HINTS); d_col=choose(cols,DBH_HINTS); c_col=choose(cols,CIRC_HINTS)
    source_col=choose(cols,SOURCE_HINTS)
    result={'file':str(path),'rows':len(rows),'columns':cols,'detected':{'year':year_col,'plot':plot_col,'height':h_col,'dbh':d_col,'circumference':c_col,'source':source_col},'inventory':{}}
    for year in YEARS:
        selected=[]
        for r in rows:
            if year_col:
                y=num(r.get(year_col))
                if y is None or int(round(y))!=year: continue
            elif str(year) not in path.name: continue
            if plot_col:
                p=str(r.get(plot_col,'')).strip().upper()
                if p and p!='A5' and 'A5' not in p: continue
            selected.append(r)
        if not selected: continue
        heights=[num(r.get(h_col)) for r in selected] if h_col else []
        dbhs=[num(r.get(d_col)) for r in selected] if d_col else []
        circs=[num(r.get(c_col)) for r in selected] if c_col else []
        heights=[x for x in heights if x is not None and x>0]
        dbhs=[x for x in dbhs if x is not None and x>0]
        circs=[x for x in circs if x is not None and x>0]
        sources=Counter(str(r.get(source_col,'')).strip() for r in selected) if source_col else Counter()
        result['inventory'][str(year)]={'selected_rows':len(selected),'valid_heights':len(heights),'valid_dbh':len(dbhs),'valid_circumference':len(circs),'height_sources':dict(sources),'height_min':min(heights) if heights else None,'height_max':max(heights) if heights else None}
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--root',type=Path,required=True)
    p.add_argument('--output-dir',type=Path,required=True)
    a=p.parse_args(); root=a.root.resolve(); out=a.output_dir.resolve()
    if out.exists(): raise FileExistsError(f'refusing existing output directory: {out}')
    out.mkdir(parents=True)
    audit=[]
    for path in sorted(root.rglob('*.csv')):
        try:
            s=summarize_csv(path)
            if any(s['detected'].values()) and s['inventory']: audit.append(s)
        except Exception as e:
            audit.append({'file':str(path),'error':repr(e)})
    (out/'height_inventory_audit.json').write_text(json.dumps(audit,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    # Flatten useful inventory records.
    flat=[]
    for s in audit:
        detected = s.get('detected', {})
        for inventory_year, v in s.get('inventory', {}).items():
            # Keep the inventory year separate from the detected source-column
            # name. In v1, detected['year'] overwrote the numeric year here.
            flat.append({
                'file': s['file'],
                'inventory_year': int(inventory_year),
                'year_column': detected.get('year'),
                'plot_column': detected.get('plot'),
                'height_column': detected.get('height'),
                'dbh_column': detected.get('dbh'),
                'circumference_column': detected.get('circumference'),
                'source_column': detected.get('source'),
                **v,
            })
    fields=['file','inventory_year','year_column','plot_column','height_column','dbh_column','circumference_column','source_column','selected_rows','valid_heights','valid_dbh','valid_circumference','height_sources','height_min','height_max']
    # Unique while preserving order.
    fields=list(dict.fromkeys(fields))
    with (out/'height_inventory_audit.csv').open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader()
        for r in flat:
            r=dict(r);r['height_sources']=json.dumps(r.get('height_sources',{}),ensure_ascii=False);w.writerow(r)
    lines=['# Audit des hauteurs par inventaire','','Cet audit est en lecture seule et ne contient aucune donnée individuelle.','', '| Année | Fichiers candidats | Lignes sélectionnées | Hauteurs valides |','|---:|---:|---:|---:|']
    for year in YEARS:
        xs=[r for r in flat if int(r['inventory_year'])==year]
        lines.append(f"| {year} | {len(xs)} | {sum(int(r['selected_rows']) for r in xs)} | {sum(int(r['valid_heights']) for r in xs)} |")
    lines += ['','## Fichiers candidats détaillés','']
    for r in flat:
        if int(r['valid_heights'])>0:
            lines.append(f"- **{r['inventory_year']}** — `{Path(r['file']).name}`: {r['valid_heights']}/{r['selected_rows']} hauteurs; source={r.get('height_sources',{})}; colonnes hauteur/DBH/circonférence=`{r.get('height_column')}` / `{r.get('dbh_column')}` / `{r.get('circumference_column')}`.")
    (out/'height_inventory_audit.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(f'[OK] audit written to {out}')
    for year in YEARS:
        xs=[r for r in flat if int(r['inventory_year'])==year]
        print(f"[SUMMARY] {year}: candidate_files={len(xs)} valid_heights={sum(int(r['valid_heights']) for r in xs)}")
if __name__=='__main__':main()
