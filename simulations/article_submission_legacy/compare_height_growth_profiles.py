# SPDX-License-Identifier: LGPL-3.0-or-later
"""Compare complete trajectories for theorem-compatible height profiles.

Q-7B-2 preserves the analysed status factor S[n] and modifies only the
continuous baseline height field according to

    C_h^(beta)(h) = c_h * (1 - h/H)^beta.

DBH growth, status, mortality, diffusion, boundaries, and time stepping remain
patrimonial. beta=1 reproduces the validated legacy trajectory.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np
from scipy.sparse.linalg import spsolve

from pydynamicforest.initial_conditions import build_initial_state
from pydynamicforest.model import evaluate_model_fields
from pydynamicforest.numerics import compute_derived_quantities
from pydynamicforest.observation_operators import (
    basal_area_consistent,
    continuous_dominant_height_details,
    height_dbh_correlation,
    height_variance,
    mean_dbh,
    mean_height,
    quadratic_mean_dbh,
    stand_density,
)
from pydynamicforest.solver import (
    advance_one_step_sparse_legacy,
    assemble_sparse_legacy_system,
    compute_transport_legacy,
    evaluate_model_fields_for_solver,
)
from pydynamicforest.types import State
from simulations.article_submission_legacy.context import build_context
from simulations.article_submission_legacy.initial_condition import build_initial_condition
from simulations.article_submission_legacy.parameters import build_parameters

BETAS = (1.0, 1.25, 1.5)
TARGET_AGES = (18.0, 45.0, 69.0)
TRAJECTORY_FIELDS = [
    "beta", "time", "age", "step_index", "stand_density", "basal_area_m2_ha",
    "mean_height_m", "continuous_top_height_m", "H0_minus_Hm_m",
    "height_sd_m", "mean_dbh_cm", "quadratic_mean_dbh_cm",
    "dbh_sd_cm", "height_dbh_correlation", "min_density", "max_density",
]
COMPARISON_FIELDS = [
    "target_age", "beta", "actual_age", "stand_density", "basal_area_m2_ha",
    "mean_height_m", "continuous_top_height_m", "H0_minus_Hm_m",
    "height_sd_m", "mean_dbh_cm", "quadratic_mean_dbh_cm", "dbh_sd_cm",
    "height_dbh_correlation", "delta_stand_density", "delta_basal_area_m2_ha",
    "delta_mean_height_m", "delta_continuous_top_height_m",
    "delta_H0_minus_Hm_m", "delta_height_sd_m", "delta_mean_dbh_cm",
    "delta_quadratic_mean_dbh_cm", "delta_dbh_sd_cm",
    "delta_height_dbh_correlation",
]


def height_profile_multiplier(p, beta: float) -> np.ndarray:
    """Return the factor converting the beta=1 field to exponent beta."""
    if not np.isfinite(beta) or beta <= 0.0:
        raise ValueError("beta must be a finite strictly positive number.")
    remaining = np.clip(1.0 - p.numerics.grid.x, 0.0, 1.0)
    if beta == 1.0:
        return np.ones_like(remaining)
    return remaining ** (beta - 1.0)


def modify_height_growth(fields, p, beta: float):
    """Copy model fields and modify only the height-growth component."""
    modified = {
        name: np.array(values, copy=True)
        for name, values in fields.items()
    }
    modified["height_growth"] *= height_profile_multiplier(p, beta)[:, None]
    return modified


def advance_one_step_height_profile(state: State, p, beta: float) -> State:
    """Advance one legacy sparse step with a modified baseline height profile."""
    derived = compute_derived_quantities(state, p)
    current = modify_height_growth(
        evaluate_model_fields_for_solver(state, p), p, beta
    )
    next_fields = evaluate_model_fields(p, state.time + p.numerics.time.dt)
    transport = compute_transport_legacy(state, p, derived, current)
    A, b = assemble_sparse_legacy_system(
        state, p, derived, next_fields, transport
    )
    U_next = np.asarray(spsolve(A, b), dtype=float).reshape(state.U.shape)
    dt = p.numerics.time.dt
    return State(
        time=state.time + dt,
        age=state.age + dt,
        U=U_next,
        step_index=state.step_index + 1,
    )


def summarize_state(state: State, p, beta: float) -> dict[str, float | int]:
    N = stand_density(state.U, p)
    Hm = mean_height(state.U, p)
    H0 = float(continuous_dominant_height_details(state.U, p)["dominant_height"])
    Dm = mean_dbh(state.U, p, unit="cm")
    Dg = quadratic_mean_dbh(state.U, p, unit="cm")
    variance_d = max(0.0, Dg**2 - Dm**2)
    return {
        "beta": beta, "time": state.time, "age": state.age,
        "step_index": state.step_index, "stand_density": N,
        "basal_area_m2_ha": basal_area_consistent(state.U, p),
        "mean_height_m": Hm, "continuous_top_height_m": H0,
        "H0_minus_Hm_m": H0 - Hm,
        "height_sd_m": float(np.sqrt(height_variance(state.U, p))),
        "mean_dbh_cm": Dm, "quadratic_mean_dbh_cm": Dg,
        "dbh_sd_cm": float(np.sqrt(variance_d)),
        "height_dbh_correlation": height_dbh_correlation(state.U, p),
        "min_density": float(np.min(state.U)),
        "max_density": float(np.max(state.U)),
    }


def run_trajectory(beta: float, p=None, context=None):
    """Run one complete trajectory and return every-step summaries and states."""
    if p is None:
        p = build_parameters()
    if context is None:
        context = build_context()
    state = build_initial_state(build_initial_condition(), p, context)
    rows = [summarize_state(state, p, beta)]
    states = [state]
    final_time = context.final_age - context.initial_age
    while state.time < final_time - 0.5 * p.numerics.time.dt:
        state = advance_one_step_height_profile(state, p, beta)
        rows.append(summarize_state(state, p, beta))
        states.append(state)
    return rows, states


def nearest_age_rows(rows, target_ages=TARGET_AGES):
    return [min(rows, key=lambda row: abs(float(row["age"]) - age)) for age in target_ages]


def build_comparison(trajectory_rows):
    selected = {beta: nearest_age_rows(rows) for beta, rows in trajectory_rows.items()}
    reference = {round(float(row["age"]), 8): row for row in selected[1.0]}
    output = []
    metric_names = [
        "stand_density", "basal_area_m2_ha", "mean_height_m",
        "continuous_top_height_m", "H0_minus_Hm_m", "height_sd_m",
        "mean_dbh_cm", "quadratic_mean_dbh_cm", "dbh_sd_cm",
        "height_dbh_correlation",
    ]
    for beta, rows in selected.items():
        for target_age, row in zip(TARGET_AGES, rows):
            ref = min(selected[1.0], key=lambda r: abs(float(r["age"]) - target_age))
            output.append({
                "target_age": target_age, "beta": beta,
                "actual_age": row["age"],
                **{name: row[name] for name in metric_names},
                **{f"delta_{name}": float(row[name]) - float(ref[name]) for name in metric_names},
            })
    return output


def patrimonial_regression(p=None, context=None):
    if p is None:
        p = build_parameters()
    if context is None:
        context = build_context()
    state = build_initial_state(build_initial_condition(), p, context)
    custom = advance_one_step_height_profile(state, p, 1.0)
    patrimonial = advance_one_step_sparse_legacy(state, p)
    difference = custom.U - patrimonial.U
    return {
        "max_abs_U_difference": float(np.max(np.abs(difference))),
        "l2_U_difference": float(np.linalg.norm(difference)),
    }


def run_sensitivity():
    p = build_parameters()
    context = build_context()
    trajectories = {}
    for beta in BETAS:
        rows, _ = run_trajectory(beta, p, context)
        trajectories[beta] = rows
    return trajectories, build_comparison(trajectories), patrimonial_regression(p, context)


def write_outputs(output_dir, trajectories, comparison, regression):
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    trajectory_csv = output / "height_profile_trajectories.csv"
    comparison_csv = output / "height_profile_age_comparison.csv"
    json_path = output / "height_profile_sensitivity.json"
    markdown_path = output / "height_profile_sensitivity.md"
    with trajectory_csv.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=TRAJECTORY_FIELDS)
        writer.writeheader()
        for beta in BETAS:
            writer.writerows(trajectories[beta])
    with comparison_csv.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=COMPARISON_FIELDS)
        writer.writeheader()
        writer.writerows(comparison)
    payload = {
        "scope": "complete trajectories for theorem-compatible baseline height profiles",
        "formula": "C_h^(beta)(h) = c_h (1 - h/H)^beta",
        "betas": list(BETAS),
        "unchanged_structure": "transport remains C_h^(beta)(h) S[n] n",
        "patrimonial_regression": regression,
        "comparison": comparison,
    }
    json_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Q-7B-2 height-profile sensitivity", "",
        "The analysed status factor S[n] is unchanged. Only the continuous baseline height profile is modified.", "",
        "| Age | Beta | N | G | Hm | H0 | H0-Hm | sd(H) | Dm | Dg | Corr(H,D) |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in comparison:
        lines.append(
            "| {target_age:g} | {beta:.2f} | {stand_density:.2f} | {basal_area_m2_ha:.3f} | "
            "{mean_height_m:.3f} | {continuous_top_height_m:.3f} | {H0_minus_Hm_m:.3f} | "
            "{height_sd_m:.3f} | {mean_dbh_cm:.3f} | {quadratic_mean_dbh_cm:.3f} | "
            "{height_dbh_correlation:.4f} |".format(**row)
        )
    lines.extend(["", "## Patrimonial regression", "", f"- Maximum absolute one-step U difference: `{regression['max_abs_U_difference']:.3e}`."])
    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"trajectory_csv": trajectory_csv, "comparison_csv": comparison_csv, "json": json_path, "markdown": markdown_path}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default="outputs/height_profile_sensitivity")
    args = parser.parse_args()
    files = write_outputs(args.output_dir, *run_sensitivity())
    for name, path in files.items():
        print(f"{name}: {path.resolve()}")


if __name__ == "__main__":
    main()
