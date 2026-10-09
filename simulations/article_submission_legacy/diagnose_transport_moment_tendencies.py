# SPDX-License-Identifier: LGPL-3.0-or-later
"""Diagnose instantaneous stand-moment tendencies from explicit transport.

Q-7A-3 evaluates the exact directional transport components exposed by Q-7A-2
on saved patrimonial states. The solver uses ``U - dt * transport``; therefore
the instantaneous explicit tendencies are ``dot_U = -transport``.

The reported height and DBH mean tendencies use quotient-rule diagnostics:

    dot_Hm = (dot_Mh - Hm * dot_N) / N
    dot_Dm = (dot_Md - Dm * dot_N) / N

This script diagnoses only the explicit transport part of the semi-implicit
scheme. Diffusion and mortality are deliberately excluded at this stage.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np

from pydynamicforest.numerics import (
    compute_derived_quantities,
    product_trapezoidal_weights,
)
from pydynamicforest.observation_operators import (
    joint_moment_summary,
    physical_dbh_nodes,
    physical_height_nodes,
)
from pydynamicforest.solver import (
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

RATE_FIELDS = (
    "dN_dt_trees_ha_year",
    "dMh_dt_m_trees_ha_year",
    "dMd_dt_m_trees_ha_year",
    "dHm_dt_m_year",
    "dDm_dt_m_year",
    "dDm_dt_cm_year",
)

CSV_FIELDS = [
    "target_age",
    "actual_age",
    "time",
    "step_index",
    "component",
    "stand_density",
    "mean_height_m",
    "mean_dbh_m",
    *RATE_FIELDS,
]


def load_saved_state(path: str | Path) -> State:
    """Load one state written by the article-submission full-run pipeline."""

    with np.load(Path(path)) as saved:
        return State(
            time=float(saved["time"]),
            age=float(saved["age"]),
            U=np.array(saved["U"], dtype=float),
            step_index=int(saved["step_index"]),
        )


def signed_raw_moment_rates(
    dot_U: np.ndarray,
    p,
) -> dict[str, float]:
    """Integrate signed density tendencies with observation quadrature.

    ``stand_moment`` intentionally validates non-negative stand densities and
    must not be used for signed process tendencies. This helper uses the same
    tensor-product trapezoidal weights and physical nodes, but accepts signs.
    """

    expected_shape = (p.numerics.grid.nx, p.numerics.grid.ny)
    if dot_U.shape != expected_shape:
        raise ValueError(
            f"Tendency shape {dot_U.shape} does not match grid shape "
            f"{expected_shape}."
        )
    if not np.all(np.isfinite(dot_U)):
        raise ValueError("Tendency must contain only finite values.")

    weights = product_trapezoidal_weights(p)
    height_m = physical_height_nodes(p)[:, None]
    dbh_m = physical_dbh_nodes(p, unit="m")[None, :]
    return {
        "dN_dt_trees_ha_year": float(np.sum(weights * dot_U)),
        "dMh_dt_m_trees_ha_year": float(
            np.sum(weights * height_m * dot_U)
        ),
        "dMd_dt_m_trees_ha_year": float(
            np.sum(weights * dbh_m * dot_U)
        ),
    }


def mean_tendency_rates(
    state_summary: dict[str, float],
    raw_rates: dict[str, float],
) -> dict[str, float]:
    """Convert raw moment rates to arithmetic-mean rates."""

    N = state_summary["stand_density"]
    if not np.isfinite(N) or N <= 0.0:
        return {
            "dHm_dt_m_year": float("nan"),
            "dDm_dt_m_year": float("nan"),
            "dDm_dt_cm_year": float("nan"),
        }

    Hm = state_summary["mean_height"]
    Dm = state_summary["mean_dbh_m"]
    dN = raw_rates["dN_dt_trees_ha_year"]
    dMh = raw_rates["dMh_dt_m_trees_ha_year"]
    dMd = raw_rates["dMd_dt_m_trees_ha_year"]
    dHm = (dMh - Hm * dN) / N
    dDm = (dMd - Dm * dN) / N
    return {
        "dHm_dt_m_year": float(dHm),
        "dDm_dt_m_year": float(dDm),
        "dDm_dt_cm_year": float(100.0 * dDm),
    }


def tendency_summary(
    dot_U: np.ndarray,
    state_summary: dict[str, float],
    p,
) -> dict[str, float]:
    """Return raw and normalized tendencies for one process component."""

    raw = signed_raw_moment_rates(dot_U, p)
    return {**raw, **mean_tendency_rates(state_summary, raw)}


def diagnose_state_transport(
    state: State,
    p=None,
    target_age: int | float | None = None,
) -> list[dict[str, float | int | str]]:
    """Diagnose height, DBH, and total explicit transport at one state."""

    if p is None:
        p = build_parameters()
    state_summary = joint_moment_summary(state.U, p)
    derived = compute_derived_quantities(state, p)
    fields = evaluate_model_fields_for_solver(state, p)
    transport = compute_transport_components_legacy(state, p, derived, fields)

    dot_U_components = {
        "height_transport": -transport["height"],
        "dbh_transport": -transport["dbh"],
        "total_transport": -transport["total"],
    }

    rows = []
    for component, dot_U in dot_U_components.items():
        rates = tendency_summary(dot_U, state_summary, p)
        rows.append(
            {
                "target_age": state.age if target_age is None else target_age,
                "actual_age": state.age,
                "time": state.time,
                "step_index": state.step_index,
                "component": component,
                "stand_density": state_summary["stand_density"],
                "mean_height_m": state_summary["mean_height"],
                "mean_dbh_m": state_summary["mean_dbh_m"],
                **rates,
            }
        )
    return rows


def component_additivity_residuals(
    rows: list[dict[str, float | int | str]],
) -> dict[str, float]:
    """Return total minus height-plus-DBH residuals for every rate."""

    by_name = {str(row["component"]): row for row in rows}
    required = {"height_transport", "dbh_transport", "total_transport"}
    if set(by_name) != required:
        raise ValueError(f"Expected components {sorted(required)}.")

    residuals = {}
    for field in RATE_FIELDS:
        residuals[field] = float(
            by_name["total_transport"][field]
            - by_name["height_transport"][field]
            - by_name["dbh_transport"][field]
        )
    return residuals


def diagnose_saved_states(
    state_dir: str | Path,
    state_files: dict[int, str] = DEFAULT_STATE_FILES,
) -> tuple[list[dict], list[dict]]:
    """Diagnose all configured saved patrimonial states."""

    p = build_parameters()
    rows: list[dict] = []
    checks: list[dict] = []
    state_path = Path(state_dir)
    for target_age, filename in state_files.items():
        path = state_path / filename
        if not path.is_file():
            raise FileNotFoundError(f"Saved state not found: {path}")
        state_rows = diagnose_state_transport(
            load_saved_state(path),
            p=p,
            target_age=target_age,
        )
        rows.extend(state_rows)
        checks.append(
            {
                "target_age": target_age,
                "residuals": component_additivity_residuals(state_rows),
            }
        )
    return rows, checks


def _format_rate(value: float) -> str:
    return f"{value:+.9e}"


def write_outputs(
    output_dir: str | Path,
    rows: list[dict],
    checks: list[dict],
    state_dir: str | Path,
) -> dict[str, Path]:
    """Write CSV, JSON, and Markdown Q-7A-3 diagnostics."""

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    csv_path = output_path / "transport_moment_tendencies.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    json_path = output_path / "transport_moment_tendencies.json"
    payload = {
        "scope": "explicit height and DBH transport only",
        "sign_convention": "dot_U = -transport because RHS is U - dt * transport",
        "state_directory": str(state_dir),
        "units": {
            "dN_dt_trees_ha_year": "trees ha-1 year-1",
            "dMh_dt_m_trees_ha_year": "m trees ha-1 year-1",
            "dMd_dt_m_trees_ha_year": "m trees ha-1 year-1",
            "dHm_dt_m_year": "m year-1",
            "dDm_dt_m_year": "m year-1",
            "dDm_dt_cm_year": "cm year-1",
        },
        "additivity_checks": checks,
        "rows": rows,
    }
    json_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    markdown_path = output_path / "transport_moment_tendencies.md"
    lines = [
        "# Explicit transport moment tendencies",
        "",
        "Only the explicit transport terms are diagnosed. Diffusion and mortality are excluded.",
        "",
        "| Target age | Component | dN/dt | dMh/dt | dHm/dt | dMd/dt | dDm/dt |",
        "|---:|:---|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            "| {target_age:g} | {component} | {dN} | {dMh} | {dHm} | {dMd} | {dDm} |".format(
                target_age=float(row["target_age"]),
                component=row["component"],
                dN=_format_rate(float(row["dN_dt_trees_ha_year"])),
                dMh=_format_rate(float(row["dMh_dt_m_trees_ha_year"])),
                dHm=_format_rate(float(row["dHm_dt_m_year"])),
                dMd=_format_rate(float(row["dMd_dt_m_trees_ha_year"])),
                dDm=_format_rate(float(row["dDm_dt_cm_year"])),
            )
        )
    lines.extend(
        [
            "",
            "## Additivity checks",
            "",
            "Each residual is total minus height minus DBH transport.",
            "",
        ]
    )
    for check in checks:
        maximum = max(abs(float(value)) for value in check["residuals"].values())
        lines.append(
            f"- Age {check['target_age']}: maximum absolute rate residual "
            f"`{maximum:.3e}`."
        )
    lines.extend(
        [
            "",
            "## Interpretation boundary",
            "",
            "These rates are instantaneous explicit-transport diagnostics. They are not the full one-step tendencies of the semi-implicit solver and must not be attributed to diffusion or mortality.",
        ]
    )
    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    return {
        "csv_path": csv_path,
        "json_path": json_path,
        "markdown_path": markdown_path,
    }


def run_diagnostic(
    state_dir: str | Path,
    output_dir: str | Path,
) -> dict[str, Path]:
    """Run Q-7A-3 on saved states and write all outputs."""

    rows, checks = diagnose_saved_states(state_dir)
    return write_outputs(output_dir, rows, checks, state_dir)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--state-dir",
        default="outputs/observation_quadrature_full",
        help="Directory containing patrimonial NPZ states at ages 18, 45, and 69.",
    )
    parser.add_argument(
        "--output-dir",
        default="outputs/transport_moment_tendencies",
    )
    args = parser.parse_args()
    result = run_diagnostic(args.state_dir, args.output_dir)
    print(f"CSV: {result['csv_path'].resolve()}")
    print(f"JSON: {result['json_path'].resolve()}")
    print(f"Markdown: {result['markdown_path'].resolve()}")


if __name__ == "__main__":
    main()
