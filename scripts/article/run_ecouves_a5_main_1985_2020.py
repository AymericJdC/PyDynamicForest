#!/usr/bin/env python3
"""Frozen article runner for the calibrated Ecouves A5 trajectory, 1985--2020.

Calibration scope:
- mortality.value = 0.0377 yr-1, fitted to stand density in 1992, 1998, 2016, 2020;
- dbh_growth.physical_rate = 0.0165 m yr-1, selected as a compromise on mean DBH,
  basal area and diameter dispersion after the mortality calibration.

All other dynamic parameters, the numerical scheme, grids and observation
operators are inherited unchanged from the article configuration.
"""
from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

import numpy as np
import scipy

MORTALITY_K = 0.0377
DBH_GROWTH_RATE = 0.0165
YEAR_TO_AGE = {1985: 37.0, 1992: 44.0, 1998: 50.0, 2016: 68.0, 2020: 72.0}
TARGET_YEARS = tuple(YEAR_TO_AGE)
HEIGHT_PROVIDER_1985 = "log-dbh-A1-A2-A5-1985"


def locate_root() -> Path:
    here = Path(__file__).resolve()
    for path in [Path.cwd(), *Path.cwd().parents, *here.parents]:
        if (path / "simulations/article/ecouves_a5").exists():
            return path.resolve()
    raise RuntimeError("cannot locate PyDynamicForest repository root")


ROOT = locate_root()
sys.path.insert(0, str(ROOT))

from pydynamicforest.initial_conditions import build_initial_state
from pydynamicforest.numerics import compute_derived_quantities
from pydynamicforest.observation_operators import (
    basal_area_consistent,
    continuous_dominant_height,
    height_dbh_correlation,
    height_variance,
    mean_dbh,
    mean_height,
    quadratic_mean_dbh,
    stand_density,
)
from pydynamicforest.solver import advance_one_step_sparse_legacy
from pydynamicforest.types import InitialCondition, OutputSpecification, SimulationContext, State
from simulations.article.config import ARTICLE_CONFIG
from simulations.article.parameters import build_parameters
from simulations.article.ecouves_a5.main_dynamic_trajectory import StandSummary


def calibrated_article_config() -> dict:
    config = copy.deepcopy(ARTICLE_CONFIG)
    config["model"]["mortality"]["value"] = MORTALITY_K
    config["model"]["dbh_growth"]["physical_rate"] = DBH_GROWTH_RATE
    return config


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def git_value(*args: str) -> str:
    p = subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True)
    return p.stdout.strip() if p.returncode == 0 else "unavailable"


def tracked_worktree_clean() -> bool | None:
    p = subprocess.run(
        ["git", "diff", "--quiet", "--ignore-submodules", "HEAD", "--"],
        cwd=ROOT, check=False,
    )
    return p.returncode == 0


def summarize(U, parameters) -> StandSummary:
    n = stand_density(U, parameters)
    dm = mean_dbh(U, parameters, unit="cm")
    dg = quadratic_mean_dbh(U, parameters, unit="cm")
    hm = mean_height(U, parameters)
    hq = float(np.sqrt(height_variance(U, parameters) + hm * hm))
    h0 = continuous_dominant_height(U, parameters)
    return StandSummary(
        n,
        basal_area_consistent(U, parameters),
        dm,
        dg,
        float(np.sqrt(max(0.0, dg * dg - dm * dm))),
        hm,
        hq,
        h0,
        height_dbh_correlation(U, parameters),
        h0 - hm,
    )


