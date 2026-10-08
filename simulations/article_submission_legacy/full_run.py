# SPDX-License-Identifier: LGPL-3.0-or-later
"""Reproducible full-run pipeline for the manuscript-associated legacy scenario."""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
from pathlib import Path
from time import perf_counter

import numpy as np
from tqdm import tqdm

from pydynamicforest.diagnostics import (
    basal_area,
    legacy_mass,
    legacy_top_height,
    minimum_density,
    physical_dbh_grid,
    physical_height_grid,
    proportional_top_height,
    top_height,
    trapezoidal_mass,
)
from pydynamicforest.initial_conditions import build_initial_state
from pydynamicforest.solver import advance_one_step_sparse_legacy
from simulations.article_submission_legacy.config import ARTICLE_SUBMISSION_CONFIG
from simulations.article_submission_legacy.context import build_context
from simulations.article_submission_legacy.initial_condition import build_initial_condition
from simulations.article_submission_legacy.parameters import build_parameters


CSV_FIELDS = [
    "step_index",
    "time",
    "age",
    "trapezoidal_mass",
    "legacy_mass",
    "minimum_density",
    "top_height_current",
    "legacy_top_height",
    "proportional_top_height",
    "legacy_minus_proportional",
    "current_minus_proportional",
    "top_height_difference",
    "basal_area",
    "threshold_dbh_index",
    "threshold_dbh_physical",
    "stems_strictly_above_threshold",
    "stems_in_threshold_class",
    "fraction_used_from_threshold_class",
]


