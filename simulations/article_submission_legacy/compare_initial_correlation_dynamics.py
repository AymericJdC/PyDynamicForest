# SPDX-License-Identifier: LGPL-3.0-or-later
"""Compare patrimonial and correlated-initial-state trajectories.

The patrimonial trajectory is read from an existing clean full-run output. A
single experimental trajectory is generated with the same solver and parameters
but a correlated initial joint density. The patrimonial scenario is not changed.
"""

from __future__ import annotations

import argparse
import csv
import json
from contextlib import contextmanager
from dataclasses import replace
from pathlib import Path

import numpy as np

from pydynamicforest.numerics import product_trapezoidal_weights
from pydynamicforest.observation_operators import (
    physical_dbh_nodes,
    physical_height_nodes,
    stand_density,
)
from simulations.article_submission_legacy import full_run
from simulations.article_submission_legacy.initial_correlation_sensitivity import (
    build_correlated_initial_density,
)
from simulations.article_submission_legacy.parameters import build_parameters


DEFAULT_RHO = 0.8490113967
COMMON_FIELDS = (
    "stand_density",
    "basal_area",
    "quadratic_mean_dbh_cm",
    "mean_height",
    "continuous_top_height",
    "continuous_threshold_dbh_cm",
)
COMPARISON_FIELDS = ["step_index", "time", "age"]
for field in COMMON_FIELDS:
    COMPARISON_FIELDS.extend(
        [f"patrimonial_{field}", f"correlated_{field}", f"delta_{field}"]
    )
COMPARISON_FIELDS.extend(
    [
        "patrimonial_H0_minus_Hm",
        "correlated_H0_minus_Hm",
        "delta_H0_minus_Hm",
    ]
)

STATE_FILES = {
    18: "state_age_18.npz",
    45: "state_age_44p9994.npz",
    69: "state_age_69.npz",
}
STATE_SUMMARY_FIELDS = [
    "target_age",
    "scenario",
    "actual_age",
    "step_index",
    "mean_dbh_cm",
    "dbh_standard_deviation_cm",
    "height_dbh_correlation",
]


@contextmanager
def _correlated_initial_state_patch(rho: float):
    """Temporarily replace only the initial joint density used by full_run."""

    original_builder = full_run.build_initial_state

    def build_correlated_state(x0, p, c):
        state = original_builder(x0, p, c)
        correlated_U = build_correlated_initial_density(rho, p)
        return replace(state, U=correlated_U)

    full_run.build_initial_state = build_correlated_state
    try:
        yield
    finally:
        full_run.build_initial_state = original_builder


def run_correlated_trajectory(
    output_dir: str | Path,
    rho: float = DEFAULT_RHO,
    max_steps: int | None = None,
    progress: bool = True,
) -> dict:
    """Run the unchanged patrimonial dynamics from a correlated initial state."""

    output_path = Path(output_dir)
    with _correlated_initial_state_patch(rho):
        result = full_run.run_article_submission_legacy(
            output_dir=output_path,
            max_steps=max_steps,
            progress=progress,
        )

    metadata_path = output_path / "metadata.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata["experiment"] = {
        "name": "initial height-DBH correlation dynamic comparison",
        "scenario_status": "experimental initial state; patrimonial dynamics unchanged",
        "rho_requested": float(rho),
        "initial_state_builder": "correlated bivariate Gaussian from Q-6A",
    }
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    return result


