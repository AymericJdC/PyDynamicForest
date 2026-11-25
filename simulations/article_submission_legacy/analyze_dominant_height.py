# SPDX-License-Identifier: LGPL-3.0-or-later
"""Analyze temporal regularity of dominant-height diagnostics."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

OPERATORS = {
    "legacy": "legacy_top_height",
    "current": "top_height_current",
    "proportional": "proportional_top_height",
}


def load_rows(csv_path: str | Path) -> list[dict]:
    """Load and type the dominant-height comparison time series."""
    path = Path(csv_path)
    with path.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    if not rows:
        raise ValueError("The dominant-height time series is empty.")

    required = {
        "step_index",
        "age",
        "threshold_dbh_index",
        "fraction_used_from_threshold_class",
        *OPERATORS.values(),
    }
    missing = required.difference(rows[0])
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    for row in rows:
        row["step_index"] = int(row["step_index"])
        row["threshold_dbh_index"] = int(row["threshold_dbh_index"])
        for field in (
            "age",
            "fraction_used_from_threshold_class",
            *OPERATORS.values(),
        ):
            row[field] = float(row[field])
    return rows


def _series(rows: list[dict], field: str) -> list[float]:
    return [float(row[field]) for row in rows]


def _increment_metrics(values: list[float]) -> dict[str, float | int]:
    increments = [current - previous for previous, current in zip(values, values[1:])]
    if not increments:
        return {
            "max_abs_delta": 0.0,
            "signed_delta_at_max": 0.0,
            "step_at_max": 0,
            "mean_abs_delta": 0.0,
            "rms_delta": 0.0,
            "total_variation": 0.0,
        }
    max_index = max(range(len(increments)), key=lambda index: abs(increments[index]))
    return {
        "max_abs_delta": abs(increments[max_index]),
        "signed_delta_at_max": increments[max_index],
        "step_offset_at_max": max_index + 1,
        "mean_abs_delta": sum(abs(value) for value in increments) / len(increments),
        "rms_delta": math.sqrt(sum(value * value for value in increments) / len(increments)),
        "total_variation": sum(abs(value) for value in increments),
    }


def analyze_rows(rows: list[dict], target_ages=(18.0, 45.0, 69.0)) -> dict:
    """Return a JSON-serializable comparison of dominant-height operators."""
    series = {name: _series(rows, field) for name, field in OPERATORS.items()}
    regularity = {}
    for name, values in series.items():
        metrics = _increment_metrics(values)
        offset = int(metrics.pop("step_offset_at_max", 0))
        metrics["step_at_max"] = rows[offset]["step_index"]
        metrics["age_at_max"] = rows[offset]["age"]
        regularity[name] = metrics

    target_values = {}
    for target in target_ages:
        row = min(rows, key=lambda item: abs(item["age"] - target))
        target_values[f"{target:g}"] = {
            "actual_age": row["age"],
            "step_index": row["step_index"],
            **{name: row[field] for name, field in OPERATORS.items()},
        }

    threshold_changes = []
    for previous, current in zip(rows, rows[1:]):
        if previous["threshold_dbh_index"] == current["threshold_dbh_index"]:
            continue
        threshold_changes.append(
            {
                "step_index": current["step_index"],
                "age": current["age"],
                "previous_index": previous["threshold_dbh_index"],
                "current_index": current["threshold_dbh_index"],
                "fraction_before": previous["fraction_used_from_threshold_class"],
                "fraction_after": current["fraction_used_from_threshold_class"],
                **{
                    f"delta_{name}": current[field] - previous[field]
                    for name, field in OPERATORS.items()
                },
            }
        )

    pairwise = {}
    for first, second in (("legacy", "proportional"), ("current", "proportional")):
        differences = [a - b for a, b in zip(series[first], series[second])]
        index = max(range(len(differences)), key=lambda i: abs(differences[i]))
        pairwise[f"{first}_minus_{second}"] = {
            "minimum": min(differences),
            "maximum": max(differences),
            "max_absolute": abs(differences[index]),
            "age_at_max_absolute": rows[index]["age"],
            "final": differences[-1],
        }

    return {
        "n_rows": len(rows),
        "target_values": target_values,
        "regularity": regularity,
        "pairwise_differences": pairwise,
        "threshold_changes": threshold_changes,
    }


def analyze_csv(csv_path: str | Path) -> dict:
    return analyze_rows(load_rows(csv_path))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_path", help="Comparison CSV produced by full_run.py")
    parser.add_argument("--output", help="Optional JSON output path")
    args = parser.parse_args()

    analysis = analyze_csv(args.csv_path)
    rendered = json.dumps(analysis, indent=2)
    if args.output:
        Path(args.output).write_text(rendered + "\n", encoding="utf-8")
        print(f"Analysis written to {Path(args.output).resolve()}")
    else:
        print(rendered)


if __name__ == "__main__":
    main()
