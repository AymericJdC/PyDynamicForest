# SPDX-License-Identifier: LGPL-3.0-or-later
"""Compare completed Q-9D age-45 simulations across selected rho values."""

from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path("outputs/article_scenarios/main_age45")
OUTPUT = Path("outputs/article_scenarios/comparisons/main_age45")
RHOS = ("0.50", "0.85", "0.95")


def read_rows(rho: str) -> list[dict[str, str]]:
    path = ROOT / f"rho_{rho}" / "observations_simulation.csv"
    if not path.is_file():
        raise FileNotFoundError(f"Missing scenario table: {path}")
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def detect_name_field(rows: list[dict[str, str]]) -> str:
    fields = tuple(rows[0])
    for candidate in (
        "observable_name",
        "observable",
        "variable",
        "quantity",
        "metric",
        "name",
    ):
        if candidate in fields:
            return candidate
    excluded = {"requested_age", "observed_value", "simulated_value"}
    for field in fields:
        if field not in excluded and len({row[field] for row in rows}) > 1:
            return field
    raise KeyError(f"Cannot identify observable-name column. Fields: {fields}")


def number(value: str) -> float | None:
    text = (value or "").strip()
    return None if not text else float(text)


def main() -> None:
    tables = {rho: read_rows(rho) for rho in RHOS}
    name_field = detect_name_field(tables["0.85"])
    indexed: dict[str, dict[tuple[float, str], dict[str, float | None]]] = {}

    for rho, rows in tables.items():
        indexed[rho] = {
            (float(row["requested_age"]), row[name_field]): {
                "observed": number(row["observed_value"]),
                "simulated": number(row["simulated_value"]),
            }
            for row in rows
        }

    keys = list(indexed["0.85"])
    if any(set(indexed[rho]) != set(keys) for rho in RHOS):
        raise ValueError("Scenario tables do not contain identical age-observable keys.")

    output_rows: list[dict[str, object]] = []
    for age, observable in keys:
        observed = indexed["0.85"][(age, observable)]["observed"]
        simulated = {
            rho: indexed[rho][(age, observable)]["simulated"] for rho in RHOS
        }
        values = [value for value in simulated.values() if value is not None]
        spread = max(values) - min(values) if values else None
        spread_percent = (
            100.0 * spread / abs(observed)
            if spread is not None and observed not in (None, 0.0)
            else None
        )
        output_rows.append(
            {
                "age": age,
                "observable": observable,
                "observed_value": observed,
                "simulated_rho_0.50": simulated["0.50"],
                "simulated_rho_0.85": simulated["0.85"],
                "simulated_rho_0.95": simulated["0.95"],
                "scenario_spread": spread,
                "scenario_spread_percent_of_observed": spread_percent,
            }
        )

    OUTPUT.mkdir(parents=True, exist_ok=True)
    csv_path = OUTPUT / "rho_sensitivity_comparison.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(output_rows[0]))
        writer.writeheader()
        writer.writerows(output_rows)

    age69 = [row for row in output_rows if row["age"] == 69.0]
    md_path = OUTPUT / "rho_sensitivity_age69.md"
    lines = [
        "# Sensitivity to the reconstructed initial dependence at age 69",
        "",
        "All simulations start at age 45 and use unchanged dynamic parameters.",
        "",
        "| Observable | Observed | rho=0.50 | rho=0.85 | rho=0.95 | Spread | Spread / observed (%) |",
        "|:---|---:|---:|---:|---:|---:|---:|",
    ]

    def fmt(value: object, digits: int = 4) -> str:
        return "NA" if value is None else f"{float(value):.{digits}f}"

    for row in age69:
        lines.append(
            f"| {row['observable']} | {fmt(row['observed_value'])} "
            f"| {fmt(row['simulated_rho_0.50'])} "
            f"| {fmt(row['simulated_rho_0.85'])} "
            f"| {fmt(row['simulated_rho_0.95'])} "
            f"| {fmt(row['scenario_spread'])} "
            f"| {fmt(row['scenario_spread_percent_of_observed'], 2)} |"
        )

    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[OK] {csv_path}")
    print(f"[OK] {md_path}")
    print()
    print(md_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
