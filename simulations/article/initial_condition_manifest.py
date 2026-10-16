# SPDX-License-Identifier: LGPL-3.0-or-later
"""Write a reproducible manifest for the manuscript initial condition."""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
from pathlib import Path

import numpy as np

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
from simulations.article.config import ARTICLE_CONFIG
from simulations.article.context import build_context
from simulations.article.initial_condition import build_initial_condition
from simulations.article.parameters import build_parameters
from simulations.article_submission_legacy.diagnose_initial_condition import (
    INITIAL_OBSERVATIONS,
    _observed_derived_diameter_moments,
)

SUMMARY_FIELDS = [
    "observable", "simulated_value", "observed_or_derived_value", "residual",
    "unit", "status",
]
DENSITY_FIELDS = [
    "height_m", "dbh_cm", "density_trees_ha_per_normalized_area",
    "quadrature_weight", "weighted_stems_ha",
]


def _git_value(*args: str) -> str:
    try:
        return subprocess.check_output(
            ["git", *args], text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unavailable"


def build_manifest() -> tuple[dict, list[dict], list[dict]]:
    p = build_parameters()
    c = build_context()
    initial = build_initial_condition()
    state = build_initial_state(initial, p, c)
    summary = joint_moment_summary(state.U, p)
    dominant = continuous_dominant_height_details(state.U, p)
    diameter_observed = _observed_derived_diameter_moments()

    simulated = {
        "N": stand_density(state.U, p),
        "G": basal_area_consistent(state.U, p),
        "Dm": 100.0 * summary["mean_dbh_m"],
        "Dg": quadratic_mean_dbh(state.U, p, unit="cm"),
        "sigma_D": 100.0 * np.sqrt(summary["dbh_variance_m2"]),
        "Hm": summary["mean_height"],
        "sigma_H": np.sqrt(summary["height_variance_m2"]),
        "H0_continuous": dominant["dominant_height"],
        "rho_HD_effective": height_dbh_correlation(state.U, p),
        "dominant_threshold_dbh": 100.0 * dominant["threshold_dbh"],
        "dominant_selected_stems": dominant["selected_stems"],
    }
    observed = {
        "N": INITIAL_OBSERVATIONS["N"],
        "G": INITIAL_OBSERVATIONS["G"],
        "Dm": INITIAL_OBSERVATIONS["Dm_cm"],
        "Dg": diameter_observed["Dg_cm"],
        "sigma_D": diameter_observed["standard_deviation_cm"],
        "Hm": INITIAL_OBSERVATIONS["Hm"],
        "sigma_H": ARTICLE_CONFIG["initial_condition"]["sigma_h_physical"],
        "H0_continuous": INITIAL_OBSERVATIONS["H0"],
    }
    units = {
        "N": "trees/ha", "G": "m2/ha", "Dm": "cm", "Dg": "cm",
        "sigma_D": "cm", "Hm": "m", "sigma_H": "m",
        "H0_continuous": "m", "rho_HD_effective": "dimensionless",
        "dominant_threshold_dbh": "cm", "dominant_selected_stems": "trees/ha",
    }
    labels = {
        "N": "observed", "G": "observed", "Dm": "observed",
        "Dg": "derived from observed N and G",
        "sigma_D": "derived from observed Dm and Dg",
        "Hm": "observed", "sigma_H": "Gaussian marginal parameter",
        "H0_continuous": "observed target used as reconstruction constraint",
        "rho_HD_effective": "simulated joint-distribution property",
        "dominant_threshold_dbh": "simulated observation-operator threshold",
        "dominant_selected_stems": "simulated observation-operator mass",
    }
    rows = []
    for name, value in simulated.items():
        target = observed.get(name)
        rows.append({
            "observable": name,
            "simulated_value": float(value),
            "observed_or_derived_value": "" if target is None else float(target),
            "residual": "" if target is None else float(value - target),
            "unit": units[name],
            "status": labels[name],
        })

    weights = product_trapezoidal_weights(p)
    heights = physical_height_nodes(p)
    dbhs = physical_dbh_nodes(p, unit="cm")
    density_rows = []
    for i, height in enumerate(heights):
        for j, dbh in enumerate(dbhs):
            density_rows.append({
                "height_m": float(height),
                "dbh_cm": float(dbh),
                "density_trees_ha_per_normalized_area": float(state.U[i, j]),
                "quadrature_weight": float(weights[i, j]),
                "weighted_stems_ha": float(weights[i, j] * state.U[i, j]),
            })

    manifest = {
        "purpose": "initial distributed state of the numerical simulation retained for the manuscript",
        "git": {"branch": _git_value("branch", "--show-current"), "commit": _git_value("rev-parse", "HEAD")},
        "configuration_name": ARTICLE_CONFIG["name"],
        "initial_condition": {
            "name": initial.name,
            "family": "truncated correlated bivariate Gaussian",
            "initial_age_years": initial.initial_age,
            "mass_target_trees_ha": initial.mass_target,
            "marginal_parameters": {
                "height_mean_m": initial.distribution_parameters["h0_physical"],
                "height_sd_m": initial.distribution_parameters["sigma_h_physical"],
                "dbh_mean_m": initial.distribution_parameters["d0_physical"],
                "dbh_sd_m": initial.distribution_parameters["sigma_d_physical"],
            },
            "requested_height_dbh_correlation": initial.distribution_parameters["height_dbh_correlation"],
            "effective_height_dbh_correlation": simulated["rho_HD_effective"],
            "dependence_status": initial.description,
            "future_replacement": "complete individual-tree inventory when available and audited",
        },
        "numerical_support": {
            "grid_shape": [p.numerics.grid.nx, p.numerics.grid.ny],
            "normalized_height_interval": [p.numerics.grid.x_min, p.numerics.grid.x_max],
            "normalized_dbh_interval": [p.numerics.grid.y_min, p.numerics.grid.y_max],
            "height_scale_m": p.model.physical_scales.height_scale,
            "dbh_scale_m": p.model.physical_scales.dbh_scale,
            "quadrature": "tensor-product trapezoidal rule in normalized coordinates",
        },
        "dominant_height_operator": {
            "scientific_definition": "continuous upper-DBH-tail functional with prescribed mass",
            "target_stems_ha": float(dominant["selected_stems"]),
            "threshold_dbh_cm": simulated["dominant_threshold_dbh"],
            "dominant_height_m": simulated["H0_continuous"],
        },
        "observables": rows,
        "methodological_warning": (
            "The dependence parameter is constrained by the observed initial dominant-height contrast "
            "within the selected Gaussian family. It is not a statistical estimate from individual-tree records."
        ),
    }
    return manifest, rows, density_rows


def write_manifest(output_dir: str | Path) -> dict[str, Path]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    manifest, rows, density_rows = build_manifest()
    paths = {
        "json": output / "initial_condition_manifest.json",
        "summary_csv": output / "initial_condition_summary.csv",
        "markdown": output / "initial_condition_summary.md",
        "density_csv": output / "initial_joint_density.csv",
    }
    paths["json"].write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    with paths["summary_csv"].open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=SUMMARY_FIELDS)
        writer.writeheader(); writer.writerows(rows)
    with paths["density_csv"].open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=DENSITY_FIELDS)
        writer.writeheader(); writer.writerows(density_rows)
    initial = manifest["initial_condition"]
    support = manifest["numerical_support"]
    lines = [
        "# Initial condition of the manuscript simulation", "",
        "## Scientific status", "",
        manifest["methodological_warning"], "",
        f"Future empirical replacement: {initial['future_replacement']}.", "",
        "## Requested construction", "",
        f"- Family: {initial['family']};",
        f"- initial age: {initial['initial_age_years']:.1f} years;",
        f"- target mass: {initial['mass_target_trees_ha']:.2f} trees/ha;",
        f"- requested height-DBH correlation: {initial['requested_height_dbh_correlation']:.10f};",
        f"- effective height-DBH correlation: {initial['effective_height_dbh_correlation']:.10f};",
        f"- grid: {support['grid_shape'][0]} x {support['grid_shape'][1]};",
        f"- quadrature: {support['quadrature']}.", "",
        "## Initial observables", "",
        "| Observable | Simulated | Observed or derived | Residual | Unit | Status |",
        "|:---|---:|---:|---:|:---|:---|",
    ]
    for row in rows:
        target = row["observed_or_derived_value"]
        residual = row["residual"]
        lines.append(
            f"| {row['observable']} | {row['simulated_value']:.10g} | "
            f"{'' if target == '' else f'{target:.10g}'} | "
            f"{'' if residual == '' else f'{residual:+.6g}'} | "
            f"{row['unit']} | {row['status']} |"
        )
    lines.extend(["", "## Reproducibility", "", f"- Git branch: `{manifest['git']['branch']}`;", f"- Git commit: `{manifest['git']['commit']}`."])
    paths["markdown"].write_text("\n".join(lines) + "\n", encoding="utf-8")
    return paths


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default="outputs/article_initial_condition")
    args = parser.parse_args()
    for name, path in write_manifest(args.output_dir).items():
        print(f"{name}: {path.resolve()}")


if __name__ == "__main__":
    main()
