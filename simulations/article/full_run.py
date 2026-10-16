# SPDX-License-Identifier: LGPL-3.0-or-later
"""Canonical full-run pipeline for the numerical simulation in the manuscript.

The trajectory is computed once. Cheap diagnostics are written at every time
step; complete observation operators and distributed states are evaluated only
at the 15 empirical inventory ages.
"""

from __future__ import annotations

import argparse
import csv
import json
import platform
import subprocess
import sys
from pathlib import Path
from time import perf_counter

import numpy as np
import scipy
from tqdm import tqdm

from pydynamicforest.initial_conditions import build_initial_state
from pydynamicforest.numerics import product_trapezoidal_weights
from pydynamicforest.observation_operators import (
    basal_area_consistent,
    continuous_dominant_height_details,
    height_dbh_correlation,
    joint_moment_summary,
    physical_dbh_nodes,
    physical_height_nodes,
    quadratic_mean_dbh,
    stand_density,
)
from pydynamicforest.solver import advance_one_step_sparse_legacy
from simulations.article.config import ARTICLE_CONFIG
from simulations.article.context import build_context
from simulations.article.initial_condition import build_initial_condition
from simulations.article.observations import (
    SOURCE_PROVENANCE,
    STATUS,
    UNITS,
    observation_ages,
    observation_at_age,
)
from simulations.article.parameters import build_parameters

TIME_SERIES_FIELDS = [
    "step_index", "time", "age", "stand_density", "minimum_density",
    "maximum_density",
]
COMPARISON_FIELDS = [
    "requested_age", "actual_simulated_age", "age_difference", "step_index",
    "observable", "simulated_value", "observed_value", "residual",
    "relative_residual", "unit", "observation_status",
]
DENSITY_FIELDS = [
    "requested_age", "actual_simulated_age", "height_m", "dbh_cm",
    "density_trees_ha_per_normalized_area", "quadrature_weight",
    "weighted_stems_ha",
]
PRIMARY_DENSITY_AGES = (18.0, 45.0, 69.0)


