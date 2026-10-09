# SPDX-License-Identifier: LGPL-3.0-or-later
"""Diagnose the unchanged patrimonial initial condition against GIS Coop data."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np

from pydynamicforest.diagnostics import (
    legacy_top_height,
    proportional_top_height,
    top_height,
)
from pydynamicforest.initial_conditions import build_initial_state
from pydynamicforest.numerics import product_trapezoidal_weights
from pydynamicforest.observation_operators import (
    basal_area_consistent,
    continuous_dominant_height_details,
    mean_height,
    physical_dbh_nodes,
    physical_height_nodes,
    quadratic_mean_dbh,
    stand_density,
)
from simulations.article_submission_legacy.context import build_context
from simulations.article_submission_legacy.initial_condition import build_initial_condition
from simulations.article_submission_legacy.parameters import build_parameters


# Third DOUGLAS ECOUVES series in data_final_simu.csv, age 18.
# Dm is the reported mean DBH. Dg and sigma_D are derived from N, G, and Dm.
INITIAL_OBSERVATIONS = {
    "N": 1924.342105,
    "G": 21.6052,
    "Dm_cm": 11.69312727,
    "Hm": 9.6105,
    "H0": 11.65988237,
}

SUMMARY_FIELDS = [
    "age",
    "stand_density",
    "observed_N",
    "residual_N",
    "basal_area",
    "observed_G",
    "residual_G",
    "mean_dbh_cm",
    "gaussian_dbh_center_cm",
    "observed_mean_dbh_cm",
    "residual_mean_dbh_cm",
    "quadratic_mean_dbh_cm",
    "observed_quadratic_mean_dbh_cm",
    "residual_quadratic_mean_dbh_cm",
    "dbh_variance_cm2",
    "observed_implied_dbh_variance_cm2",
    "residual_dbh_variance_cm2",
    "dbh_standard_deviation_cm",
    "observed_implied_dbh_standard_deviation_cm",
    "residual_dbh_standard_deviation_cm",
    "mean_height",
    "gaussian_height_center_m",
    "observed_Hm",
    "residual_Hm",
    "height_variance_m2",
    "height_standard_deviation_m",
    "height_dbh_covariance_m2",
    "height_dbh_correlation",
    "current_top_height",
    "legacy_top_height",
    "proportional_top_height",
    "continuous_top_height",
    "observed_H0",
    "residual_H0_continuous",
    "continuous_threshold_dbh_cm",
    "continuous_selected_stems",
    "continuous_H0_minus_Hm",
    "observed_H0_minus_Hm",
    "quadratic_identity_residual_cm2",
    "basal_area_identity_residual",
]


def _observed_derived_diameter_moments() -> dict[str, float]:
    """Derive observed Dg and diameter spread from N, G, and reported Dm."""

    N = INITIAL_OBSERVATIONS["N"]
    G = INITIAL_OBSERVATIONS["G"]
    Dm_cm = INITIAL_OBSERVATIONS["Dm_cm"]
    Dg_cm = 100.0 * np.sqrt(4.0 * G / (np.pi * N))
    variance_cm2 = Dg_cm**2 - Dm_cm**2
    if variance_cm2 < 0.0:
        raise ValueError("Observed N, G, and Dm imply a negative DBH variance.")
    return {
        "Dg_cm": float(Dg_cm),
        "variance_cm2": float(variance_cm2),
        "standard_deviation_cm": float(np.sqrt(variance_cm2)),
    }


def _weighted_moments(U: np.ndarray, p) -> dict[str, float]:
    """Return quadrature-consistent first and second joint moments."""

    weights = product_trapezoidal_weights(p)
    total = stand_density(U, p)
    height = physical_height_nodes(p)[:, None]
    dbh_m = physical_dbh_nodes(p, unit="m")[None, :]

    mean_h = float(np.sum(weights * height * U) / total)
    mean_d_m = float(np.sum(weights * dbh_m * U) / total)
    centered_h = height - mean_h
    centered_d = dbh_m - mean_d_m
    var_h = float(np.sum(weights * centered_h**2 * U) / total)
    var_d_m2 = float(np.sum(weights * centered_d**2 * U) / total)
    covariance = float(np.sum(weights * centered_h * centered_d * U) / total)
    denominator = np.sqrt(var_h * var_d_m2)
    correlation = float("nan") if denominator <= 0.0 else covariance / denominator

    return {
        "mean_height": mean_h,
        "mean_dbh_m": mean_d_m,
        "height_variance_m2": var_h,
        "dbh_variance_m2": var_d_m2,
        "height_dbh_covariance_m2": covariance,
        "height_dbh_correlation": correlation,
    }


def diagnose_initial_condition() -> dict[str, float]:
    """Build and diagnose the unchanged patrimonial initial state."""

    x0 = build_initial_condition()
    p = build_parameters()
    c = build_context()
    state = build_initial_state(x0, p, c)
    U = state.U

    observed_diameter = _observed_derived_diameter_moments()
    moments = _weighted_moments(U, p)
    N = stand_density(U, p)
    G = basal_area_consistent(U, p)
    Dg_cm = quadratic_mean_dbh(U, p, unit="cm")
    Hm = mean_height(U, p)
    continuous = continuous_dominant_height_details(U, p)
    H0_cont = float(continuous["dominant_height"])

    distribution = x0.distribution_parameters
    gaussian_h_center = float(distribution["h0_physical"])
    gaussian_d_center_cm = 100.0 * float(distribution["d0_physical"])
    mean_d_cm = 100.0 * moments["mean_dbh_m"]
    var_d_cm2 = 10000.0 * moments["dbh_variance_m2"]
    sd_d_cm = float(np.sqrt(var_d_cm2))

    return {
        "age": float(state.age),
        "stand_density": N,
        "observed_N": INITIAL_OBSERVATIONS["N"],
        "residual_N": N - INITIAL_OBSERVATIONS["N"],
        "basal_area": G,
        "observed_G": INITIAL_OBSERVATIONS["G"],
        "residual_G": G - INITIAL_OBSERVATIONS["G"],
        "mean_dbh_cm": mean_d_cm,
        "gaussian_dbh_center_cm": gaussian_d_center_cm,
        "observed_mean_dbh_cm": INITIAL_OBSERVATIONS["Dm_cm"],
        "residual_mean_dbh_cm": mean_d_cm - INITIAL_OBSERVATIONS["Dm_cm"],
        "quadratic_mean_dbh_cm": Dg_cm,
        "observed_quadratic_mean_dbh_cm": observed_diameter["Dg_cm"],
        "residual_quadratic_mean_dbh_cm": Dg_cm - observed_diameter["Dg_cm"],
        "dbh_variance_cm2": var_d_cm2,
        "observed_implied_dbh_variance_cm2": observed_diameter["variance_cm2"],
        "residual_dbh_variance_cm2": var_d_cm2 - observed_diameter["variance_cm2"],
        "dbh_standard_deviation_cm": sd_d_cm,
        "observed_implied_dbh_standard_deviation_cm": observed_diameter["standard_deviation_cm"],
        "residual_dbh_standard_deviation_cm": sd_d_cm - observed_diameter["standard_deviation_cm"],
        "mean_height": Hm,
        "gaussian_height_center_m": gaussian_h_center,
        "observed_Hm": INITIAL_OBSERVATIONS["Hm"],
        "residual_Hm": Hm - INITIAL_OBSERVATIONS["Hm"],
        "height_variance_m2": moments["height_variance_m2"],
        "height_standard_deviation_m": float(np.sqrt(moments["height_variance_m2"])),
        "height_dbh_covariance_m2": moments["height_dbh_covariance_m2"],
        "height_dbh_correlation": moments["height_dbh_correlation"],
        "current_top_height": top_height(U, p),
        "legacy_top_height": legacy_top_height(U, p),
        "proportional_top_height": proportional_top_height(U, p),
        "continuous_top_height": H0_cont,
        "observed_H0": INITIAL_OBSERVATIONS["H0"],
        "residual_H0_continuous": H0_cont - INITIAL_OBSERVATIONS["H0"],
        "continuous_threshold_dbh_cm": 100.0 * float(continuous["threshold_dbh"]),
        "continuous_selected_stems": float(continuous["selected_stems"]),
        "continuous_H0_minus_Hm": H0_cont - Hm,
        "observed_H0_minus_Hm": INITIAL_OBSERVATIONS["H0"] - INITIAL_OBSERVATIONS["Hm"],
        "quadratic_identity_residual_cm2": Dg_cm**2 - (mean_d_cm**2 + var_d_cm2),
        "basal_area_identity_residual": G - 0.25 * np.pi * N * (Dg_cm / 100.0) ** 2,
    }


def interpretation(summary: dict[str, float]) -> dict:
    """Return explicit conclusions without recalibrating the patrimonial state."""

    return {
        "scenario_status": "patrimonial initial condition unchanged",
        "source_context": (
            "Age-18 values are from the selected unthinned DOUGLAS ECOUVES "
            "series in the GIS Coop extraction data_final_simu.csv."
        ),
        "observables_present": ["N", "G", "Dm", "Dg", "sigma_D", "Hm", "H0"],
        "diameter_conclusion": (
            "The patrimonial initial condition closely reproduces observed mean DBH, "
            "derived quadratic mean DBH, and implied DBH spread."
        ),
        "joint_structure_conclusion": (
            "The effective initial height-DBH correlation is nearly zero, so continuous "
            "dominant height nearly equals mean height and misses the observed H0-Hm gap."
        ),
        "identifiability_warning": (
            "Aggregate stand observables do not identify a unique joint initial "
            "height-DBH distribution or correlation parameter."
        ),
        "key_residuals": {
            "Dm_cm": summary["residual_mean_dbh_cm"],
            "Dg_cm": summary["residual_quadratic_mean_dbh_cm"],
            "sigma_D_cm": summary["residual_dbh_standard_deviation_cm"],
            "Hm_m": summary["residual_Hm"],
            "H0_continuous_m": summary["residual_H0_continuous"],
            "H0_minus_Hm_m": summary["continuous_H0_minus_Hm"] - summary["observed_H0_minus_Hm"],
        },
    }


def run_diagnostic(output_dir: str | Path) -> dict:
    """Write CSV, JSON, and Markdown diagnostics for the initial condition."""

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    summary = diagnose_initial_condition()
    notes = interpretation(summary)

    csv_path = output_path / "initial_condition_diagnostic.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=SUMMARY_FIELDS)
        writer.writeheader()
        writer.writerow(summary)

    json_path = output_path / "initial_condition_diagnostic.json"
    json_path.write_text(
        json.dumps({"summary": summary, "interpretation": notes}, indent=2) + "\n",
        encoding="utf-8",
    )

    markdown_path = output_path / "initial_condition_diagnostic.md"
    markdown = f"""# Patrimonial initial-condition diagnostic