def _git_value(*args: str) -> str | None:
    try:
        return subprocess.check_output(
            ["git", *args], stderr=subprocess.DEVNULL, text=True
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def _tracked_worktree_clean() -> bool | None:
    try:
        unstaged = subprocess.run(["git", "diff", "--quiet"], check=False).returncode
        staged = subprocess.run(
            ["git", "diff", "--cached", "--quiet"], check=False
        ).returncode
        return unstaged == 0 and staged == 0
    except OSError:
        return None


def legacy_threshold_details(U, p, target_stems_per_ha: float = 100.0) -> dict:
    """Return the discrete DBH threshold diagnostics of the legacy selection."""

    if target_stems_per_ha <= 0.0:
        raise ValueError("target_stems_per_ha must be strictly positive.")

    grid = p.numerics.grid
    d_phys = physical_dbh_grid(p)
    class_stems = grid.dx * grid.dy * np.sum(U, axis=0)

    cumulative_above = 0.0
    for j in range(grid.ny - 1, -1, -1):
        stems_here = float(class_stems[j])
        if cumulative_above + stems_here >= target_stems_per_ha:
            required = max(0.0, target_stems_per_ha - cumulative_above)
            fraction = required / stems_here if stems_here > 0.0 else 0.0
            return {
                "threshold_dbh_index": j,
                "threshold_dbh_physical": float(d_phys[j]),
                "stems_strictly_above_threshold": cumulative_above,
                "stems_in_threshold_class": stems_here,
                "fraction_used_from_threshold_class": fraction,
            }
        cumulative_above += stems_here

    return {
        "threshold_dbh_index": None,
        "threshold_dbh_physical": None,
        "stems_strictly_above_threshold": cumulative_above,
        "stems_in_threshold_class": None,
        "fraction_used_from_threshold_class": None,
    }


def diagnostic_row(state, p) -> dict:
    """Compute historical and current diagnostics for one state."""

    current_height = top_height(state.U, p)
    historical_height = legacy_top_height(state.U, p)
    proportional_height = proportional_top_height(state.U, p)
    threshold = legacy_threshold_details(state.U, p)

    return {
        "step_index": state.step_index,
        "time": state.time,
        "age": state.age,
        "trapezoidal_mass": trapezoidal_mass(state.U, p),
        "legacy_mass": legacy_mass(state.U, p),
        "minimum_density": minimum_density(state.U),
        "top_height_current": current_height,
        "legacy_top_height": historical_height,
        "proportional_top_height": proportional_height,
        "legacy_minus_proportional": historical_height - proportional_height,
        "current_minus_proportional": current_height - proportional_height,
        "top_height_difference": historical_height - current_height,
        "basal_area": basal_area(state.U, p),
        **threshold,
    }


def _save_observation(state, p, output_dir: Path) -> Path:
    age_label = f"{state.age:.6f}".rstrip("0").rstrip(".").replace(".", "p")
    path = output_dir / f"state_age_{age_label}.npz"
    np.savez_compressed(
        path,
        U=state.U,
        x=p.numerics.grid.x,
        y=p.numerics.grid.y,
        time=np.array(state.time),
        age=np.array(state.age),
        step_index=np.array(state.step_index),
    )
    return path


def run_article_submission_legacy(
    output_dir: str | Path = "outputs/article_submission_legacy",
    max_steps: int | None = None,
    progress: bool = True,
) -> dict:
    """Run the sparse legacy scenario and write reproducible raw outputs."""

    x0 = build_initial_condition()
    p = build_parameters()
    c = build_context()
    state = build_initial_state(x0, p, c)

    requested_steps = p.numerics.time.n_steps
    n_steps = requested_steps if max_steps is None else min(max_steps, requested_steps)
    if n_steps < 0:
        raise ValueError("max_steps must be non-negative.")

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    csv_path = output_path / "time_series_legacy.csv"
    metadata_path = output_path / "metadata.json"
    config_path = output_path / "configuration.json"

    observation_ages = list(c.output.observation_ages)
    age_tolerance = 0.5 * p.numerics.time.dt
    saved_observations: dict[str, str] = {}

    start = perf_counter()
    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=CSV_FIELDS)
        writer.writeheader()

        def record(current_state) -> None:
            writer.writerow(diagnostic_row(current_state, p))
            for requested_age in observation_ages:
                key = f"{requested_age:g}"
                if key not in saved_observations and abs(current_state.age - requested_age) <= age_tolerance:
                    saved = _save_observation(current_state, p, output_path)
                    saved_observations[key] = saved.name

        record(state)
        iterator = range(n_steps)
        if progress:
            iterator = tqdm(iterator, total=n_steps, desc="Article legacy simulation")

        for _ in iterator:
            state = advance_one_step_sparse_legacy(state, p)
            record(state)

    elapsed = perf_counter() - start
    metadata = {
        "scenario": ARTICLE_SUBMISSION_CONFIG["name"],
        "description": ARTICLE_SUBMISSION_CONFIG["description"],
        "git_commit": _git_value("rev-parse", "HEAD"),
        "git_branch": _git_value("branch", "--show-current"),
        "tracked_worktree_clean_at_metadata_write": _tracked_worktree_clean(),
        "solver": "sparse legacy-equivalent",
        "n_steps_requested": requested_steps,
        "n_steps_run": n_steps,
        "dt": p.numerics.time.dt,
        "initial_age": c.initial_age,
        "final_age_reached": state.age,
        "elapsed_seconds": elapsed,
        "time_series_file": csv_path.name,
        "observation_files": saved_observations,
        "diagnostic_conventions": {
            "legacy_mass": "dx * dy * sum(U[1:, 1:])",
            "legacy_top_height": (
                "100 largest-DBH stems/ha; decreasing height within DBH ties; "
                "rectangular cell weights"
            ),
            "top_height_current": "current PyDynamicForest DBH-only stable sort",
            "proportional_top_height": (
                "100 largest-DBH stems/ha; uniform fraction of the threshold "
                "DBH class; arithmetic height mean"
            ),
        },
    }

    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    config_path.write_text(
        json.dumps(ARTICLE_SUBMISSION_CONFIG, indent=2), encoding="utf-8"
    )

    return {
        "final_state": state,
        "metadata": metadata,
        "time_series_path": csv_path,
        "metadata_path": metadata_path,
        "configuration_path": config_path,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the manuscript-associated legacy scenario."
    )
    parser.add_argument(
        "--output-dir",
        default="outputs/article_submission_legacy",
        help="Directory receiving CSV, metadata, configuration and state files.",
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=None,
        help="Optional short-run limit. Omit for all 10000 steps.",
    )
    parser.add_argument(
        "--no-progress",
        action="store_true",
        help="Disable the progress bar.",
    )
    args = parser.parse_args()

    result = run_article_submission_legacy(
        output_dir=args.output_dir,
        max_steps=args.max_steps,
        progress=not args.no_progress,
    )
    final_state = result["final_state"]
    print("Article-submission legacy simulation completed.")
    print(f"  steps: {result['metadata']['n_steps_run']}")
    print(f"  final age: {final_state.age:.6f}")
    print(f"  elapsed seconds: {result['metadata']['elapsed_seconds']:.3f}")
    print(f"  outputs: {Path(args.output_dir).resolve()}")


if __name__ == "__main__":
    main()