def load_initial(path: Path, parameters):
    with np.load(path, allow_pickle=False) as payload:
        U0 = np.array(payload["U0"], dtype=float, copy=True)
        year = int(payload["inventory_year"])
        age = float(payload["biological_age"])
    expected = (parameters.numerics.grid.nx, parameters.numerics.grid.ny)
    if U0.shape != expected:
        raise ValueError(f"invalid U0 shape {U0.shape}, expected {expected}")
    if year != 1985 or abs(age - 37.0) > 1e-12:
        raise ValueError(f"invalid initial provenance: year={year}, age={age}")
    if not np.all(np.isfinite(U0)) or np.min(U0) < 0:
        raise ValueError("U0 must be finite and non-negative")
    mass = float(stand_density(U0, parameters))
    x0 = InitialCondition(
        name="ecouves_a5_1985_empirical_log_dbh",
        initial_age=37.0,
        mass_target=mass,
        distribution_kind="precomputed_empirical_height_dbh",
        distribution_parameters={
            "inventory_year": 1985,
            "height_provider_id": HEIGHT_PROVIDER_1985,
            "height_reconstruction": "deterministic logarithmic height-DBH allometry",
            "residual_height_variability_simulated": False,
            "conversion": "conservative_bilinear_nodal_mass",
            "axis_order": "height_dbh",
        },
        source=str(path),
        description="Ecouves A5 1985 empirical initial state for the frozen article run.",
        U0=U0,
    )
    return x0, U0


def load_target(path: Path, year: int, parameters):
    with np.load(path, allow_pickle=False) as payload:
        U = np.array(payload["U0"], dtype=float, copy=True)
        stored_age = None
        for key in ("gis_age", "biological_age", "age"):
            if key in payload.files:
                stored_age = float(payload[key])
                break
    if U.shape != (parameters.numerics.grid.nx, parameters.numerics.grid.ny):
        raise ValueError(f"target {path} has invalid shape {U.shape}")
    if not np.all(np.isfinite(U)) or np.min(U) < 0:
        raise ValueError(f"target {path} is invalid")
    return U, stored_age


def nearest_target_steps(dt: float) -> dict[int, int]:
    start = YEAR_TO_AGE[1985]
    return {year: int(round((age - start) / dt)) for year, age in YEAR_TO_AGE.items()}


def completed_full_horizon(final_age: float, target_age: float, dt: float) -> bool:
    return float(final_age) >= float(target_age) - 0.5 * float(dt)


