#!/usr/bin/env python3
"""Generate Q-9E.3 deterministic height reconstructions for Écouves A5."""
from __future__ import annotations
import argparse,csv,sys
from pathlib import Path

def repo_root():
    here=Path(__file__).resolve()
    for p in [Path.cwd(),*Path.cwd().parents,*here.parents]:
        if (p/"simulations/article/ecouves_a5").exists(): return p
    raise RuntimeError("cannot locate PyDynamicForest root")
ROOT=repo_root(); sys.path.insert(0,str(ROOT))
from simulations.article.ecouves_a5.height_types import AdapterMode
from simulations.article.ecouves_a5.height_reconstruction import reconstruct_year
from simulations.article.ecouves_a5.height_export import write_rows,DIAGNOSTIC_COLUMNS
from simulations.article.ecouves_a5.savine_height_provider import SavineDouglasHeightProvider,DomainPolicy,REFERENCE
from simulations.article.ecouves_a5.inventory import REFERENCE_YEARS

EXTRA_COLUMNS=("provider_version","variant","domain_status","domain_reasons","quadratic_mean_diameter_cm","basal_area_m2_ha","local_effect_lambda")

def read_csv(path):
    with path.open(encoding="utf-8",newline="") as f:return list(csv.DictReader(f))
def main(argv=None):
    p=argparse.ArgumentParser(); p.add_argument("--inventory-long",type=Path,default=ROOT/"outputs/article_scenarios/ecouves_a5_reconstruction/ecouves_a5_inventory_long.csv"); p.add_argument("--output-dir",type=Path,default=ROOT/"outputs/article_scenarios/ecouves_a5_height_reconstruction"); p.add_argument("--years",nargs="*",type=int); p.add_argument("--adapter-mode",choices=[x.value for x in AdapterMode],default=AdapterMode.REFERENCE_STATE.value); p.add_argument("--strict-domain",action="store_true"); a=p.parse_args(argv)
    if not a.inventory_long.exists(): p.error(f"input not found: {a.inventory_long}")
    rows=read_csv(a.inventory_long); mode=AdapterMode(a.adapter_mode); years=a.years or (sorted(REFERENCE_YEARS) if mode is AdapterMode.REFERENCE_STATE else sorted({int(r['year']) for r in rows}))
    provider=SavineDouglasHeightProvider(domain_policy=DomainPolicy.STRICT if a.strict_domain else DomainPolicy.PERMISSIVE)
    results=[reconstruct_year(rows,y,provider,mode) for y in years]; out=a.output_dir; out.mkdir(parents=True,exist_ok=True)
    assigned=[r for result in results for r in result.assignment_rows]
    from simulations.article.ecouves_a5.height_export import ASSIGNMENT_COLUMNS
    write_rows(out/"ecouves_a5_assigned_heights.csv",assigned,ASSIGNMENT_COLUMNS+EXTRA_COLUMNS)
    diag=[]; domain=[]; comparisons=[]
    for result in results:
        diag.append({"site":result.context.site,"plot":result.context.plot,"year":result.year,"age":result.context.age,**result.diagnostics.__dict__,"n_extrapolated":result.n_extrapolated})
        domain.append({"year":result.year,"series_status":result.context.series_status,"adapter_mode":result.context.adapter_mode.value,"n_trees":len(result.trees),"n_extrapolated":result.n_extrapolated,"stand_covariate_domain":"unknown","validation_status":result.validation.status})
        for c in result.target_comparisons: comparisons.append({"year":result.year,**c.__dict__})
    write_rows(out/"ecouves_a5_height_diagnostics.csv",diag,DIAGNOSTIC_COLUMNS+("n_extrapolated",))
    write_rows(out/"ecouves_a5_height_domain_diagnostics.csv",domain,("year","series_status","adapter_mode","n_trees","n_extrapolated","stand_covariate_domain","validation_status"))
    write_rows(out/"ecouves_a5_height_target_comparisons.csv",comparisons,("year","metric","computed","target","difference","absolute_difference","relative_difference","status"))
    lines=["# Q-9E.3 - Reconstruction provisoire des hauteurs d'Écouves A5","",f"Source : {REFERENCE}","","La relation nationale est appliquée en effets fixes, pour une structure équienne, avec lambda = 0. Les hauteurs sont des prédictions et non des observations. Les domaines publiés de BA et Dg ne sont pas disponibles.","","| Année | Série | Arbres | Extrapolations DBH | Couverture | H moyenne (m) | H quadratique (m) | H dominante (m) |","|---:|---|---:|---:|---:|---:|---:|---:|"]
    def f(value): return "NA" if value is None else f"{value:.3f}"
    for r in results:
        d=r.diagnostics; lines.append(f"| {r.year} | {r.context.series_status} | {len(r.trees)} | {r.n_extrapolated} | {d.weighted_coverage:.3f} | {f(d.mean_height_m)} | {f(d.quadratic_mean_height_m)} | {f(d.dominant_height_m)} |")
    lines += ["","Aucune hauteur n'a été recalée sur un agrégat cible. Aucune dispersion aléatoire n'a été ajoutée.",""]
    (out/"ecouves_a5_height_reconstruction_report.md").write_text("\n".join(lines),encoding="utf-8")
    print(f"Q-9E.3 outputs written to {out}")
if __name__=="__main__":main()
