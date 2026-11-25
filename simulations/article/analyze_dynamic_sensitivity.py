# SPDX-License-Identifier: LGPL-3.0-or-later
"""Summarize the Q-9E OAT screening against Ecouves A5 observations."""

from __future__ import annotations

import csv
import json
from math import sqrt
from pathlib import Path

from simulations.article.dynamic_sensitivity import selected_dynamic_sensitivity_cases

OUTPUT_ROOT = Path("outputs/article_scenarios")
BASELINE_DIR = OUTPUT_ROOT / "main_age45" / "rho_0.85"
ANALYSIS_DIR = OUTPUT_ROOT / "comparisons" / "dynamic_sensitivity_age45_rho_0.85"
PRIMARY = ("N", "G", "Dm", "Hm", "H0")
DIAGNOSTIC = ("Dg", "sigma_D", "H0_minus_Hm")


def read_table(directory: Path) -> list[dict[str, str]]:
    path = directory / "observations_simulation.csv"
    if not path.is_file():
        raise FileNotFoundError(path)
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def scores(rows: list[dict[str, str]]) -> dict[str, float]:
    grouped: dict[str, list[float]] = {name: [] for name in PRIMARY + DIAGNOSTIC}
    for row in rows:
        name = row["observable"]
        if name not in grouped or float(row["requested_age"]) <= 45.0:
            continue
        observed = row["observed_value"].strip()
        if not observed:
            continue
        target = float(observed)
        residual = float(row["simulated_value"]) - target
        grouped[name].append(residual / target)

    result = {}
    for name, values in grouped.items():
        result[f"rrmse_{name}"] = (
            sqrt(sum(value * value for value in values) / len(values))
            if values else float("nan")
        )
    primary_values = [
        value
        for name in PRIMARY
        for value in grouped[name]
    ]
    result["primary_score"] = sqrt(
        sum(value * value for value in primary_values) / len(primary_values)
    )
    return result


def main() -> None:
    cases = selected_dynamic_sensitivity_cases()
    entries = [
        {
            "case": "baseline",
            "parameter": "baseline",
            "multiplier": 1.0,
            "baseline_value": "",
            "perturbed_value": "",
            **scores(read_table(BASELINE_DIR)),
        }
    ]
    for case in cases:
        directory = OUTPUT_ROOT / case.scenario.output_relative_path
        metadata = json.loads((directory / "metadata.json").read_text(encoding="utf-8"))
        if not metadata["completed_full_horizon"]:
            raise ValueError(f"Incomplete case: {case.name}")
        entries.append(
            {
                "case": case.name,
                "parameter": case.parameter,
                "multiplier": case.multiplier,
                "baseline_value": case.baseline_value,
                "perturbed_value": case.perturbed_value,
                **scores(read_table(directory)),
            }
        )

    entries.sort(key=lambda row: row["primary_score"])
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = ANALYSIS_DIR / "oat_scores.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(entries[0]))
        writer.writeheader()
        writer.writerows(entries)

    md_path = ANALYSIS_DIR / "oat_summary.md"
    lines = [
        "# Local dynamic-parameter sensitivity at age 45, rho=0.85",
        "",
        "The score is the root mean square relative error over post-initial observations for N, G, Dm, Hm, and H0. It is a screening criterion, not a likelihood or validation metric.",
        "",
        "| Rank | Case | Parameter | Multiplier | Primary score | N | G | Dm | Hm | H0 | sigma_D | H0-Hm |",
        "|---:|:---|:---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for rank, row in enumerate(entries, 1):
        lines.append(
            f"| {rank} | {row['case']} | {row['parameter']} | {float(row['multiplier']):.2f} "
            f"| {row['primary_score']:.4f} | {row['rrmse_N']:.4f} "
            f"| {row['rrmse_G']:.4f} | {row['rrmse_Dm']:.4f} "
            f"| {row['rrmse_Hm']:.4f} | {row['rrmse_H0']:.4f} "
            f"| {row['rrmse_sigma_D']:.4f} | {row['rrmse_H0_minus_Hm']:.4f} |"
        )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(md_path.read_text(encoding="utf-8"))
    print(f"[OK] {csv_path}")
    print(f"[OK] {md_path}")


if __name__ == "__main__":
    main()