def _git_value(*args: str) -> str:
    try:
        return subprocess.check_output(
            ["git", *args], text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unavailable"


def _tracked_worktree_clean() -> bool | None:
    try:
        result = subprocess.run(
            ["git", "diff", "--quiet", "--ignore-submodules", "HEAD", "--"],
            check=False,
        )
        return result.returncode == 0
    except OSError:
        return None


def _cheap_row(state, p) -> dict:
    return {
        "step_index": state.step_index,
        "time": state.time,
        "age": state.age,
        "stand_density": stand_density(state.U, p),
        "minimum_density": float(np.min(state.U)),
        "maximum_density": float(np.max(state.U)),
    }


def summarize_state(state, p) -> dict[str, float]:
    moments = joint_moment_summary(state.U, p)
    dominant = continuous_dominant_height_details(state.U, p)
    Dm = 100.0 * moments["mean_dbh_m"]
    Dg = quadratic_mean_dbh(state.U, p, unit="cm")
    return {
        "N": stand_density(state.U, p),
        "G": basal_area_consistent(state.U, p),
        "Dm": Dm,
        "Dg": Dg,
        "sigma_D": float(np.sqrt(max(0.0, Dg**2 - Dm**2))),
        "Hm": moments["mean_height"],
        "H0": dominant["dominant_height"],
        "sigma_H": float(np.sqrt(max(0.0, moments["height_variance_m2"]))),
        "rho_HD": height_dbh_correlation(state.U, p),
        "H0_minus_Hm": dominant["dominant_height"] - moments["mean_height"],
        "dominant_threshold_dbh": 100.0 * dominant["threshold_dbh"],
        "dominant_selected_stems": dominant["selected_stems"],
    }


def _comparison_rows(requested_age: float, state, p) -> list[dict]:
    simulated = summarize_state(state, p)
    observed = observation_at_age(requested_age)
    rows = []
    for name, value in simulated.items():
        target = observed.get(name)
        residual = None if target is None else value - target
        relative = (
            None if target is None or target == 0.0 else residual / target
        )
        rows.append({
            "requested_age": requested_age,
            "actual_simulated_age": state.age,
            "age_difference": state.age - requested_age,
            "step_index": state.step_index,
            "observable": name,
            "simulated_value": value,
            "observed_value": "" if target is None else target,
            "residual": "" if residual is None else residual,
            "relative_residual": "" if relative is None else relative,
            "unit": UNITS.get(name, {
                "sigma_H": "m", "rho_HD": "dimensionless",
                "H0_minus_Hm": "m", "dominant_threshold_dbh": "cm",
                "dominant_selected_stems": "trees/ha",
            }.get(name, "")),
            "observation_status": (
                "missing_in_source" if target is None and name in observed
                else STATUS.get(name, "simulated_only")
            ),
        })
    return rows


def _write_state(path: Path, requested_age: float, state) -> None:
    np.savez_compressed(
        path,
        requested_age=float(requested_age),
        actual_age=float(state.age),
        time=float(state.time),
        step_index=int(state.step_index),
        U=np.asarray(state.U, dtype=float),
    )


def _density_rows(requested_age: float, state, p) -> list[dict]:
    weights = product_trapezoidal_weights(p)
    heights = physical_height_nodes(p)
    dbhs = physical_dbh_nodes(p, unit="cm")
    rows = []
    for i, height in enumerate(heights):
        for j, dbh in enumerate(dbhs):
            rows.append({
                "requested_age": requested_age,
                "actual_simulated_age": state.age,
                "height_m": float(height),
                "dbh_cm": float(dbh),
                "density_trees_ha_per_normalized_area": float(state.U[i, j]),
                "quadrature_weight": float(weights[i, j]),
                "weighted_stems_ha": float(weights[i, j] * state.U[i, j]),
            })
    return rows


def run_article_full(
    output_dir: str | Path,
    max_steps: int | None = None,
    progress: bool = True,
) -> dict:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    x0 = build_initial_condition()
    p = build_parameters()
    c = build_context()
    state = build_initial_state(x0, p, c)
    requested_steps = p.numerics.time.n_steps
    n_steps = requested_steps if max_steps is None else min(max_steps, requested_steps)
    if n_steps < 0:
        raise ValueError("max_steps must be non-negative.")

    targets = observation_ages()
    dt = p.numerics.time.dt
    target_steps = {
        age: int(round((age - c.initial_age) / dt)) for age in targets
    }
    target_steps = {
        age: step for age, step in target_steps.items() if 0 <= step <= n_steps
    }
    states_by_age = {}
    time_rows = []
    comparison_rows = []
    density_rows = []
    start = perf_counter()
    clean_at_start = _tracked_worktree_clean()

    iterator = range(n_steps + 1)
    if progress:
        iterator = tqdm(iterator, total=n_steps + 1, desc="article simulation")
    for step in iterator:
        time_rows.append(_cheap_row(state, p))
        for age, target_step in target_steps.items():
            if target_step == step:
                states_by_age[age] = state
        if step == n_steps:
            break
        state = advance_one_step_sparse_legacy(state, p)

    for age in targets:
        if age not in states_by_age:
            continue
        saved = states_by_age[age]
        label = str(int(age)) if float(age).is_integer() else str(age).replace(".", "p")
        _write_state(output / f"state_age_{label}.npz", age, saved)
        comparison_rows.extend(_comparison_rows(age, saved, p))
        if age in PRIMARY_DENSITY_AGES:
            density_rows.extend(_density_rows(age, saved, p))

    paths = {
        "time_series": output / "time_series.csv",
        "comparison": output / "observations_simulation.csv",
        "comparison_md": output / "observations_simulation.md",
        "densities": output / "joint_densities_primary_ages.csv",
        "configuration": output / "configuration.json",
        "metadata": output / "metadata.json",
        "reproducibility": output / "reproducibility.json",
    }
    with paths["time_series"].open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=TIME_SERIES_FIELDS)
        writer.writeheader(); writer.writerows(time_rows)
    with paths["comparison"].open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=COMPARISON_FIELDS)
        writer.writeheader(); writer.writerows(comparison_rows)
    with paths["densities"].open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=DENSITY_FIELDS)
        writer.writeheader(); writer.writerows(density_rows)
    paths["configuration"].write_text(json.dumps(ARTICLE_CONFIG, indent=2) + "\n", encoding="utf-8")

    elapsed = perf_counter() - start
    metadata = {
        "purpose": "canonical numerical simulation retained for the manuscript",
        "requested_steps": requested_steps,
        "steps_run": n_steps,
        "completed_full_horizon": n_steps == requested_steps,
        "elapsed_seconds": elapsed,
        "saved_observation_ages": sorted(states_by_age),
        "primary_density_ages": list(PRIMARY_DENSITY_AGES),
        "dominant_height_operator": "continuous upper-DBH-tail functional",
        "observation_source": SOURCE_PROVENANCE,
        "files": {name: path.name for name, path in paths.items()},
    }
    paths["metadata"].write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    reproducibility = {
        "git_branch": _git_value("branch", "--show-current"),
        "git_commit": _git_value("rev-parse", "HEAD"),
        "tracked_worktree_clean_at_start": clean_at_start,
        "tracked_worktree_clean_at_end": _tracked_worktree_clean(),
        "python_version": sys.version,
        "platform": platform.platform(),
        "numpy_version": np.__version__,
        "scipy_version": scipy.__version__,
        "command": "python -m simulations.article.full_run --output-dir outputs/article_simulation",
    }
    paths["reproducibility"].write_text(json.dumps(reproducibility, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Observations and simulation", "",
        "| Age | Observable | Simulated | Observed | Residual | Relative residual | Unit |",
        "|---:|:---|---:|---:|---:|---:|:---|",
    ]
    for row in comparison_rows:
        observed = row["observed_value"]
        residual = row["residual"]
        relative = row["relative_residual"]
        lines.append(
            f"| {row['requested_age']:g} | {row['observable']} | {row['simulated_value']:.8g} | "
            f"{'' if observed == '' else f'{observed:.8g}'} | "
            f"{'' if residual == '' else f'{residual:+.8g}'} | "
            f"{'' if relative == '' else f'{100.0 * relative:+.3f}%'} | {row['unit']} |"
        )
    paths["comparison_md"].write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"metadata": metadata, "reproducibility": reproducibility, "paths": paths}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default="outputs/article_simulation")
    parser.add_argument("--max-steps", type=int)
    parser.add_argument("--no-progress", action="store_true")
    args = parser.parse_args()
    result = run_article_full(args.output_dir, args.max_steps, not args.no_progress)
    print(f"steps: {result['metadata']['steps_run']}")
    print(f"elapsed_seconds: {result['metadata']['elapsed_seconds']:.3f}")
    for name, path in result["paths"].items():
        print(f"{name}: {path.resolve()}")


if __name__ == "__main__":
    main()
