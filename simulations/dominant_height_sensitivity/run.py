# SPDX-License-Identifier: LGPL-3.0-or-later
"""Isolated DBH-mesh sensitivity study for dominant-height operators.

The density is generated analytically on each grid. No dynamic simulation is
run, so the experiment isolates the discretization sensitivity of the
observation operators from the numerical evolution of the forest state.
"""

from __future__ import annotations

import argparse
import csv
import json
from copy import deepcopy
from pathlib import Path

import numpy as np

from pydynamicforest.diagnostics import (
    legacy_top_height,
    proportional_top_height,
    top_height,
)
from pydynamicforest.numerics import integrate_2d_trapezoidal
from simulations.article_submission_legacy.config import ARTICLE_SUBMISSION_CONFIG
from simulations.article_submission_legacy.parameters import build_parameters

DEFAULT_NY_VALUES = (20, 40, 80, 160)
REFERENCE_NY = 1280
FIXED_NX = 161


def build_parameters_for_grid(nx: int, ny: int):
    config = deepcopy(ARTICLE_SUBMISSION_CONFIG)
    config["grid"].update({"nx": nx, "ny": ny})
    return build_parameters(config)


def _normal_density(values, mean, standard_deviation):
    return np.exp(-0.5 * ((values - mean) / standard_deviation) ** 2)


def controlled_density(p, case: str, mass_target: float = 800.0) -> np.ndarray:
    """Evaluate and trapezoidally normalize a controlled analytical density."""
    grid = p.numerics.grid
    X, Y = np.meshgrid(grid.x, grid.y, indexing="ij")

    if case == "regular_height_dbh":
        # Smooth positive height-DBH association with moderate conditional spread.
        mean_height = 0.12 + 0.62 * Y
        raw = _normal_density(Y, 0.38, 0.15) * _normal_density(X, mean_height, 0.07)
    elif case == "dispersed_threshold":
        # A broad bimodal conditional height distribution makes arbitrary
        # within-class height tie-breaking particularly visible.
        dbh = _normal_density(Y, 0.42, 0.12)
        low = _normal_density(X, 0.30 + 0.28 * Y, 0.055)
        high = _normal_density(X, 0.58 + 0.22 * Y, 0.055)
        raw = dbh * (0.48 * low + 0.52 * high)
    else:
        raise ValueError(f"Unknown controlled-density case: {case}")

    integral = integrate_2d_trapezoidal(raw, grid.dx, grid.dy)
    if integral <= 0.0:
        raise ValueError("Controlled density has non-positive mass.")
    return raw * mass_target / integral


def evaluate_case(case: str, ny_values=DEFAULT_NY_VALUES, reference_ny=REFERENCE_NY):
    """Evaluate all operators and errors relative to a fine-grid reference."""
    reference_p = build_parameters_for_grid(FIXED_NX, reference_ny)
    reference_U = controlled_density(reference_p, case)
    reference_value = proportional_top_height(reference_U, reference_p)

    rows = []
    for ny in ny_values:
        p = build_parameters_for_grid(FIXED_NX, int(ny))
        U = controlled_density(p, case)
        values = {
            "legacy": legacy_top_height(U, p),
            "current": top_height(U, p),
            "proportional": proportional_top_height(U, p),
        }
        rows.append(
            {
                "case": case,
                "nx": FIXED_NX,
                "ny": int(ny),
                "dbh_step_physical": p.numerics.grid.dy * p.model.physical_scales.dbh_scale,
                "reference_ny": int(reference_ny),
                "reference_proportional": reference_value,
                **values,
                **{
                    f"absolute_error_{name}": abs(value - reference_value)
                    for name, value in values.items()
                },
            }
        )
    return rows


def run_study(output_dir: str | Path):
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    cases = ("regular_height_dbh", "dispersed_threshold")
    rows = [row for case in cases for row in evaluate_case(case)]

    csv_path = output_path / "dominant_height_mesh_sensitivity.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    summary = {
        "purpose": "isolated dominant-height operator sensitivity to DBH resolution",
        "fixed_nx": FIXED_NX,
        "ny_values": list(DEFAULT_NY_VALUES),
        "reference_ny": REFERENCE_NY,
        "cases": {},
    }
    for case in cases:
        case_rows = [row for row in rows if row["case"] == case]
        summary["cases"][case] = {
            "fine_grid_values": {
                name: case_rows[-1][name]
                for name in ("legacy", "current", "proportional")
            },
            "errors_by_ny": {
                str(row["ny"]): {
                    name: row[f"absolute_error_{name}"]
                    for name in ("legacy", "current", "proportional")
                }
                for row in case_rows
            },
        }

    json_path = output_path / "dominant_height_mesh_sensitivity.json"
    json_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return {"rows": rows, "csv_path": csv_path, "json_path": json_path}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        default="outputs/dominant_height_mesh_sensitivity",
    )
    args = parser.parse_args()
    result = run_study(args.output_dir)
    print(f"CSV: {result['csv_path'].resolve()}")
    print(f"JSON: {result['json_path'].resolve()}")


if __name__ == "__main__":
    main()
