#!/usr/bin/env python3
"""Focused audit of the Écouves empirical target-state reconstruction chain.

Run from the PyDynamicForest repository root. Produces one Markdown file and
modifies nothing.
"""
from __future__ import annotations
import argparse, re, subprocess
from pathlib import Path

CANDIDATES = [
    "scripts/article/validate_ecouves_a5_initial_states.py",
    "scripts/article/run_ecouves_a5_main_1985_2020.py",
    "simulations/article/ecouves_a5/main_dynamic_trajectory.py",
    "simulations/article/ecouves_a5/pydynamicforest_adapter.py",
    "scripts/article/diagnose_ecouves_a5_distributions.py",
    "simulations/article/ecouves_a5/distributional_diagnostics.py",
]
PATTERN = re.compile(
    r"ecouves_a5_grid_state|native_initial_state|solver_compatibility|"
    r"load_q9e4|convert_q9e4|height_provider|savine|allometr|height|"
    r"hauteur|residual|1985|1992|1998|2016|2020|savez|target",
    re.I,
)

def excerpt(path: Path, context: int = 3) -> list[tuple[int,int,list[str]]]:
    lines=path.read_text(encoding="utf-8",errors="replace").splitlines()
    hits=[i for i,line in enumerate(lines) if PATTERN.search(line)]
    ranges=[]
    for i in hits:
        a=max(0,i-context); b=min(len(lines),i+context+1)
        if ranges and a<=ranges[-1][1]: ranges[-1]=(ranges[-1][0],max(ranges[-1][1],b))
        else:ranges.append((a,b))
    return [(a+1,b,lines[a:b]) for a,b in ranges]

def git_output(repo: Path, args: list[str]) -> str:
    try:
        return subprocess.run(["git",*args],cwd=repo,text=True,capture_output=True,check=True).stdout.strip()
    except Exception as exc:
        return f"[indisponible: {exc}]"

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--repo",type=Path,default=Path.cwd())
    ap.add_argument("--output",type=Path,default=Path("audit_ecouves_target_state_chain.md"))
    a=ap.parse_args(); repo=a.repo.resolve(); out=a.output.resolve()
    lines=["# Audit ciblé de la chaîne de reconstruction des cibles Écouves A5","",f"- Dépôt : `{repo}`","- Audit en lecture seule.",""]

    # Locate source-grid constructors and provider definitions across repository.
    located=[]
    for p in repo.rglob("*.py"):
        if any(x in p.parts for x in (".git","__pycache__")): continue
        text=p.read_text(encoding="utf-8",errors="replace")
        if re.search(r"ecouves_a5_grid_state|q9e4|savine-douglas|height_provider",text,re.I):
            located.append(p)
    lines += ["## Fichiers contenant les marqueurs de construction","",*(f"- `{p.relative_to(repo)}`" for p in sorted(located)),""]

    ordered=[]
    for rel in CANDIDATES:
        p=repo/rel
        if p.exists() and p not in ordered: ordered.append(p)
    for p in sorted(located):
        if p not in ordered: ordered.append(p)

    lines += ["## Extraits des fichiers candidats",""]
    for p in ordered:
        lines += [f"### `{p.relative_to(repo)}`",""]
        chunks=excerpt(p)
        if not chunks:
            lines.append("Aucun extrait ciblé.")
        else:
            for start,end,content in chunks:
                lines += [f"Lignes {start}–{end} :","```python",*content,"```",""]

    lines += ["## Historique Git des fichiers principaux",""]
    for p in ordered[:12]:
        rel=str(p.relative_to(repo))
        log=git_output(repo,["log","--follow","--date=short","--pretty=format:%h %ad %s","--",rel])
        lines += [f"### `{rel}`","```text",log or "Aucun commit trouvé.","```",""]

    lines += ["## Recherche historique des noms d’états sources","","```text"]
    lines.append(git_output(repo,["log","-S","ecouves_a5_grid_state","--all","--oneline","--","*.py"]))
    lines += ["```","","## Arborescence des sorties cibles","","```text"]
    target=repo/"outputs/article_scenarios/ecouves_a5_solver_compatibility"
    if target.exists():
        for p in sorted(target.iterdir()): lines.append(f"{p.name}\t{p.stat().st_size} bytes")
    else: lines.append("Dossier absent.")
    lines += ["```",""]
    out.write_text("\n".join(lines)+"\n",encoding="utf-8")
    print(f"[OK] {out}")

if __name__=="__main__":main()
