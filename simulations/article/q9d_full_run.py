# SPDX-License-Identifier: LGPL-3.0-or-later
"""Canonical output pipeline for one Q-9D copula scenario."""

from __future__ import annotations

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
from pydynamicforest.solver import advance_one_step_sparse_legacy
from simulations.article.context import build_context
from simulations.article.full_run import (
    COMPARISON_FIELDS,
    DENSITY_FIELDS,
    TIME_SERIES_FIELDS,
    _cheap_row,
    _comparison_rows,
    _density_rows,
    _write_state,
)
from simulations.article.parameters import build_parameters
from simulations.article.scenarios import (
    Q9DScenario,
    load_scenario_initial_condition,
)


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


def _write_csv(path: Path, fields: list[str], rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def run_q9d_scenario(
    scenario: Q9DScenario,
    output_root: str | Path = "outputs/article_scenarios",
    *,
    max_steps: int | None = None,
    progress: bool = True,
    overwrite: bool = False,
) -> dict:
    """Run one Q-9D scenario and write isolated reproducibility outputs."""
    output = Path(output_root) / scenario.output_relative_path
    if output.exists() and any(output.iterdir()) and not overwrite:
        raise FileExistsError(
            f"Refusing to overwrite non-empty scenario directory: {output}"
        )
    output.mkdir(parents=True, exist_ok=True)

    p = build_parameters(scenario.config)
    c = build_context(scenario.config)
    x0 = load_scenario_initial_condition(scenario)
    state = build_initial_state(x0, p, c)

    requested_steps = p.numerics.time.n_steps
    n_steps = requested_steps if max_steps is None else min(max_steps, requested_steps)
    if n_steps < 0:
        raise ValueError("max_steps must be non-negative.")

    target_steps = {
        age: int(round((age - c.initial_age) / p.numerics.time.dt))
        for age in scenario.comparison_ages
    }
    target_steps = {
        age: step for age, step in target_steps.items() if 0 <= step <= n_steps
    }
    primary_density_ages = {
        scenario.initial_age,
        scenario.final_age,
    }
    states_by_age = {}
    time_rows: list[dict] = []
    comparison_rows: list[dict] = []
    density_rows: list[dict] = []

    start = perf_counter()
    clean_at_start = _tracked_worktree_clean()
    iterator = range(n_steps + 1)
    if progress:
        iterator = tqdm(iterator, total=n_steps + 1, desc=scenario.name)

    for step in iterator:
        time_rows.append(_cheap_row(state, p))
        for age, target_step in target_steps.items():
            if target_step == step:
                states_by_age[age] = state
        if step == n_steps:
            break
        state = advance_one_step_sparse_legacy(state, p)

    for age in scenario.comparison_ages:
        if age not in states_by_age:
            continue
        saved = states_by_age[age]
        label = str(int(age)) if float(age).is_integer() else str(age).replace(".", "p")
        _write_state(output / f"state_age_{label}.npz", age, saved)
        comparison_rows.extend(_comparison_rows(age, saved, p))
        if age in primary_density_ages:
            density_rows.extend(_density_rows(age, saved, p))

    paths = {
        "time_series": output / "time_series.csv",
        "comparison": output / "observations_simulation.csv",
        "densities": output / "joint_densities_primary_ages.csv",
        "configuration": output / "configuration.json",
        "metadata": output / "metadata.json",
        "reproducibility": output / "reproducibility.json",
        "initial_state_manifest": output / "initial_state_manifest.json",
    }
    _write_csv(paths["time_series"], TIME_SERIES_FIELDS, time_rows)
    _write_csv(paths["comparison"], COMPARISON_FIELDS, comparison_rows)
    _write_csv(paths["densities"], DENSITY_FIELDS, density_rows)
    paths["configuration"].write_text(
        json.dumps(scenario.config, indent=2) + "\n", encoding="utf-8"
    )

    elapsed = perf_counter() - start
    completed = n_steps == requested_steps
    metadata = {
        "scenario": scenario.name,
        "domain": scenario.domain,
        "requested_rho": scenario.requested_rho,
        "initial_age": scenario.initial_age,
        "final_age_target": scenario.final_age,
        "final_age_reached": state.age,
        "requested_steps": requested_steps,
        "steps_run": n_steps,
        "completed_full_horizon": completed,
        "historical_dt": scenario.config["q9d"]["historical_dt"],
        "effective_dt": p.numerics.time.dt,
        "dynamic_parameters_recalibrated": False,
        "saved_observation_ages": sorted(states_by_age),
        "elapsed_seconds": elapsed,
        "initial_state_source": str(scenario.initial_state_path),
        "initial_state_key": scenario.initial_state_key,
        "files": {name: path.name for name, path in paths.items()},
    }
    paths["metadata"].write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
    )
    initial_manifest = {
        "name": x0.name,
        "initial_age": x0.initial_age,
        "mass_target": x0.mass_target,
        "distribution_kind": x0.distribution_kind,
        "distribution_parameters": x0.distribution_parameters,
        "source": x0.source,
        "description": x0.description,
        "shape": list(x0.U0.shape),
        "minimum_density": float(np.min(x0.U0)),
        "maximum_density": float(np.max(x0.U0)),
        "finite": bool(np.all(np.isfinite(x0.U0))),
    }
    paths["initial_state_manifest"].write_text(
        json.dumps(initial_manifest, indent=2) + "\n", encoding="utf-8"
    )
    reproducibility = {
        "git_branch": _git_value("branch", "--show-current"),
        "git_commit": _git_value("rev-parse", "HEAD"),
        "tracked_worktree_clean_at_start": clean_at_start,
        "tracked_worktree_clean_at_end": _tracked_worktree_clean(),
        "python_version": sys.version,
        "platform": platform.platform(),
        "numpy_version": np.__version__,
        "scipy_version": scipy.__version__,
        "command": (
            "python -m simulations.article.run_q9d_scenarios "
            f"--scenario {scenario.name}"
        ),
    }
    paths["reproducibility"].write_text(
        json.dumps(reproducibility, indent=2) + "\n", encoding="utf-8"
    )
    return {
        "scenario": scenario,
        "final_state": state,
        "metadata": metadata,
        "paths": paths,
    }
