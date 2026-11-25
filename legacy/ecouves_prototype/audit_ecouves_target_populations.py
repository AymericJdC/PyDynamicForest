#!/usr/bin/env python3
"""Audit complete A5 target populations independently of the height sample.

Run from the PyDynamicForest repository root. Writes one Markdown report.
No source file is modified.
"""
from pathlib import Path
import pandas as pd

ROOT = Path.home() / "Downloads" / "ECOUVES_NUM_2026-11-18"
INV = Path("outputs/article_scenarios/ecouves_a5_reconstruction/ecouves_a5_inventory_long.csv")
COV = ROOT / "02_CALIBRATION_A_CONSERVER/ecouves_multiyear_regularized_targets/01_inputs_audit/ecouves_selected_years_coverage.csv"
SER = ROOT / "03_DONNEES_SOURCES_RESTREINTES/douglas_ecouves_series_3.csv"
OUT = Path("audit_ecouves_target_populations.md")
YEARS = (1985, 1992, 1998, 2016, 2020)
PLANTING_YEAR = 1948

for p in (INV, COV, SER):
    if not p.is_file():
        raise FileNotFoundError(p)

inv = pd.read_csv(INV, encoding="utf-8-sig")
cov = pd.read_csv(COV, encoding="utf-8-sig")
ser = pd.read_csv(SER, encoding="utf-8-sig")

# Q-9E.1 already contains the selected complete individual inventories.
if "included_in_reference_state" in inv:
    flag = inv["included_in_reference_state"].astype(str).str.lower().isin(("true", "1", "yes"))
    inv = inv[flag].copy()
if "plot" in inv:
    inv = inv[inv["plot"].astype(str).str.upper().eq("A5")].copy()

# Aggregate series has ages, not years. The biological convention is age = year - 1948.
ser = ser.copy()
ser["year_from_age"] = pd.to_numeric(ser["age"], errors="coerce") + PLANTING_YEAR

lines = [
    "# Audit des populations cibles Écouves A5",
    "",
    "Le dénominateur d'une couverture en hauteur doit être l'inventaire individuel complet, pas le sous-échantillon de hauteurs de François.",
    "",
    "| Année | Arbres Q-9E.1 | N Q-9E.1 (ha-1) | N série agrégée | DBH dans l'audit précédent | H mesurées | Verdict |",
    "|---:|---:|---:|---:|---:|---:|---|",
]

for year in YEARS:
    rows = inv[pd.to_numeric(inv["year"], errors="coerce").eq(year)]
    n_trees = len(rows)
    if "expansion_factor_ha" in rows and n_trees:
        n_ha = pd.to_numeric(rows["expansion_factor_ha"], errors="coerce").sum()
    else:
        n_ha = float("nan")
    agg = ser[ser["year_from_age"].round().eq(year)]
    n_agg = pd.to_numeric(agg["N"], errors="coerce").iloc[0] if len(agg) == 1 else float("nan")
    old = cov[pd.to_numeric(cov["biological_year"], errors="coerce").eq(year)]
    old_dbh = int(old["A5_valid_dbh_records"].iloc[0]) if len(old) else 0
    h = int(old["A5_measured_heights"].iloc[0]) if len(old) else 0
    if n_trees == 0:
        verdict = "population complète absente"
    elif old_dbh < n_trees:
        verdict = "fichier François = sous-échantillon; utiliser Q-9E.1 pour les DBH"
    else:
        verdict = "effectifs individuels cohérents à vérifier contre N"
    lines.append(
        f"| {year} | {n_trees} | {n_ha:.3f} | {n_agg:.3f} | {old_dbh} | {h} | {verdict} |"
    )

lines += [
    "",
    "## Décision de reconstruction",
    "",
    "- La population diamétrique complète doit provenir de `ecouves_a5_inventory_long.csv` pour les cinq années.",
    "- Les fichiers de François fournissent les hauteurs totales mesurées et les résidus allométriques, notamment pour 2016 et 2020.",
    "- Les hauteurs manquantes seront complétées par l'allométrie ad hoc de l'année et la distribution empirique centrée de ses résidus.",
    "- `HbH`/`ht_vv` reste exclue de la hauteur totale.",
]
OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"[OK] {OUT}")