def write_csv(path: Path, rows) -> None:
    rows = list(rows)
    if not rows:
        raise ValueError(f"no rows for {path}")
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--initial-state", type=Path, required=True)
    parser.add_argument("--target-state-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--no-progress", action="store_true")
    args = parser.parse_args(argv)

    initial_path = args.initial_state.resolve()
    target_dir = args.target_state_dir.resolve()
    output = args.output_dir.resolve()
    if output.exists():
        raise FileExistsError(f"refusing existing output directory: {output}")
    output.mkdir(parents=True)

    config = calibrated_article_config()
    parameters = build_parameters(config)
    x0, U0 = load_initial(initial_path, parameters)
    context = SimulationContext(
        "ecouves_a5_frozen_article_1985_2020",
        37.0,
        72.0,
        OutputSpecification(observation_ages=list(YEAR_TO_AGE.values()), save_full_trajectory=False),
        description="Frozen article trajectory with calibrated K and c_phi.",
    )
    state = build_initial_state(x0, parameters, context)
    steps = nearest_target_steps(parameters.numerics.time.dt)
    final_step = steps[2020]
    if final_step > parameters.numerics.time.n_steps:
        raise ValueError("article time horizon is too short")

    targets = {1985: summarize(U0, parameters)}
    provenance = {1985: {"path": str(initial_path), "sha256": sha256(initial_path), "stored_age": 37.0}}
    for year in TARGET_YEARS[1:]:
        path = target_dir / f"ecouves_a5_native_initial_state_{year}.npz"
        if not path.is_file():
            raise FileNotFoundError(path)
        U, stored_age = load_target(path, year, parameters)
        targets[year] = summarize(U, parameters)
        provenance[year] = {"path": str(path), "sha256": sha256(path), "stored_age": stored_age, "age_used": YEAR_TO_AGE[year]}

    saved = {1985: State(state.time, state.age, state.U.copy(), state.step_index)}
    time_rows = []
    started_at = datetime.now(timezone.utc).isoformat()
    clean_start = tracked_worktree_clean()
    start = perf_counter()
    iterator = range(final_step + 1)
    if not args.no_progress:
        from tqdm import tqdm
        iterator = tqdm(iterator, total=final_step + 1, desc="Ecouves A5 frozen 1985--2020")
    for step in iterator:
        if step % 100 == 0 or step in steps.values():
            s = summarize(state.U, parameters)
            derived = compute_derived_quantities(state, parameters)
            time_rows.append({
                "step_index": state.step_index, "time": state.time, "age": state.age,
                **s.record(), "minimum_density": float(np.min(state.U)),
                "status_minimum": float(np.min(derived.status_field)),
                "status_maximum": float(np.max(derived.status_field)),
            })
        for year, target_step in steps.items():
            if step == target_step and year not in saved:
                saved[year] = State(state.time, state.age, state.U.copy(), state.step_index)
        if step == final_step:
            break
        state = advance_one_step_sparse_legacy(state, parameters)
    elapsed = perf_counter() - start

    comparisons = []
    initial_N = targets[1985].N
    for year in TARGET_YEARS:
        simulated = summarize(saved[year].U, parameters)
        target = targets[year]
        for metric in StandSummary.__dataclass_fields__:
            sv, tv = getattr(simulated, metric), getattr(target, metric)
            comparisons.append({
                "year": year, "requested_age": YEAR_TO_AGE[year],
                "actual_simulated_age": saved[year].age, "step_index": saved[year].step_index,
                "metric": metric, "simulated_value": sv,
                "reconstructed_target_value": tv, "residual": sv-tv,
                "relative_residual": (sv-tv)/tv if tv != 0 else None,
            })
        comparisons.append({
            "year": year, "requested_age": YEAR_TO_AGE[year],
            "actual_simulated_age": saved[year].age, "step_index": saved[year].step_index,
            "metric": "cumulative_stem_loss", "simulated_value": initial_N-simulated.N,
            "reconstructed_target_value": initial_N-target.N,
            "residual": target.N-simulated.N, "relative_residual": None,
        })

    valid = all(
        row["minimum_density"] >= -parameters.numerics.positivity_tolerance
        and row["status_minimum"] >= -1e-12 and row["status_maximum"] <= 1+1e-12
        for row in time_rows
    )
    if not valid:
        raise RuntimeError("trajectory failed numerical validity checks")

    write_csv(output / "ecouves_a5_frozen_1985_2020_time_series.csv", time_rows)
    write_csv(output / "ecouves_a5_frozen_1985_2020_comparison.csv", comparisons)
    for year, saved_state in saved.items():
        np.savez_compressed(
            output / f"ecouves_a5_frozen_state_{year}.npz",
            U=saved_state.U, year=year, requested_age=YEAR_TO_AGE[year],
            actual_age=saved_state.age, step_index=saved_state.step_index, time=saved_state.time,
        )

    completed = completed_full_horizon(state.age, 72.0, parameters.numerics.time.dt)
    metadata = {
        "purpose": "frozen calibrated article trajectory for Ecouves A5",
        "initial_year": 1985, "initial_age_biological": 37.0,
        "historical_article_age_label": 38.0,
        "final_year": 2020, "final_age_requested": 72.0,
        "final_age_actual": state.age, "completed_full_horizon": completed,
        "steps_run": state.step_index, "dt": parameters.numerics.time.dt,
        "started_at_utc": started_at, "elapsed_seconds": elapsed,
        "dynamic_parameters_recalibrated": True,
        "calibrated_parameters": ["mortality.value", "dbh_growth.physical_rate"],
        "mortality_coefficient_per_year": MORTALITY_K,
        "dbh_growth_physical_rate_m_per_year": DBH_GROWTH_RATE,
        "calibration_targets": {
            "mortality.value": "stand density in 1992, 1998, 2016 and 2020",
            "dbh_growth.physical_rate": "mean DBH in 1992, 1998, 2016 and 2020",
        },
        "calibration_criteria": {
            "mortality.value": "sum of squared log-density residuals",
            "dbh_growth.physical_rate": "sequential compromise after log-mean-DBH screen, retaining basal-area and dispersion diagnostics",
        },
        "parameters_retained_unchanged": ["height_growth", "diffusion", "status allocation", "H", "Phi"],
        "height_provider_1985": HEIGHT_PROVIDER_1985,
        "height_values_1985_are_measured": False,
        "residual_height_variability_1985_simulated": False,
        "target_years": list(TARGET_YEARS),
        "target_age_convention": "biological ages; civil years are primary identifiers",
        "numerical_validity": valid,
        "initial_state_path": str(initial_path), "initial_state_sha256": sha256(initial_path),
        "target_state_provenance": provenance,
    }
    (output / "ecouves_a5_frozen_1985_2020_metadata.json").write_text(json.dumps(metadata, indent=2)+"\n", encoding="utf-8")
    (output / "configuration.json").write_text(json.dumps({
        "scenario": "ecouves_a5_frozen_article_1985_2020",
        "initial_state_path": str(initial_path), "target_state_dir": str(target_dir),
        "output_dir": str(output), "initial_year": 1985, "final_year": 2020,
        "initial_age": 37.0, "final_age_target": 72.0,
        "dt": parameters.numerics.time.dt, "target_years": list(TARGET_YEARS),
        "target_ages": YEAR_TO_AGE, "mortality_coefficient_per_year": MORTALITY_K,
        "dbh_growth_physical_rate_m_per_year": DBH_GROWTH_RATE,
    }, indent=2)+"\n", encoding="utf-8")
    (output / "reproducibility.json").write_text(json.dumps({
        "git_branch": git_value("branch", "--show-current"),
        "git_commit": git_value("rev-parse", "HEAD"),
        "tracked_worktree_clean_at_start": clean_start,
        "tracked_worktree_clean_at_end": tracked_worktree_clean(),
        "python_version": sys.version, "platform": platform.platform(),
        "numpy_version": np.__version__, "scipy_version": scipy.__version__,
        "command": " ".join(sys.argv), "started_at_utc": started_at,
        "elapsed_seconds": elapsed, "runner_path": str(Path(__file__).resolve()),
        "runner_sha256": sha256(Path(__file__).resolve()),
        "initial_state_sha256": sha256(initial_path),
    }, indent=2)+"\n", encoding="utf-8")

    lines = [
        "# Frozen calibrated Ecouves A5 trajectory, 1985--2020", "",
        f"- K: {MORTALITY_K} yr-1;", f"- c_phi: {DBH_GROWTH_RATE} m yr-1;",
        "- c_h, diffusion, status allocation, H and Phi unchanged;",
        f"- completed: {completed};", f"- numerical validity: {valid};", "",
        "| Year | Age | Metric | Simulation | Reconstructed target | Relative residual |",
        "|---:|---:|:---|---:|---:|---:|",
    ]
    for row in comparisons:
        if row["metric"] == "cumulative_stem_loss":
            continue
        rr = row["relative_residual"]
        lines.append(f"| {row['year']} | {row['requested_age']:g} | {row['metric']} | {row['simulated_value']:.8g} | {row['reconstructed_target_value']:.8g} | {100*rr:+.3f}% |")
    (output / "ecouves_a5_frozen_1985_2020_report.md").write_text("\n".join(lines)+"\n", encoding="utf-8")
    print(f"[OK] outputs written to {output}")
    print(f"[VERDICT] completed={completed} valid={valid} K={MORTALITY_K} cphi={DBH_GROWTH_RATE} steps={state.step_index} final_age={state.age:.12f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
