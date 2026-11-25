# SPDX-License-Identifier: LGPL-3.0-or-later
"""Rebuild observation-comparison outputs from saved canonical states.

This post-processing command never advances the numerical model. It is intended
for observation-operator or table changes that do not require rerunning the
10,000-step trajectory.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import numpy as np

from pydynamicforest.types import State
from simulations.article.full_run import COMPARISON_FIELDS, _comparison_rows
from simulations.article.observations import observation_ages
from simulations.article.parameters import build_parameters


def _state_label(age: float) -> str:
    return str(int(age)) if float(age).is_integer() else str(age).replace(".", "p")


def load_saved_state(output_dir: str | Path, requested_age: float) -> State:
    path = Path(output_dir) / f"state_age_{_state_label(requested_age)}.npz"
    if not path.is_file():
        raise FileNotFoundError(f"Saved state not found: {path}")
    with np.load(path) as payload:
        stored_requested_age = float(payload["requested_age"])
        if stored_requested_age != float(requested_age):
            raise ValueError(
                f"Stored requested age {stored_requested_age} does not match {requested_age}."
            )
        return State(
            time=float(payload["time"]),
            age=float(payload["actual_age"]),
            U=np.array(payload["U"], dtype=float, copy=True),
            step_index=int(payload["step_index"]),
        )


def _write_markdown(path: Path, rows: list[dict]) -> None:
    lines = [
        "# Observations and simulation", "",
        "| Age | Observable | Simulated | Observed | Residual | Relative residual | Unit |",
        "|---:|:---|---:|---:|---:|---:|:---|",
    ]
    for row in rows:
        observed = row["observed_value"]
        residual = row["residual"]
        relative = row["relative_residual"]
        lines.append(
            f"| {row['requested_age']:g} | {row['observable']} | {row['simulated_value']:.8g} | "
            f"{'' if observed == '' else f'{observed:.8g}'} | "
            f"{'' if residual == '' else f'{residual:+.8g}'} | "
            f"{'' if relative == '' else f'{100.0 * relative:+.3f}%'} | {row['unit']} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def rebuild_comparison(
    output_dir: str | Path,
    ages=None,
) -> dict[str, Path]:
    output = Path(output_dir)
    p = build_parameters()
    requested_ages = observation_ages() if ages is None else tuple(ages)
    rows = []
    for age in requested_ages:
        rows.extend(_comparison_rows(age, load_saved_state(output, age), p))
    csv_path = output / "observations_simulation.csv"
    markdown_path = output / "observations_simulation.md"
    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=COMPARISON_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    _write_markdown(markdown_path, rows)
    return {"comparison": csv_path, "comparison_md": markdown_path}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default="outputs/article_simulation")
    args = parser.parse_args()
    for name, path in rebuild_comparison(args.output_dir).items():
        print(f"{name}: {path.resolve()}")


if __name__ == "__main__":
    main()
