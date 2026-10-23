#!/usr/bin/env python3
"""Command-line audit for Q-9E.1."""
from __future__ import annotations
import argparse, sys
from pathlib import Path

def repo_root()->Path:
    here=Path(__file__).resolve()
    for p in [Path.cwd(),*Path.cwd().parents,here.parent,*here.parents]:
        if (p/"simulations"/"article"/"ecouves_a5").exists(): return p
    raise RuntimeError("cannot locate PyDynamicForest root")
ROOT=repo_root()
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from simulations.article.ecouves_a5.inventory import read_individual_inventory,read_reference,candidate_rules,reconcile,detect_anomalies,write_csv,YEARS

def fmt(v):
    if v is None:return "NA"
    if isinstance(v,float):return f"{v:.6g}"
    return str(v)

def report(ind_path,ref_path,imeta,rmeta,long,cands,rec,anom,area):
    status={y:{s:sum(r["year"]==y and r["status"]==s for r in long) for s in ("rest","sec","chab")} for y in YEARS}
    dec=[a for a in anom if a["anomaly_type"]=="circumference_decrease"]
    lines=["# Q-9E.1 - Audit des inventaires individuels d'Écouves A5","","> Portée : audit diamétrique uniquement. Aucune hauteur n'est imputée.","","## 1. Fichiers et feuilles","",f"- Inventaires : `{ind_path.name}`, feuille `{imeta['sheet']}`.",f"- Référence agrégée : `{ref_path.name}`, feuille `{rmeta['sheet']}`.","- Les lignes d'autres dispositifs ne sont ni exportées ni rapportées.","","## 2. Faits établis","",f"- {len(set(r['tree_id'] for r in long))} arbres distincts; {len(YEARS)} inventaires.",f"- Surface analytique : {area:.4f} ha; facteur d'expansion : {1/area:.10f} tiges/ha.","- Circonférences en cm, diamètres en cm, densités en tiges/ha, surface terrière en m²/ha.","- `AA` est exclue de la table analytique.","","## 3. Ventilation des statuts","","| Année | Série | rest | sec | chab |","|---:|---|---:|---:|---:|"]
    for y in YEARS: lines.append(f"| {y} | {'reference' if y in {x['year'] for x in rec if x['series_status']=='reference'} else 'audit'} | {status[y]['rest']} | {status[y]['sec']} | {status[y]['chab']} |")
    lines += ["","## 4. Réconciliation","","Le score est la somme des erreurs relatives absolues sur N et Cg. Les égalités à 1e-12 près suivent l'ordre de parcimonie documenté dans le code. `exact` exige |ΔN| ≤ 0,02 tige/ha et |ΔCg| ≤ 0,005 cm; `rounding_match` exige |ΔN| ≤ 0,5 et |ΔCg| ≤ 0,05.","","| Année | Série | Règle | n | N calculé | N réf. | Cg calculé | Cg réf. | Statut |","|---:|---|---|---:|---:|---:|---:|---:|---|"]
    for x in rec: lines.append(f"| {x['year']} | {x['series_status']} | {x['selected_rule']} | {x['n_included']} | {fmt(x['N_computed_ha'])} | {fmt(x['N_reference_ha'])} | {fmt(x['Cg_computed_cm'])} | {fmt(x['Cg_reference_cm'])} | {x['match_status']} |")
    surf=[]
    for x in rec:
        if x['N_reference_ha'] is not None and x['n_included']:
            surf.append((x['year'],x['n_included']/x['N_reference_ha']))
    lines += ["","## 5. Inférences soutenues par les calculs","",f"- Les surfaces implicites n/N de la série réconciliée vont de {min(v for _,v in surf):.7f} à {max(v for _,v in surf):.7f} ha, ce qui permet d'évaluer l'hypothèse d'un calcul des densités avec 0,1216 ha malgré certains affichages à 0,1200 ha.","- La règle de 1980 est obtenue par le même classement que les autres années; aucune exception annuelle n'est codée.","","## 6. Anomalies individuelles","",f"- {len(anom)} signalements au total, dont {len(dec)} diminutions de circonférence. Aucune valeur n'a été corrigée."]
    from collections import Counter
    for k,v in sorted(Counter(a['anomaly_type'] for a in anom).items()): lines.append(f"- `{k}` : {v}")
    if dec:
        lines += ["","Diminutions observées :"]
        for a in dec: lines.append(f"- arbre {a['tree_id']}, {a['previous_year']} -> {a['year']} : {a['previous_value']} -> {a['current_value']} cm.")
    lines += ["","## 7. Hypothèses non résolues","","- Les fichiers ne permettent pas d'établir avec certitude le moment exact auquel `sec` ou `chab` devient terminal.","- Les années d'audit sont conservées sans leur inventer d'agrégats de référence.","- Les éventuels écarts résiduels peuvent refléter arrondis, sélection scientifique, écorce ou qualité de mesure.","","## 8. Conclusion pour Q-9E.2","","La chronologie diamétrique est normalisée et les états de référence sont explicitement sélectionnés. Le futur fournisseur de hauteurs devra consommer cette interface sans modifier les règles diamétriques ni les données sources.",""]
    return "\n".join(lines)

def main(argv=None):
    p=argparse.ArgumentParser(); p.add_argument("--individual-data",type=Path,default=ROOT/"data/article/ecouves_a5/raw/Ecouves-A5.xlsx"); p.add_argument("--reference-data",type=Path,default=ROOT/"data/article/ecouves_a5/reference/Douglas2021(116obs).xlsx"); p.add_argument("--output-dir",type=Path,default=ROOT/"outputs/article_scenarios/ecouves_a5_reconstruction"); p.add_argument("--plot-area-ha",type=float,default=0.1216); a=p.parse_args(argv)
    for x in (a.individual_data,a.reference_data):
        if not x.exists(): p.error(f"input file not found: {x}")
    long,im=read_individual_inventory(a.individual_data,a.plot_area_ha); ref,rm=read_reference(a.reference_data); cand=candidate_rules(long,ref,a.plot_area_ha); rec=reconcile(long,cand,ref); an=detect_anomalies(long,im); out=a.output_dir; out.mkdir(parents=True,exist_ok=True)
    public=[{k:v for k,v in r.items() if not k.startswith("_")} for r in long]
    write_csv(out/"ecouves_a5_inventory_long.csv",public); write_csv(out/"ecouves_a5_candidate_rules.csv",cand); write_csv(out/"ecouves_a5_reconciled_inventories.csv",rec); write_csv(out/"ecouves_a5_individual_anomalies.csv",an,["tree_id","year","anomaly_type","previous_year","previous_value","current_value","status","severity","comment"])
    (out/"ecouves_a5_audit_report.md").write_text(report(a.individual_data,a.reference_data,im,rm,long,cand,rec,an,a.plot_area_ha),encoding="utf-8")
    print(f"Q-9E.1 outputs written to {out}")
if __name__=="__main__": main()
