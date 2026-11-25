#!/usr/bin/env python3
"""Trace the provenance of ecouves_a5_inventory_long.csv.

Run from the PyDynamicForest repository root. The audit is read-only and writes
one Markdown report. It inspects the constructor, Git history, output manifest,
and the recent-year records, with special attention to 2013, 2016 and 2020.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

import pandas as pd


def run(cwd: Path, command: list[str]) -> str:
    completed = subprocess.run(command, cwd=cwd, text=True, capture_output=True)
    output = (completed.stdout + completed.stderr).strip()
    return output or "[aucune sortie]"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def excerpt(path: Path, terms: tuple[str, ...], context: int = 4) -> list[str]:
    if not path.is_file():
        return [f"Fichier absent : `{path}`"]
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    indices = [
        index for index, line in enumerate(lines)
        if any(term.lower() in line.lower() for term in terms)
    ]
    ranges: list[tuple[int, int]] = []
    for index in indices:
        start = max(0, index - context)
        end = min(len(lines), index + context + 1)
        if ranges and start <= ranges[-1][1]:
            ranges[-1] = (ranges[-1][0], max(ranges[-1][1], end))
        else:
            ranges.append((start, end))
    rendered = []
    for start, end in ranges:
        rendered.append(f"Lignes {start + 1}-{end} :")
        rendered.append("```python")
        rendered.extend(lines[start:end])
        rendered.append("```")
    return rendered or ["Aucun passage ciblé trouvé."]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument(
        "--inventory",
        type=Path,
        default=Path(
            "outputs/article_scenarios/ecouves_a5_reconstruction/"
            "ecouves_a5_inventory_long.csv"
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("audit_ecouves_inventory_provenance.md"),
    )
    args = parser.parse_args()

    repo = args.repo.resolve()
    inventory = args.inventory.resolve()
    output = args.output.resolve()
    constructor = repo / "scripts/article/audit_ecouves_a5.py"

    if not inventory.is_file():
        raise FileNotFoundError(inventory)

    frame = pd.read_csv(inventory, encoding="utf-8-sig")
    years = (1985, 1992, 1998, 2001, 2007, 2010, 2013, 2016, 2020)

    report = [
        "# Audit de provenance de `ecouves_a5_inventory_long.csv`",
        "",
        "## Objet",
        "",
        "Établir comment les inventaires individuels récents, notamment 2013, 2016 et 2020, ont été construits et distinguer les mesures, les reports de valeurs et les règles d'inclusion.",
        "",
        "## Fichier audité",
        "",
        f"- Chemin : `{inventory}`",
        f"- SHA-256 : `{sha256(inventory)}`",
        f"- Lignes : **{len(frame)}**",
        f"- Colonnes : `{list(frame.columns)}`",
        "",
        "## Synthèse par année",
        "",
        "| Année | Lignes | has_measurement=True | included=True | DBH positifs inclus | Circonférences distinctes incluses |",
        "|---:|---:|---:|---:|---:|---:|",
    ]

    for year in years:
        rows = frame[pd.to_numeric(frame["year"], errors="coerce").eq(year)].copy()
        measured = rows["has_measurement"].astype(str).str.lower().isin(("true", "1", "yes"))
        included = rows["included_in_reference_state"].astype(str).str.lower().isin(("true", "1", "yes"))
        diameters = pd.to_numeric(rows["diameter_cm"], errors="coerce")
        circumferences = pd.to_numeric(rows["circumference_cm"], errors="coerce")
        report.append(
            f"| {year} | {len(rows)} | {int(measured.sum())} | {int(included.sum())} | "
            f"{int((included & diameters.gt(0)).sum())} | "
            f"{circumferences[included & circumferences.gt(0)].nunique()} |"
        )

    report += [
        "",
        "## Détection des valeurs reportées entre inventaires",
        "",
        "Les tableaux ci-dessous comptent, parmi les arbres présents deux années successives, les circonférences strictement identiques. Une forte proportion peut signaler un report de la dernière mesure plutôt qu'une nouvelle observation.",
        "",
        "| Transition | Arbres communs avec valeurs positives | Circonférences identiques | Proportion identique |",
        "|---|---:|---:|---:|",
    ]

    for first, second in zip(years[:-1], years[1:]):
        a = frame[pd.to_numeric(frame["year"], errors="coerce").eq(first)][
            ["tree_id", "circumference_cm"]
        ].rename(columns={"circumference_cm": "c1"})
        b = frame[pd.to_numeric(frame["year"], errors="coerce").eq(second)][
            ["tree_id", "circumference_cm"]
        ].rename(columns={"circumference_cm": "c2"})
        joined = a.merge(b, on="tree_id", how="inner")
        joined["c1"] = pd.to_numeric(joined["c1"], errors="coerce")
        joined["c2"] = pd.to_numeric(joined["c2"], errors="coerce")
        valid = joined[joined["c1"].gt(0) & joined["c2"].gt(0)]
        same = int((valid["c1"] == valid["c2"]).sum())
        fraction = same / len(valid) if len(valid) else float("nan")
        report.append(
            f"| {first}→{second} | {len(valid)} | {same} | {100 * fraction:.1f}% |"
        )

    report += [
        "",
        "## Règles d'inclusion par année",
        "",
    ]
    grouped = (
        frame.groupby(["year", "series_status", "inclusion_rule", "included_in_reference_state"])
        .size()
        .reset_index(name="count")
    )
    report += ["| Année | series_status | inclusion_rule | included | Effectif |", "|---:|---|---|---|---:|"]
    for row in grouped.itertuples(index=False):
        report.append(
            f"| {row.year} | `{row.series_status}` | `{row.inclusion_rule}` | `{row.included_in_reference_state}` | {row.count} |"
        )

    report += [
        "",
        "## Extraits du constructeur",
        "",
        *excerpt(
            constructor,
            (
                "inventory_long", "2013", "2016", "2020", "carry", "forward",
                "Francois", "Ningre", "has_measurement", "included_in_reference_state",
                "inclusion_rule", "circumference",
            ),
        ),
        "",
        "## Historique Git du constructeur",
        "",
        "```text",
        run(
            repo,
            [
                "git", "log", "--follow", "--date=iso", "--stat",
                "--", "scripts/article/audit_ecouves_a5.py",
            ],
        ),
        "```",
        "",
        "## Historique Git des changements touchant les années récentes",
        "",
        "```text",
        run(
            repo,
            [
                "git", "log", "--all", "-S", "2020", "--oneline", "--",
                "scripts/article/audit_ecouves_a5.py",
                "simulations/article/ecouves_a5/*.py",
            ],
        ),
        "```",
        "",
        "## Métadonnées voisines",
        "",
    ]

    parent = inventory.parent
    for path in sorted(parent.iterdir()):
        report.append(f"- `{path.name}` ({path.stat().st_size} octets)")

    report += [
        "",
        "## Décision attendue",
        "",
        "À partir de cet audit, décider si `ecouves_a5_inventory_long.csv` est la population diamétrique complète à conserver pour 2013, 2016 et 2020, ou si les années récentes doivent être reconstruites directement depuis le fichier de François Ningre.",
    ]

    output.write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"[OK] {output}")


if __name__ == "__main__":
    main()
