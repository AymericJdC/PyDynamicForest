# SPDX-License-Identifier: LGPL-3.0-or-later
"""Compare one-step vertical-status modulation experiments.

Q-7B-1 replaces only the status multiplier carried by the height-axis flux.
DBH transport, diffusion, mortality, numerical boundaries, and time step remain
patrimonial. Both transport-only and complete one-step responses are reported.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np
from scipy.sparse.linalg import spsolve

from pydynamicforest.model import evaluate_model_fields
from pydynamicforest.numerics import compute_derived_quantities
from pydynamicforest.observation_operators import (
    continuous_dominant_height_details,
    joint_moment_summary,
)
from pydynamicforest.solver import (
    advance_one_step_sparse_legacy,
    assemble_sparse_legacy_system,
    compute_transport_components_legacy,
    evaluate_model_fields_for_solver,
)
from pydynamicforest.types import State
from simulations.article_submission_legacy.diagnose_vertical_fluxes import (
    vertical_divergence_from_faces,
)
from simulations.article_submission_legacy.parameters import build_parameters

DEFAULT_STATE_FILES = {
    18: "state_age_18.npz",
    45: "state_age_44p9994.npz",
    69: "state_age_69.npz",
}
FORMULATIONS = (
    "linear",
    "sqrt",
    "floor_0p1_linear",
    "floor_0p1_sqrt",
)
RESPONSE_TYPES = ("transport_only", "full_step")
OBSERVABLES = (
    "stand_density",
    "mean_height_m",
    "mean_dbh_cm",
    "height_variance_m2",
    "continuous_top_height_m",
    "continuous_H0_minus_Hm_m",
)
CSV_FIELDS = [
    "target_age",
    "actual_age",
    "time",
    "step_index",
    "dt_year",
    "formulation",
    "response_type",
    *OBSERVABLES,
    *(f"d_{name}_dt" for name in OBSERVABLES),
    "min_state_density",
    "max_state_density",
]


def load_saved_state(path: str | Path) -> State:
    with np.load(Path(path)) as saved:
        return State(
            time=float(saved["time"]),
            age=float(saved["age"]),
            U=np.array(saved["U"], dtype=float),
            step_index=int(saved["step_index"]),
        )


def transform_status(status: np.ndarray, formulation: str) -> np.ndarray:
    """Apply a bounded monotone experimental status modulation."""
    status = np.clip(np.asarray(status, dtype=float), 0.0, 1.0)
    if formulation == "linear":
        transformed = status
    elif formulation == "sqrt":
        transformed = np.sqrt(status)
    elif formulation == "floor_0p1_linear":
        transformed = 0.1 + 0.9 * status
    elif formulation == "floor_0p1_sqrt":
        transformed = 0.1 + 0.9 * np.sqrt(status)
    else:
        raise ValueError(f"Unknown status formulation: {formulation}")
    return np.clip(transformed, 0.0, 1.0)


def compute_modified_height_transport(
    state: State,
    p,
    derived,
    fields: dict[str, np.ndarray],
    formulation: str,
) -> np.ndarray:
    """Return the legacy height divergence with transformed upwind status."""
    U = state.U
    J = derived.cumulative_distribution
    status = derived.status_field
    height_growth = fields["height_growth"]
    nx, ny = U.shape
    den = max(derived.total_mass, p.numerics.epsilon_zero_mass)
    flux = np.zeros((nx - 1, ny), dtype=float)

    for i in range(nx - 1):
        velocity = 0.5 * (height_growth[i + 1, :] + height_growth[i, :])
        positive = velocity >= 0.0
        lower_status = transform_status(status[i, :], formulation)
        upper_status = transform_status(J[i + 1, :] / den, formulation)
        upwind_density = np.where(
            positive,
            lower_status * U[i, :],
            upper_status * U[i + 1, :],
        )
        flux[i, :] = velocity * upwind_density

    return vertical_divergence_from_faces(flux, p)


def summarize_state(U: np.ndarray, p) -> dict[str, float]:
    moments = joint_moment_summary(U, p)
    dominant = continuous_dominant_height_details(U, p)
    Hm = moments["mean_height"]
    return {
        "stand_density": moments["stand_density"],
        "mean_height_m": Hm,
        "mean_dbh_cm": 100.0 * moments["mean_dbh_m"],
        "height_variance_m2": moments["height_variance_m2"],
        "continuous_top_height_m": float(dominant["dominant_height"]),
        "continuous_H0_minus_Hm_m": float(dominant["dominant_height"]) - Hm,
    }


def build_responses(state: State, p, formulation: str) -> dict[str, np.ndarray]:
    """Build transport-only and full-step responses for one formulation."""
    derived = compute_derived_quantities(state, p)
    current_fields = evaluate_model_fields_for_solver(state, p)
    next_fields = evaluate_model_fields(p, state.time + p.numerics.time.dt)
    patrimonial = compute_transport_components_legacy(
        state, p, derived, current_fields
    )
    height_transport = compute_modified_height_transport(
        state, p, derived, current_fields, formulation
    )
    total_transport = height_transport + patrimonial["dbh"]
    dt = p.numerics.time.dt
    transport_only = state.U - dt * total_transport
    A, b = assemble_sparse_legacy_system(
        state,
        p,
        derived,
        next_fields,
        total_transport,
    )
    full_step = np.asarray(spsolve(A, b), dtype=float).reshape(state.U.shape)
    return {"transport_only": transport_only, "full_step": full_step}


def diagnose_state(state: State, p=None, target_age=None):
    if p is None:
        p = build_parameters()
    target_age = state.age if target_age is None else target_age
    baseline = summarize_state(state.U, p)
    dt = p.numerics.time.dt
    rows = []
    for formulation in FORMULATIONS:
        for response_type, U_next in build_responses(state, p, formulation).items():
            summary = summarize_state(U_next, p)
            rows.append(
                {
                    "target_age": target_age,
                    "actual_age": state.age,
                    "time": state.time,
                    "step_index": state.step_index,
                    "dt_year": dt,
                    "formulation": formulation,
                    "response_type": response_type,
                    **summary,
                    **{
                        f"d_{name}_dt": (summary[name] - baseline[name]) / dt
                        for name in OBSERVABLES
                    },
                    "min_state_density": float(np.min(U_next)),
                    "max_state_density": float(np.max(U_next)),
                }
            )
    return rows


def patrimonial_regression(state: State, p=None) -> dict[str, float]:
    if p is None:
        p = build_parameters()
    diagnostic = build_responses(state, p, "linear")["full_step"]
    patrimonial = advance_one_step_sparse_legacy(state, p).U
    difference = diagnostic - patrimonial
    return {
        "max_abs_U_difference": float(np.max(np.abs(difference))),
        "l2_U_difference": float(np.linalg.norm(difference)),
    }


def diagnose_saved_states(state_dir, state_files=DEFAULT_STATE_FILES):
    p = build_parameters()
    rows, regressions = [], []
    for age, filename in state_files.items():
        path = Path(state_dir) / filename
        if not path.is_file():
            raise FileNotFoundError(f"Saved state not found: {path}")
        state = load_saved_state(path)
        rows.extend(diagnose_state(state, p, age))
        regressions.append({"target_age": age, **patrimonial_regression(state, p)})
    return rows, regressions


def write_outputs(output_dir, rows, regressions, state_dir):
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    csv_path = output / "vertical_status_modulation_responses.csv"
    json_path = output / "vertical_status_modulation_responses.json"
    markdown_path = output / "vertical_status_modulation_responses.md"
    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    payload = {
        "scope": "one-step alternatives to vertical status modulation",
        "state_directory": str(state_dir),
        "formulations": list(FORMULATIONS),
        "response_types": list(RESPONSE_TYPES),
        "fixed_mechanisms": [
            "patrimonial DBH transport",
            "patrimonial diffusion",
            "patrimonial mortality",
            "patrimonial time step and boundaries",
        ],
        "patrimonial_regression": regressions,
        "rows": rows,
    }
    json_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Q-7B-1 vertical status modulation responses",
        "",
        "Only the height-axis status multiplier is modified. DBH transport, diffusion, and mortality remain patrimonial.",
        "",
        "| Age | Response | Formulation | dHm/dt | dVar(H)/dt | dH0/dt | d(H0-Hm)/dt | dN/dt |",
        "|---:|:---|:---|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            "| {target_age:g} | {response_type} | {formulation} | "
            "{d_mean_height_m_dt:+.6f} | {d_height_variance_m2_dt:+.6f} | "
            "{d_continuous_top_height_m_dt:+.6f} | "
            "{d_continuous_H0_minus_Hm_m_dt:+.6f} | "
            "{d_stand_density_dt:+.6f} |".format(**row)
        )
    lines.extend(["", "## Patrimonial regression", ""])
    for regression in regressions:
        lines.append(
            f"- Age {regression['target_age']}: max absolute U difference "
            f"`{regression['max_abs_U_difference']:.3e}`."
        )
    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"csv": csv_path, "json": json_path, "markdown": markdown_path}


def run_diagnostic(state_dir, output_dir):
    rows, regressions = diagnose_saved_states(state_dir)
    return write_outputs(output_dir, rows, regressions, state_dir)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-dir", default="outputs/observation_quadrature_full")
    parser.add_argument("--output-dir", default="outputs/vertical_status_modulations")
    args = parser.parse_args()
    for name, path in run_diagnostic(args.state_dir, args.output_dir).items():
        print(f"{name}: {path.resolve()}")


if __name__ == "__main__":
    main()
