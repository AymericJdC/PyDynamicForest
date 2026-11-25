#!/usr/bin/env python3
"""Audit the post-Francois Ecouves allometry chain in repo and local archive.

Run from PyDynamicForest root. Writes one Markdown report, changes nothing.
"""
from __future__ import annotations
import argparse, re, subprocess
from pathlib import Path

TERMS = re.compile(
    r"francois|ningre|height_dbh_samples|measured_height|log_dbh|allometr|"
    r"beta0|beta1|hauteur_ech|Ht01|Ht07|Ht10|Ht13|Ht16|Ht20|"
    r"residual|initial_cloud|projected_state|regulariz",
    re.I,
)
TEXT_EXT={'.py','.md','.json','.csv','.txt','.sh','.qmd','.yaml','.yml'}
SKIP={'.git','__pycache__','.pytest_cache','.mypy_cache','.ruff_cache','site-packages'}

def run(cwd:Path,args:list[str])->str:
    p=subprocess.run(args,cwd=cwd,text=True,capture_output=True)
    return (p.stdout+p.stderr).strip()

def scan(root:Path,label:str):
    records=[]
    if not root.exists(): return records
    for p in root.rglob('*'):
        if not p.is_file() or p.suffix.lower() not in TEXT_EXT or any(x in SKIP for x in p.parts): continue
        if p.stat().st_size>3_000_000: continue
        try:t=p.read_text(encoding='utf-8',errors='replace')
        except Exception:continue
        hits=[]
        for i,line in enumerate(t.splitlines(),1):
            if TERMS.search(line):
                hits.append((i,line.strip()[:240]))
                if len(hits)>=8:break
        if hits:
            records.append((p.stat().st_mtime,p,label,hits))
    return sorted(records,reverse=True)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--repo',type=Path,default=Path.cwd())
    ap.add_argument('--archive',type=Path,default=Path.home()/'Downloads'/'ECOUVES_NUM_2026-11-18')
    ap.add_argument('--output',type=Path,default=Path('audit_recent_ecouves_allometry_chain.md'))
    a=ap.parse_args(); repo=a.repo.resolve(); archive=a.archive.resolve(); out=a.output.resolve()
    rec=scan(repo,'repo')+scan(archive,'archive locale')
    rec=sorted(rec,reverse=True)
    lines=['# Audit de la chaîne allométrique Écouves récente','',
           f'- Dépôt : `{repo}`',f'- Archive : `{archive}`','- Audit en lecture seule.','',
           '## État Git actuel','', '```text',run(repo,['git','status','--short']), '```','',
           '## Commits depuis le 1er novembre 2026','', '```text',
           run(repo,['git','log','--since=2026-11-01','--date=short','--pretty=format:%h %ad %s']), '```','',
           '## Fichiers repérés, du plus récent au plus ancien','']
    for _,p,label,hits in rec[:80]:
        try: rel=p.relative_to(repo if label=='repo' else archive)
        except ValueError: rel=p
        lines += [f'### `{rel}`', '',f'- Source : {label}',f'- Dernière modification : {p.stat().st_mtime_ns}', '- Extraits :']
        for n, s in hits:
            safe_snippet = s.replace('`', "'")
            lines.append(f"  - L{n}: `{safe_snippet}`")
        lines.append('')
    lines += ['## Recherche Git historique ciblée','']
    for term in ['height_dbh_samples','measured_height','log_dbh_A1_A2_A5','hauteur_ech','Francois Ningre']:
        lines += [f'### `{term}`','```text',run(repo,['git','log','--all','-S',term,'--oneline','--','*.py','*.md','*.json','*.csv']),'```','']
    out.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(f'[OK] {out}')
if __name__=='__main__':main()