The patrimonial scenario and its initial condition are left unchanged.

## Stand-level observables and derived diameter moments

| Observable | Simulated | Observed or derived | Residual |
|---|---:|---:|---:|
| N (trees/ha) | {summary['stand_density']:.6f} | {summary['observed_N']:.6f} | {summary['residual_N']:+.6f} |
| G (m2/ha) | {summary['basal_area']:.6f} | {summary['observed_G']:.6f} | {summary['residual_G']:+.6f} |
| Dm (cm) | {summary['mean_dbh_cm']:.6f} | {summary['observed_mean_dbh_cm']:.6f} | {summary['residual_mean_dbh_cm']:+.6f} |
| Dg (cm) | {summary['quadratic_mean_dbh_cm']:.6f} | {summary['observed_quadratic_mean_dbh_cm']:.6f} | {summary['residual_quadratic_mean_dbh_cm']:+.6f} |
| sigma_D (cm) | {summary['dbh_standard_deviation_cm']:.6f} | {summary['observed_implied_dbh_standard_deviation_cm']:.6f} | {summary['residual_dbh_standard_deviation_cm']:+.6f} |
| Hm (m) | {summary['mean_height']:.6f} | {summary['observed_Hm']:.6f} | {summary['residual_Hm']:+.6f} |
| H0 continuous (m) | {summary['continuous_top_height']:.6f} | {summary['observed_H0']:.6f} | {summary['residual_H0_continuous']:+.6f} |

