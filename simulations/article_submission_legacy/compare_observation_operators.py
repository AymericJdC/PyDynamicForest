# SPDX-License-Identifier: LGPL-3.0-or-later
"""Compare historical and quadrature-consistent operators on saved states."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np

from pydynamicforest.diagnostics import (
    legacy_mass,
    legacy_top_height,
    proportional_top_height,
    top_height,
)
from pydynamicforest.observation_operators import (
    basal_area_consistent,
    continuous_dominant_height_details,
    mean_height,
    quadratic_mean_dbh,
    stand_density,
)
from simulations.article_submission_legacy.parameters import build_parameters


OBSERVATIONS = {
    18: {"N": 1924.34, "H0": 11.66, "G": 21.61, "Dg": 11.69, "Hm": 9.61},
    45: {"N": 1143.09, "H0": 31.61, "G": 66.32, "Dg": 26.10, "Hm": 28.23},
    69: {"N": 682.57, "H0": 43.14, "G": 89.56, "Dg": 39.45, "Hm": 38.97},
}

STATE_FILES = {
    18: "state_age_18.npz",
    45: "state_age_44p9994.npz",
    69: "state_age_69.npz",
}

CSV_FIELDS = [
    "target_age",
    "actual_age",
    "step_index",
    "stand_density",
    "legacy_mass",
    "mean_height",
    "quadratic_mean_dbh_cm",
    "basal_area_consistent",
    "basal_area_identity_residual",
    "legacy_top_height",
    "current_top_height",
    "proportional_top_height",
    "continuous_top_height",
    "continuous_threshold_dbh_cm",
    "continuous_selected_stems",
    "continuous_total_stems",
    "continuous_threshold_interval_index",
    "observed_N",
    "observed_H0",
    "observed_G",
    "observed_Dg_cm",
    "observed_Hm",
    "residual_N",
    "residual_H0_continuous",
    "residual_G",
    "residual_Dg_cm",
    "residual_Hm",
]


def load_saved_state(path: str | Path) -> dict:
    """Load one compressed state and return plain arrays and scalar metadata."""

    with np.load(Path(path)) as saved:
        required = {"U", "age", "step_index"}
        missing = required.difference(saved.files)
        if missing:
            raise ValueError(f"Missing state fields in {path}: {sorted(missing)}")
        return {
            "U": np.array(saved["U"], dtype=float),
            "age": float(saved["age"]),
            "step_index": int(saved["step_index"]),
        }


def compare_state(U, p, target_age: int, actual_age: float, step_index: int) -> dict:
    """Compute the complete observation-operator comparison for one state."""

    observed = OBSERVATIONS[target_age]
    density = stand_density(U, p)
    mean_h = mean_height(U, p)
    dg_cm = quadratic_mean_dbh(U, p, unit="cm")
    basal = basal_area_consistent(U, p)
    continuous = continuous_dominant_height_details(U, p)

    identity_value = 0.25 * np.pi * density * (dg_cm / 100.0) ** 2

    return {
        "target_age": target_age,
        "actual_age": actual_age,
        "step_index": step_index,
        "stand_density": density,
        "legacy_mass": legacy_mass(U, p),
        "mean_height": mean_h,
        "quadratic_mean_dbh_cm": dg_cm,
        "basal_area_consistent": basal,
        "basal_area_identity_residual": basal - identity_value,
        "legacy_top_height": legacy_top_height(U, p),
        "current_top_height": top_height(U, p),
        "proportional_top_height": proportional_top_height(U, p),
        "continuous_top_height": continuous["dominant_height"],
        "continuous_threshold_dbh_cm": 100.0 * continuous["threshold_dbh"],
        "continuous_selected_stems": continuous["selected_stems"],
        "continuous_total_stems": continuous["total_stems"],
        "continuous_threshold_interval_index": continuous["threshold_interval_index"],
        "observed_N": observed["N"],
        "observed_H0": observed["H0"],
        "observed_G": observed["G"],
        "observed_Dg_cm": observed["Dg"],
        "observed_Hm": observed["Hm"],
        "residual_N": density - observed["N"],
        "residual_H0_continuous": continuous["dominant_height"] - observed["H0"],
        "residual_G": basal - observed["G"],
        "residual_Dg_cm": dg_cm - observed["Dg"],
        "residual_Hm": mean_h - observed["Hm"],
    }


def compare_saved_states(
    input_dir: str | Path,
    output_dir: str | Path,
) -> dict:
    """Compare observation operators at ages 18, 45, and 69 years."""

    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    p = build_parameters()

    rows = []
    for target_age, filename in STATE_FILES.items():
        state_path = input_path / filename
        if not state_path.is_file():
            raise FileNotFoundError(f"Required saved state not found: {state_path}")
        state = load_saved_state(state_path)
        rows.append(
            compare_state(
                state["U"],
                p,
                target_age=target_age,
                actual_age=state["age"],
                step_index=state["step_index"],
            )
        )

    csv_path = output_path / "observation_operator_comparison.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    payload = {
        "purpose": "compare historical and quadrature-consistent observation operators",
        "input_directory": str(input_path),
        "quadrature": "tensor-product trapezoidal weights in normalized coordinates",
        "continuous_top_height": (
            "piecewise-linear interpolation of DBH marginal and height-moment "
            "densities in physical DBH"
        ),
        "rows": rows,
    }
    json_path = output_path / "observation_operator_comparison.json"
    json_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    return {"rows": rows, "csv_path": csv_path, "json_path": json_path}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input-dir",
        default="outputs/dominant_height_comparison",
        help="Directory containing the saved states at ages 18, 45, and 69.",
    )
    parser.add_argument(
        "--output-dir",
        default="outputs/observation_operator_comparison",
    )
    args = parser.parse_args()

    result = compare_saved_states(args.input_dir, args.output_dir)
    print(f"CSV: {result['csv_path'].resolve()}")
    print(f"JSON: {result['json_path'].resolve()}")


if __name__ == "__main__":
    main()