def _read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def compare_trajectories(
    patrimonial_csv: str | Path,
    correlated_csv: str | Path,
    output_csv: str | Path,
) -> Path:
    """Write aligned full-trajectory differences for common diagnostics."""

    patrimonial = _read_csv(patrimonial_csv)
    correlated = _read_csv(correlated_csv)
    if len(patrimonial) != len(correlated):
        raise ValueError("Patrimonial and correlated trajectories have different lengths.")

    rows = []
    for base, experiment in zip(patrimonial, correlated):
        if base["step_index"] != experiment["step_index"]:
            raise ValueError("Trajectory step indices are not aligned.")
        row = {
            "step_index": int(base["step_index"]),
            "time": float(base["time"]),
            "age": float(base["age"]),
        }
        for field in COMMON_FIELDS:
            base_value = float(base[field])
            experiment_value = float(experiment[field])
            row[f"patrimonial_{field}"] = base_value
            row[f"correlated_{field}"] = experiment_value
            row[f"delta_{field}"] = experiment_value - base_value

        base_gap = float(base["continuous_top_height"]) - float(base["mean_height"])
        experiment_gap = float(experiment["continuous_top_height"]) - float(
            experiment["mean_height"]
        )
        row["patrimonial_H0_minus_Hm"] = base_gap
        row["correlated_H0_minus_Hm"] = experiment_gap
        row["delta_H0_minus_Hm"] = experiment_gap - base_gap
        rows.append(row)

    output_path = Path(output_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=COMPARISON_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return output_path


def _state_joint_summary(path: str | Path, scenario: str, target_age: int) -> dict:
    p = build_parameters()
    with np.load(Path(path)) as saved:
        U = np.array(saved["U"], dtype=float)
        actual_age = float(saved["age"])
        step_index = int(saved["step_index"])

    weights = product_trapezoidal_weights(p)
    total = stand_density(U, p)
    height = physical_height_nodes(p)[:, None]
    dbh = physical_dbh_nodes(p, unit="m")[None, :]
    mean_h = float(np.sum(weights * height * U) / total)
    mean_d = float(np.sum(weights * dbh * U) / total)
    centered_h = height - mean_h
    centered_d = dbh - mean_d
    var_h = float(np.sum(weights * centered_h**2 * U) / total)
    var_d = float(np.sum(weights * centered_d**2 * U) / total)
    covariance = float(np.sum(weights * centered_h * centered_d * U) / total)
    denominator = np.sqrt(var_h * var_d)
    correlation = float("nan") if denominator <= 0.0 else covariance / denominator

    return {
        "target_age": target_age,
        "scenario": scenario,
        "actual_age": actual_age,
        "step_index": step_index,
        "mean_dbh_cm": 100.0 * mean_d,
        "dbh_standard_deviation_cm": 100.0 * np.sqrt(var_d),
        "height_dbh_correlation": correlation,
    }


def write_state_summary(
    patrimonial_dir: str | Path,
    correlated_dir: str | Path,
    output_csv: str | Path,
) -> Path:
    """Compare Dm, sigma_D, and correlation at ages 18, 45, and 69."""

    rows = []
    for age, filename in STATE_FILES.items():
        rows.append(
            _state_joint_summary(Path(patrimonial_dir) / filename, "patrimonial", age)
        )
        rows.append(
            _state_joint_summary(Path(correlated_dir) / filename, "correlated", age)
        )

    output_path = Path(output_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=STATE_SUMMARY_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return output_path


def run_comparison(
    patrimonial_dir: str | Path,
    correlated_dir: str | Path,
    comparison_dir: str | Path,
    rho: float = DEFAULT_RHO,
    max_steps: int | None = None,
    progress: bool = True,
) -> dict:
    """Run the correlated experiment and compare it with saved patrimonial output."""

    patrimonial_path = Path(patrimonial_dir)
    correlated_path = Path(correlated_dir)
    comparison_path = Path(comparison_dir)
    patrimonial_csv = patrimonial_path / "time_series_legacy.csv"
    if not patrimonial_csv.is_file():
        raise FileNotFoundError(f"Patrimonial trajectory not found: {patrimonial_csv}")

    run_correlated_trajectory(correlated_path, rho, max_steps, progress)
    trajectory_csv = compare_trajectories(
        patrimonial_csv,
        correlated_path / "time_series_legacy.csv",
        comparison_path / "trajectory_comparison.csv",
    )

    state_csv = None
    if max_steps is None:
        state_csv = write_state_summary(
            patrimonial_path,
            correlated_path,
            comparison_path / "state_joint_structure_comparison.csv",
        )

    metadata = {
        "purpose": "Q-6B dynamic comparison of patrimonial and correlated initial states",
        "patrimonial_directory": str(patrimonial_path),
        "correlated_directory": str(correlated_path),
        "rho_requested": float(rho),
        "patrimonial_dynamics_changed": False,
        "trajectory_comparison_csv": str(trajectory_csv),
        "state_joint_structure_comparison_csv": None if state_csv is None else str(state_csv),
    }
    metadata_path = comparison_path / "comparison_metadata.json"
    comparison_path.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    return {
        "trajectory_csv": trajectory_csv,
        "state_csv": state_csv,
        "metadata_path": metadata_path,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--patrimonial-dir",
        default="outputs/observation_quadrature_full",
    )
    parser.add_argument(
        "--correlated-dir",
        default="outputs/initial_correlation_dynamic_rho0849",
    )
    parser.add_argument(
        "--comparison-dir",
        default="outputs/initial_correlation_dynamic_comparison",
    )
    parser.add_argument("--rho", type=float, default=DEFAULT_RHO)
    parser.add_argument("--max-steps", type=int, default=None)
    parser.add_argument("--no-progress", action="store_true")
    args = parser.parse_args()

    result = run_comparison(
        patrimonial_dir=args.patrimonial_dir,
        correlated_dir=args.correlated_dir,
        comparison_dir=args.comparison_dir,
        rho=args.rho,
        max_steps=args.max_steps,
        progress=not args.no_progress,
    )
    print(f"Trajectory comparison: {result['trajectory_csv'].resolve()}")
    if result["state_csv"] is not None:
        print(f"State comparison: {result['state_csv'].resolve()}")
    print(f"Metadata: {result['metadata_path'].resolve()}")


if __name__ == "__main__":
    main()
