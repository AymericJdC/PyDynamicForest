# SPDX-License-Identifier: LGPL-3.0-or-later
"""Diagnose legacy vertical face fluxes and their moment contributions.

Q-7A-5b reconstructs the height-axis upwind fluxes used by the patrimonial
transport scheme, verifies their divergence against Q-7A-2, and attributes
flux and moment-rate contributions to height interfaces, DBH classes, and the
upwind status carried by each face flux.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np

from pydynamicforest.numerics import (
    compute_derived_quantities,
    dbh_trapezoidal_weights,
    product_trapezoidal_weights,
)
from pydynamicforest.observation_operators import joint_moment_summary, physical_dbh_nodes
from pydynamicforest.solver import compute_transport_components_legacy, evaluate_model_fields_for_solver
from pydynamicforest.types import State
from simulations.article_submission_legacy.parameters import build_parameters

DEFAULT_STATE_FILES = {18: "state_age_18.npz", 45: "state_age_44p9994.npz", 69: "state_age_69.npz"}
STATUS_EDGES = np.array([0.0, 0.2, 0.4, 0.6, 0.8, 1.0])
DBH_EDGES_CM = np.array([0.0, 20.0, 40.0, 60.0, 80.0, np.inf])

INTERFACE_FIELDS = [
    "target_age", "interface_index", "height_interface_m", "integrated_flux_trees_ha_year",
    "flux_share", "mean_upwind_status", "dN_dt_below", "dMh_dt_contribution_m_trees_ha_year",
    "dMh_mean_contribution_m_year", "dMh2_dt_contribution_m2_trees_ha_year",
    "dVarH_dt_contribution_m2_year",
]
CLASS_FIELDS = [
    "target_age", "classification", "class_label", "lower", "upper", "upper_inclusive",
    "integrated_flux_trees_ha_year", "flux_share", "dMh_dt_contribution_m_trees_ha_year",
    "dHm_dt_contribution_m_year", "dMh2_dt_contribution_m2_trees_ha_year",
    "dVarH_dt_contribution_m2_year",
]
CHECK_FIELDS = [
    "target_age", "max_abs_divergence_residual", "l2_divergence_residual",
    "direct_dN_dt", "flux_dN_dt", "direct_dMh_dt", "flux_dMh_dt",
    "direct_dMh2_dt", "flux_dMh2_dt", "direct_dHm_dt", "flux_dHm_dt",
    "direct_dVarH_dt", "flux_dVarH_dt",
]


def load_saved_state(path: str | Path) -> State:
    with np.load(Path(path)) as saved:
        return State(time=float(saved["time"]), age=float(saved["age"]), U=np.array(saved["U"], dtype=float), step_index=int(saved["step_index"]))


def compute_vertical_face_fluxes(state: State, p, derived, fields):
    """Return face fluxes F[i+1/2,j] and the upwind status carried by them."""
    U = state.U
    J = derived.cumulative_distribution
    S = derived.status_field
    Ch = fields["height_growth"]
    nx, ny = U.shape
    den = max(derived.total_mass, p.numerics.epsilon_zero_mass)
    flux = np.zeros((nx - 1, ny), dtype=float)
    upwind_status = np.zeros_like(flux)
    for i in range(nx - 1):
        velocity = 0.5 * (Ch[i + 1, :] + Ch[i, :])
        positive = velocity >= 0.0
        lower_status = S[i, :]
        upper_status = J[i + 1, :] / den
        upwind_status[i, :] = np.where(positive, lower_status, upper_status)
        upwind_density = np.where(positive, lower_status * U[i, :], upper_status * U[i + 1, :])
        flux[i, :] = velocity * upwind_density
    return flux, upwind_status


def vertical_divergence_from_faces(flux, p):
    nx = p.numerics.grid.nx
    ny = p.numerics.grid.ny
    divergence = np.zeros((nx, ny), dtype=float)
    divergence[:-1, :] += flux / p.numerics.grid.dx
    divergence[1:, :] -= flux / p.numerics.grid.dx
    return divergence


def _signed_height_rates(dot_U, p, state_summary):
    weights = product_trapezoidal_weights(p)
    h = (p.numerics.grid.x * p.model.physical_scales.height_scale)[:, None]
    dN = float(np.sum(weights * dot_U))
    dMh = float(np.sum(weights * h * dot_U))
    dMh2 = float(np.sum(weights * h**2 * dot_U))
    N = state_summary["stand_density"]
    Hm = state_summary["mean_height"]
    Mh2_per_stem = state_summary["height_second_moment"] / N
    dHm = (dMh - Hm * dN) / N
    dVar = (dMh2 - Mh2_per_stem * dN) / N - 2.0 * Hm * dHm
    return {"dN": dN, "dMh": dMh, "dMh2": dMh2, "dHm": dHm, "dVarH": dVar}


def _flux_subset_rates(flux_subset, state, p, summary):
    dot_U = -vertical_divergence_from_faces(flux_subset, p)
    return _signed_height_rates(dot_U, p, summary)


def _class_mask(values, lower, upper, final):
    return (values >= lower) & ((values <= upper) if final else (values < upper))


def diagnose_state(state: State, p=None, target_age=None):
    if p is None:
        p = build_parameters()
    age = state.age if target_age is None else target_age
    derived = compute_derived_quantities(state, p)
    fields = evaluate_model_fields_for_solver(state, p)
    components = compute_transport_components_legacy(state, p, derived, fields)
    faces, upwind_status = compute_vertical_face_fluxes(state, p, derived, fields)
    divergence = vertical_divergence_from_faces(faces, p)
    residual = divergence - components["height"]
    summary = joint_moment_summary(state.U, p)
    direct = _signed_height_rates(-components["height"], p, summary)
    reconstructed = _flux_subset_rates(faces, state, p, summary)

    dbh_weights = dbh_trapezoidal_weights(p)
    integrated_faces = faces @ dbh_weights
    positive_total = float(np.sum(np.maximum(integrated_faces, 0.0)))
    height_scale = p.model.physical_scales.height_scale
    face_heights = 0.5 * (p.numerics.grid.x[:-1] + p.numerics.grid.x[1:]) * height_scale
    interface_rows = []
    for i, height in enumerate(face_heights):
        subset = np.zeros_like(faces); subset[i, :] = faces[i, :]
        rates = _flux_subset_rates(subset, state, p, summary)
        face_weights = dbh_weights * np.abs(faces[i, :])
        mean_status = float(np.sum(face_weights * upwind_status[i, :]) / np.sum(face_weights)) if np.sum(face_weights) > 0 else float("nan")
        interface_rows.append({
            "target_age": age, "interface_index": i, "height_interface_m": float(height),
            "integrated_flux_trees_ha_year": float(integrated_faces[i]),
            "flux_share": float(max(integrated_faces[i], 0.0) / positive_total) if positive_total > 0 else float("nan"),
            "mean_upwind_status": mean_status, "dN_dt_below": -float(integrated_faces[i]),
            "dMh_dt_contribution_m_trees_ha_year": rates["dMh"],
            "dMh_mean_contribution_m_year": rates["dHm"],
            "dMh2_dt_contribution_m2_trees_ha_year": rates["dMh2"],
            "dVarH_dt_contribution_m2_year": rates["dVarH"],
        })

    class_rows = []
    dbh_nodes = physical_dbh_nodes(p, unit="cm")
    for classification, edges, values in (
        ("dbh_cm", DBH_EDGES_CM, np.broadcast_to(dbh_nodes[None, :], faces.shape)),
        ("upwind_status", STATUS_EDGES, upwind_status),
    ):
        for k, (lower, upper) in enumerate(zip(edges[:-1], edges[1:])):
            final = k == len(edges) - 2
            mask = _class_mask(values, lower, upper, final)
            subset = np.where(mask, faces, 0.0)
            rates = _flux_subset_rates(subset, state, p, summary)
            integrated = float(np.sum((subset @ dbh_weights)))
            class_rows.append({
                "target_age": age, "classification": classification,
                "class_label": f"[{lower:g}, {upper:g}{']' if final else '['}",
                "lower": lower, "upper": upper, "upper_inclusive": final,
                "integrated_flux_trees_ha_year": integrated,
                "flux_share": integrated / float(np.sum(integrated_faces)) if np.sum(integrated_faces) != 0 else float("nan"),
                "dMh_dt_contribution_m_trees_ha_year": rates["dMh"],
                "dHm_dt_contribution_m_year": rates["dHm"],
                "dMh2_dt_contribution_m2_trees_ha_year": rates["dMh2"],
                "dVarH_dt_contribution_m2_year": rates["dVarH"],
            })

    check = {
        "target_age": age,
        "max_abs_divergence_residual": float(np.max(np.abs(residual))),
        "l2_divergence_residual": float(np.linalg.norm(residual)),
        "direct_dN_dt": direct["dN"], "flux_dN_dt": reconstructed["dN"],
        "direct_dMh_dt": direct["dMh"], "flux_dMh_dt": reconstructed["dMh"],
        "direct_dMh2_dt": direct["dMh2"], "flux_dMh2_dt": reconstructed["dMh2"],
        "direct_dHm_dt": direct["dHm"], "flux_dHm_dt": reconstructed["dHm"],
        "direct_dVarH_dt": direct["dVarH"], "flux_dVarH_dt": reconstructed["dVarH"],
    }
    return interface_rows, class_rows, check


def diagnose_saved_states(state_dir, state_files=DEFAULT_STATE_FILES):
    p = build_parameters(); interfaces, classes, checks = [], [], []
    for age, filename in state_files.items():
        path = Path(state_dir) / filename
        if not path.is_file(): raise FileNotFoundError(f"Saved state not found: {path}")
        irows, crows, check = diagnose_state(load_saved_state(path), p, age)
        interfaces.extend(irows); classes.extend(crows); checks.append(check)
    return interfaces, classes, checks


def write_outputs(output_dir, interfaces, classes, checks, state_dir):
    output = Path(output_dir); output.mkdir(parents=True, exist_ok=True)
    files = {"interfaces": output / "vertical_flux_interfaces.csv", "classes": output / "vertical_flux_classes.csv", "checks": output / "vertical_flux_reconstruction.csv", "json": output / "vertical_fluxes.json", "markdown": output / "vertical_fluxes.md"}
    for key, rows, fields in (("interfaces", interfaces, INTERFACE_FIELDS), ("classes", classes, CLASS_FIELDS), ("checks", checks, CHECK_FIELDS)):
        with files[key].open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields); writer.writeheader(); writer.writerows(rows)
    payload = {"scope": "legacy vertical upwind face fluxes", "state_directory": str(state_dir), "dbh_edges_cm": DBH_EDGES_CM.tolist(), "status_edges": STATUS_EDGES.tolist(), "reconstruction_checks": checks, "interface_rows": interfaces, "class_rows": classes}
    files["json"].write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    lines = ["# Q-7A-5b vertical face fluxes", "", "The diagnostic reconstructs the legacy height-axis upwind fluxes and their moment contributions.", "", "## Reconstruction", ""]
    for row in checks:
        lines.append(f"- Age {row['target_age']}: max divergence residual `{row['max_abs_divergence_residual']:.3e}`; dHm `{row['flux_dHm_dt']:.6f}` m/year; dVar(H) `{row['flux_dVarH_dt']:.6f}` m2/year.")
    lines.extend(["", "## Contributions by class", "", "| Age | Classification | Class | Flux share | dHm/dt | dVar(H)/dt |", "|---:|:---|:---|---:|---:|---:|"])
    for row in classes:
        lines.append("| {target_age:g} | {classification} | {class_label} | {flux_share:.4f} | {dHm_dt_contribution_m_year:+.6f} | {dVarH_dt_contribution_m2_year:+.6f} |".format(**row))
    files["markdown"].write_text("\n".join(lines) + "\n", encoding="utf-8")
    return files


def run_diagnostic(state_dir, output_dir):
    return write_outputs(output_dir, *diagnose_saved_states(state_dir), state_dir)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-dir", default="outputs/observation_quadrature_full")
    parser.add_argument("--output-dir", default="outputs/vertical_fluxes")
    args = parser.parse_args(); files = run_diagnostic(args.state_dir, args.output_dir)
    for name, path in files.items(): print(f"{name}: {path.resolve()}")


if __name__ == "__main__": main()