## Effective joint moments

- Gaussian DBH center: `{summary['gaussian_dbh_center_cm']:.9f} cm`;
- effective mean DBH: `{summary['mean_dbh_cm']:.9f} cm`;
- effective quadratic mean DBH: `{summary['quadratic_mean_dbh_cm']:.9f} cm`;
- effective DBH variance: `{summary['dbh_variance_cm2']:.9f} cm2`;
- effective mean height: `{summary['mean_height']:.9f} m`;
- effective height variance: `{summary['height_variance_m2']:.9f} m2`;
- effective height-DBH covariance: `{summary['height_dbh_covariance_m2']:.12e} m2`;
- effective height-DBH correlation: `{summary['height_dbh_correlation']:.12e}`.

## Dominant-height operators

- current: `{summary['current_top_height']:.9f} m`;
- legacy: `{summary['legacy_top_height']:.9f} m`;
- proportional: `{summary['proportional_top_height']:.9f} m`;
- continuous: `{summary['continuous_top_height']:.9f} m`;
- continuous d100: `{summary['continuous_threshold_dbh_cm']:.9f} cm`.

## Interpretation

- The patrimonial initial condition closely reproduces N, G, Dm, derived Dg, implied DBH spread, and Hm.
- Its effective height-DBH correlation is nearly zero.
- Consequently, continuous H0 nearly equals Hm and misses the observed initial H0-Hm gap.
- Aggregate observables do not identify a unique joint distribution or correlation parameter.
- This diagnostic does not recalibrate or modify the patrimonial initial condition.
"""
    markdown_path.write_text(markdown, encoding="utf-8")

    return {
        "summary": summary,
        "interpretation": notes,
        "csv_path": csv_path,
        "json_path": json_path,
        "markdown_path": markdown_path,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default="outputs/initial_condition_diagnostic")
    args = parser.parse_args()
    result = run_diagnostic(args.output_dir)
    print(f"CSV: {result['csv_path'].resolve()}")
    print(f"JSON: {result['json_path'].resolve()}")
    print(f"Markdown: {result['markdown_path'].resolve()}")


if __name__ == "__main__":
    main()
