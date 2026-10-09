# SPDX-License-Identifier: LGPL-3.0-or-later
"""Diagnose one-step counterfactual responses of model mechanisms.

Q-7A-4b evaluates eight one-step experiments from saved patrimonial states:
identity, directional and total explicit transport, diffusion, mortality,
diffusion plus mortality, and the full patrimonial step.

The isolated implicit responses are counterfactual one-step responses. They are
not an additive biological decomposition of the full nonlinear trajectory.
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
from simulations.article_submission_legacy.parameters import build_parameters


DEFAULT_STATE_FILES = {
    18: "state_age_18.npz",
    45: "state_age_44p9994.npz",
    69: "state_age_69.npz",
}

EXPERIMENTS = (
    "identity",
    "height_transport_only",
    "dbh_transport_only",
    "total_transport_only",
    "diffusion_only",
    "mortality_only",
    "diffusion_and_mortality",
    "patrimonial_full_step",
)

OBSERVABLE_FIELDS = (
    "stand_density",
    "height_moment",
    "dbh_moment_m",
    "mean_height_m",
    "mean_dbh_cm",
    "height_variance_m2",
    "dbh_variance_cm2",
    "height_dbh_covariance_m_cm",
    "height_dbh_correlation",
    "continuous_top_height_m",
    "continuous_H0_minus_Hm_m",
)

RATE_FIELDS = tuple(f"d_{field}_dt" for field in OBSERVABLE_FIELDS)

CSV_FIELDS = [
    "target_age",
    "actual_age",
    "time",
    "step_index",
    "dt_year",
    "experiment",
    *OBSERVABLE_FIELDS,
    *RATE_FIELDS,
]

RESIDUAL_FIELDS = [
    "target_age",
    "residual_type",
    *OBSERVABLE_FIELDS,
    *RATE_FIELDS,
]


def load_saved_state(path: str | Path) -> State:
    """Load one NPZ state written by the full-run pipeline."""
    with np.load(Path(path)) as saved:
        return State(
            time=float(saved["time"]),
            age=float(saved["age"]),
            U=np.array(saved["U"], dtype=float),
            step_index=int(saved["step_index"]),
        )


def summarize_state(U: np.ndarray, p) -> dict[str, float]:
    """Return the first two joint moments and continuous dominant height."""
    summary = joint_moment_summary(U, p)
    dominant = continuous_dominant_height_details(U, p)
    mean_height = summary["mean_height"]
    return {
        "stand_density": summary["stand_density"],
        "height_moment": summary["height_moment"],
        "dbh_moment_m": summary["dbh_moment_m"],
        "mean_height_m": mean_height,
        "mean_dbh_cm": 100.0 * summary["mean_dbh_m"],
        "height_variance_m2": summary["height_variance_m2"],
        "dbh_variance_cm2": 10000.0 * summary["dbh_variance_m2"],
        "height_dbh_covariance_m_cm": 100.0
        * summary["height_dbh_covariance_m2"],
        "height_dbh_correlation": summary["height_dbh_correlation"],
        "continuous_top_height_m": float(dominant["dominant_height"]),
        "continuous_H0_minus_Hm_m": float(dominant["dominant_height"])
        - mean_height,
    }


def _solve_implicit_response(
    state: State,
    p,
    derived,
    fields_next: dict[str, np.ndarray],
    transport: np.ndarray,
    *,
    diffusion_factor: float,
    mortality_factor: float,
) -> np.ndarray:
    A, b = assemble_sparse_legacy_system(
        state,
        p,
        derived,
        fields_next,
        transport,
        diffusion_factor=diffusion_factor,
        mortality_factor=mortality_factor,
    )
    return np.asarray(spsolve(A, b), dtype=float).reshape(state.U.shape)


def build_one_step_experiments(state: State, p=None) -> dict[str, np.ndarray]:
    """Build the eight Q-7A-4b counterfactual next states."""
    if p is None:
        p = build_parameters()

    derived = compute_derived_quantities(state, p)
    fields_current = evaluate_model_fields_for_solver(state, p)
    fields_next = evaluate_model_fields(p, state.time + p.numerics.time.dt)
    components = compute_transport_components_legacy(
        state, p, derived, fields_current
    )
    zero_transport = np.zeros_like(state.U)
    dt = p.numerics.time.dt

    experiments = {
        "identity": state.U.copy(),
        "height_transport_only": state.U - dt * components["height"],
        "dbh_transport_only": state.U - dt * components["dbh"],
        "total_transport_only": state.U - dt * components["total"],
        "diffusion_only": _solve_implicit_response(
            state,
            p,
            derived,
            fields_next,
            zero_transport,
            diffusion_factor=1.0,
            mortality_factor=0.0,
        ),
        "mortality_only": _solve_implicit_response(
            state,
            p,
            derived,
            fields_next,
            zero_transport,
            diffusion_factor=0.0,
            mortality_factor=1.0,
        ),
        "diffusion_and_mortality": _solve_implicit_response(
            state,
            p,
            derived,
            fields_next,
            zero_transport,
            diffusion_factor=1.0,
            mortality_factor=1.0,
        ),
        "patrimonial_full_step": _solve_implicit_response(
            state,
            p,
            derived,
            fields_next,
            components["total"],
            diffusion_factor=1.0,
            mortality_factor=1.0,
        ),
    }
    if tuple(experiments) != EXPERIMENTS:
        raise RuntimeError("Unexpected Q-7A-4b experiment order.")
    return experiments


def diagnose_state_responses(
    state: State,
    p=None,
    target_age: int | float | None = None,
) -> tuple[list[dict], dict[str, float]]:
    """Return response rows and full-step regression residuals for one state."""
    if p is None:
        p = build_parameters()
    dt = p.numerics.time.dt
    baseline = summarize_state(state.U, p)
    experiments = build_one_step_experiments(state, p)

    rows: list[dict] = []
    for name, U_next in experiments.items():
        summary = summarize_state(U_next, p)
        rates = {
            f"d_{field}_dt": (summary[field] - baseline[field]) / dt
            for field in OBSERVABLE_FIELDS
        }
        rows.append(
            {
                "target_age": state.age if target_age is None else target_age,
                "actual_age": state.age,
                "time": state.time,
                "step_index": state.step_index,
                "dt_year": dt,
                "experiment": name,
                **summary,
                **rates,
            }
        )

    patrimonial = advance_one_step_sparse_legacy(state, p)
    diagnostic_full = experiments["patrimonial_full_step"]
    regression = {
        "max_abs_U_difference": float(
            np.max(np.abs(diagnostic_full - patrimonial.U))
        ),
        "l2_U_difference": float(
            np.linalg.norm(diagnostic_full - patrimonial.U)
        ),
    }
    return rows, regression


def _rows_by_experiment(rows: list[dict]) -> dict[str, dict]:
    result = {str(row["experiment"]): row for row in rows}
    if set(result) != set(EXPERIMENTS):
        raise ValueError("The complete set of Q-7A-4b experiments is required.")
    return result


def response_residuals(rows: list[dict]) -> list[dict]:
    """Calculate non-additivity residuals for observables and their rates."""
    by_name = _rows_by_experiment(rows)
    identity_row = by_name["identity"]

    def delta(experiment: str, field: str) -> float:
        return float(by_name[experiment][field]) - float(identity_row[field])

    specifications = {
        "implicit_nonadditivity": (
            "diffusion_and_mortality",
            "diffusion_only",
            "mortality_only",
        ),
        "full_minus_transport_minus_implicit": (
            "patrimonial_full_step",
            "total_transport_only",
            "diffusion_and_mortality",
        ),
    }

    residual_rows = []
    for residual_type, (joint, left, right) in specifications.items():
        residual = {
            "target_age": rows[0]["target_age"],
            "residual_type": residual_type,
        }
        for field in OBSERVABLE_FIELDS:
            residual[field] = delta(joint, field) - delta(left, field) - delta(
                right, field
            )
            residual[f"d_{field}_dt"] = residual[field] / float(
                rows[0]["dt_year"]
            )
        residual_rows.append(residual)
    return residual_rows


def diagnose_saved_states(
    state_dir: str | Path,
    state_files: dict[int, str] = DEFAULT_STATE_FILES,
) -> tuple[list[dict], list[dict], list[dict]]:
    """Diagnose all configured patrimonial states."""
    p = build_parameters()
    rows: list[dict] = []
    residuals: list[dict] = []
    regressions: list[dict] = []
    state_path = Path(state_dir)

    for target_age, filename in state_files.items():
        path = state_path / filename
        if not path.is_file():
            raise FileNotFoundError(f"Saved state not found: {path}")
        state_rows, regression = diagnose_state_responses(
            load_saved_state(path), p=p, target_age=target_age
        )
        rows.extend(state_rows)
        residuals.extend(response_residuals(state_rows))
        regressions.append({"target_age": target_age, **regression})
    return rows, residuals, regressions


def write_outputs(
    output_dir: str | Path,
    rows: list[dict],
    residuals: list[dict],
    regressions: list[dict],
    state_dir: str | Path,
) -> dict[str, Path]:
    """Write CSV, JSON, and Markdown Q-7A-4b outputs."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    responses_csv = output_path / "implicit_step_responses.csv"
    with responses_csv.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    residuals_csv = output_path / "implicit_step_additivity.csv"
    with residuals_csv.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=RESIDUAL_FIELDS)
        writer.writeheader()
        writer.writerows(residuals)

    json_path = output_path / "implicit_step_responses.json"
    payload = {
        "scope": "one-step counterfactual mechanism responses",
        "state_directory": str(state_dir),
        "experiments": list(EXPERIMENTS),
        "interpretation_warning": (
            "Isolated implicit responses and response residuals are numerical "
            "counterfactuals, not additive biological effects."
        ),
        "units": {
            "stand_density": "trees ha-1",
            "height_moment": "m trees ha-1",
            "dbh_moment_m": "m trees ha-1",
            "mean_height_m": "m",
            "mean_dbh_cm": "cm",
            "height_variance_m2": "m2",
            "dbh_variance_cm2": "cm2",
            "height_dbh_covariance_m_cm": "m cm",
            "height_dbh_correlation": "dimensionless",
            "continuous_top_height_m": "m",
            "continuous_H0_minus_Hm_m": "m",
        },
        "full_step_regression": regressions,
        "residuals": residuals,
        "rows": rows,
    }
    json_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    markdown_path = output_path / "implicit_step_responses.md"
    lines = [
        "# Q-7A-4b one-step mechanism responses",
        "",
        "The isolated implicit responses are numerical counterfactuals, not an additive biological decomposition.",
        "",
        "| Age | Experiment | dN/dt | dHm/dt | dVar(H)/dt | dH0/dt | d(H0-Hm)/dt |",
        "|---:|:---|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            "| {age:g} | {experiment} | {dN:+.6e} | {dHm:+.6e} | "
            "{dVarH:+.6e} | {dH0:+.6e} | {dGap:+.6e} |".format(
                age=float(row["target_age"]),
                experiment=row["experiment"],
                dN=float(row["d_stand_density_dt"]),
                dHm=float(row["d_mean_height_m_dt"]),
                dVarH=float(row["d_height_variance_m2_dt"]),
                dH0=float(row["d_continuous_top_height_m_dt"]),
                dGap=float(row["d_continuous_H0_minus_Hm_m_dt"]),
            )
        )
    lines.extend(["", "## Full-step regression", ""])
    for regression in regressions:
        lines.append(
            f"- Age {regression['target_age']}: max absolute U difference "
            f"`{regression['max_abs_U_difference']:.3e}`."
        )
    lines.extend(["", "## Response non-additivity", ""])
    for residual in residuals:
        lines.append(
            f"- Age {residual['target_age']}, {residual['residual_type']}: "
            f"dHm residual `{residual['d_mean_height_m_dt']:+.3e}` m/year; "
            f"dVar(H) residual `{residual['d_height_variance_m2_dt']:+.3e}` m2/year."
        )
    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    return {
        "responses_csv": responses_csv,
        "residuals_csv": residuals_csv,
        "json_path": json_path,
        "markdown_path": markdown_path,
    }


def run_diagnostic(
    state_dir: str | Path,
    output_dir: str | Path,
) -> dict[str, Path]:
    rows, residuals, regressions = diagnose_saved_states(state_dir)
    return write_outputs(
        output_dir, rows, residuals, regressions, state_dir
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--state-dir",
        default="outputs/observation_quadrature_full",
    )
    parser.add_argument(
        "--output-dir",
        default="outputs/implicit_step_responses",
    )
    args = parser.parse_args()
    result = run_diagnostic(args.state_dir, args.output_dir)
    print(f"Responses CSV: {result['responses_csv'].resolve()}")
    print(f"Additivity CSV: {result['residuals_csv'].resolve()}")
    print(f"JSON: {result['json_path'].resolve()}")
    print(f"Markdown: {result['markdown_path'].resolve()}")


if __name__ == "__main__":
    main()
