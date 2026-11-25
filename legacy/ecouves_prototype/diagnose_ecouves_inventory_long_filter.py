#!/usr/bin/env python3
"""Diagnose why Q-9E.1 rows were filtered to zero.

Run from the PyDynamicForest repository root. The script writes one Markdown
report and modifies no source file.
"""
from pathlib import Path
import pandas as pd

SOURCE = Path("outputs/article_scenarios/ecouves_a5_reconstruction/ecouves_a5_inventory_long.csv")
OUTPUT = Path("diagnose_ecouves_inventory_long_filter.md")
TARGET_YEARS = (1985, 1992, 1998, 2016, 2020)

if not SOURCE.is_file():
    raise FileNotFoundError(SOURCE)

frame = pd.read_csv(SOURCE, encoding="utf-8-sig")

lines = [
    "# Diagnostic du filtrage de `ecouves_a5_inventory_long.csv`",
    "",
    f"- Fichier : `{SOURCE.resolve()}`",
    f"- Nombre total de lignes : **{len(frame)}**",
    f"- Colonnes : `{list(frame.columns)}`",
    "",
]

for column in ("site", "plot", "series_status", "included_in_reference_state", "inclusion_rule", "year"):
    lines += [f"## Colonne `{column}`", ""]
    if column not in frame.columns:
        lines += ["Colonne absente.", ""]
        continue
    counts = frame[column].astype(str).value_counts(dropna=False)
    lines += ["| Valeur | Effectif |", "|---|---:|"]
    for value, count in counts.head(50).items():
        safe = str(value).replace("|", "\\|")
        lines.append(f"| `{safe}` | {int(count)} |")
    lines.append("")

lines += ["## Effectifs bruts par année cible", "", "| Année | Lignes | DBH valides | Somme des facteurs d'expansion |", "|---:|---:|---:|---:|"]
for year in TARGET_YEARS:
    if "year" in frame.columns:
        selected = frame[pd.to_numeric(frame["year"], errors="coerce").eq(year)]
    else:
        selected = frame.iloc[0:0]
    if "diameter_cm" in selected.columns:
        valid_dbh = int(pd.to_numeric(selected["diameter_cm"], errors="coerce").gt(0).sum())
    else:
        valid_dbh = 0
    if "expansion_factor_ha" in selected.columns:
        expansion = pd.to_numeric(selected["expansion_factor_ha"], errors="coerce").sum(min_count=1)
    else:
        expansion = float("nan")
    lines.append(f"| {year} | {len(selected)} | {valid_dbh} | {expansion:.6f} |")

lines += [
    "",
    "## Interprétation attendue",
    "",
    "Le précédent audit a obtenu zéro ligne parce qu'un filtre a été appliqué avec une valeur qui ne correspond pas au codage réel d'au moins une colonne (`plot` ou `included_in_reference_state`). Ce rapport permet de corriger ce filtre sans toucher aux données.",
]

OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"[OK] {OUTPUT}")
