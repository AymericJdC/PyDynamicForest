# SPDX-License-Identifier: LGPL-3.0-or-later
"""Sensitivity of the initial state to height-DBH Gaussian correlation.

This experiment does not modify the patrimonial initial condition. It builds a
separate family of correlated bivariate Gaussian densities with the same
analytical location and scale parameters, normalizes every density to the same
stem number, and reports effective moments after truncation and discretization.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np

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
from simulations.article_submission_legacy.diagnose_initial_condition import (
    INITIAL_OBSERVATIONS,
    _observed_derived_diameter_moments,
)
from simulations.article_submission_legacy.initial_condition import build_initial_condition
from simulations.article_submission_legacy.parameters import build_parameters


DEFAULT_RHOS = (-0.75, -0.50, -0.25, 0.0, 0.25, 0.50, 0.75, 0.90)
CSV_FIELDS = [
    "rho_requested",
    "stand_density",
    "basal_area",
    "mean_dbh_cm",
    "quadratic_mean_dbh_cm",
    "dbh_standard_deviation_cm",
    "mean_height",
    "height_standard_deviation_m",
    "height_dbh_covariance_m2",
    "height_dbh_correlation_effective",
    "continuous_top_height",
    "continuous_H0_minus_Hm",
    "continuous_threshold_dbh_cm",
    "continuous_selected_stems",
    "residual_N",
    "residual_G",
    "residual_Dm_cm",
    "residual_Dg_cm",
    "residual_sigma_D_cm",
    "residual_Hm",
    "residual_H0",
]


def _validate_rho(rho: float) -> float:
    rho = float(rho)
    if not np.isfinite(rho) or abs(rho) >= 1.0:
        raise ValueError("rho must be finite and strictly between -1 and 1.")
    return rho


def build_correlated_initial_density(rho: float, p=None) -> np.ndarray:
    """Build one normalized correlated Gaussian on the patrimonial grid."""

    rho = _validate_rho(rho)
    if p is None:
        p = build_parameters()
    x0 = build_initial_condition()
    pars = x0.distribution_parameters

    height_m = physical_height_nodes(p)[:, None]
    dbh_m = physical_dbh_nodes(p, unit="m")[None, :]
    z_h = (height_m - float(pars["h0_physical"])) / float(
        pars["sigma_h_physical"]
    )
    z_d = (dbh_m - float(pars["d0_physical"])) / float(
        pars["sigma_d_physical"]
    )
    exponent = -0.5 * (z_h**2 - 2.0 * rho * z_h * z_d + z_d**2) / (
        1.0 - rho**2
    )
    raw = np.exp(exponent)
    weights = product_trapezoidal_weights(p)
    normalization = float(np.sum(weights * raw))
    if not np.isfinite(normalization) or normalization <= 0.0:
        raise ValueError("The correlated initial density cannot be normalized.")
    return float(x0.mass_target) * raw / normalization


def _joint_moments(U: np.ndarray, p) -> dict[str, float]:
    weights = product_trapezoidal_weights(p)
    total = stand_density(U, p)
    height = physical_height_nodes(p)[:, None]
    dbh = physical_dbh_nodes(p, unit="m")[None, :]
    mean_h = float(np.sum(weights * height * U) / total)
    mean_d = float(np.sum(weights * dbh * U) / total)
    centered_h = height - mean_h
    centered_d = dbh - mean_d
    var_h = float(np.sum(weights * centered_h**2 * U) / total)
    var_d = float(np.sum(weights * centered_d**2 * U) / total)
    covariance = float(np.sum(weights * centered_h * centered_d * U) / total)
    denominator = np.sqrt(var_h * var_d)
    correlation = float("nan") if denominator <= 0.0 else covariance / denominator
    return {
        "mean_height": mean_h,
        "mean_dbh_m": mean_d,
        "height_variance_m2": var_h,
        "dbh_variance_m2": var_d,
        "covariance_m2": covariance,
        "correlation": correlation,
    }


def evaluate_rho(rho: float, p=None) -> dict[str, float]:
    """Evaluate observables for one requested analytical correlation."""

    if p is None:
        p = build_parameters()
    U = build_correlated_initial_density(rho, p)
    moments = _joint_moments(U, p)
    observed_diameter = _observed_derived_diameter_moments()

    N = stand_density(U, p)
    G = basal_area_consistent(U, p)
    Dm_cm = 100.0 * moments["mean_dbh_m"]
    Dg_cm = quadratic_mean_dbh(U, p, unit="cm")
    sigma_D_cm = 100.0 * np.sqrt(moments["dbh_variance_m2"])
    Hm = mean_height(U, p)
    H0 = continuous_dominant_height_details(U, p)

    return {
        "rho_requested": float(rho),
        "stand_density": N,
        "basal_area": G,
        "mean_dbh_cm": Dm_cm,
        "quadratic_mean_dbh_cm": Dg_cm,
        "dbh_standard_deviation_cm": sigma_D_cm,
        "mean_height": Hm,
        "height_standard_deviation_m": np.sqrt(moments["height_variance_m2"]),
        "height_dbh_covariance_m2": moments["covariance_m2"],
        "height_dbh_correlation_effective": moments["correlation"],
        "continuous_top_height": H0["dominant_height"],
        "continuous_H0_minus_Hm": H0["dominant_height"] - Hm,
        "continuous_threshold_dbh_cm": 100.0 * H0["threshold_dbh"],
        "continuous_selected_stems": H0["selected_stems"],
        "residual_N": N - INITIAL_OBSERVATIONS["N"],
        "residual_G": G - INITIAL_OBSERVATIONS["G"],
        "residual_Dm_cm": Dm_cm - INITIAL_OBSERVATIONS["Dm_cm"],
        "residual_Dg_cm": Dg_cm - observed_diameter["Dg_cm"],
        "residual_sigma_D_cm": sigma_D_cm - observed_diameter["standard_deviation_cm"],
        "residual_Hm": Hm - INITIAL_OBSERVATIONS["Hm"],
        "residual_H0": H0["dominant_height"] - INITIAL_OBSERVATIONS["H0"],
    }


def evaluate_rhos(rhos=DEFAULT_RHOS) -> list[dict[str, float]]:
    """Evaluate an ordered sequence of requested correlations."""

    p = build_parameters()
    return [evaluate_rho(rho, p) for rho in rhos]


def interpolate_target_rho(rows: list[dict[str, float]]) -> dict | None:
    """Linearly bracket the requested rho whose H0 matches the observation.

    This is a descriptive interpolation within the chosen Gaussian family, not
    a statistical estimate of the true stand correlation.
    """

    target = INITIAL_OBSERVATIONS["H0"]
    ordered = sorted(rows, key=lambda row: row["rho_requested"])
    for left, right in zip(ordered, ordered[1:]):
        y0 = left["continuous_top_height"] - target
        y1 = right["continuous_top_height"] - target
        if y0 == 0.0:
            return {"rho_requested_interpolated": left["rho_requested"], "bracket": [left["rho_requested"], left["rho_requested"]]}
        if y0 * y1 <= 0.0 and y1 != y0:
            fraction = -y0 / (y1 - y0)
            rho = left["rho_requested"] + fraction * (
                right["rho_requested"] - left["rho_requested"]
            )
            return {
                "rho_requested_interpolated": float(rho),
                "bracket": [left["rho_requested"], right["rho_requested"]],
                "warning": "descriptive interpolation, not statistical estimation",
            }
    return None


def run_sensitivity(output_dir: str | Path, rhos=DEFAULT_RHOS) -> dict:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    rows = evaluate_rhos(rhos)
    target = interpolate_target_rho(rows)

    csv_path = output_path / "initial_correlation_sensitivity.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    json_path = output_path / "initial_correlation_sensitivity.json"
    payload = {
        "scenario_status": "separate sensitivity experiment; patrimonial scenario unchanged",
        "analytical_parameters_held_fixed": [
            "mass target", "height location", "DBH location", "height scale", "DBH scale"
        ],
        "effective_marginal_moments": (
            "reported after truncation, discretization, and quadrature normalization"
        ),
        "observed_target_H0": INITIAL_OBSERVATIONS["H0"],
        "target_rho_interpolation": target,
        "identifiability_warning": (
            "A matching rho within this Gaussian family is not a statistical estimate "
            "of the true initial height-DBH correlation."
        ),
        "rows": rows,
    }
    json_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    markdown_path = output_path / "initial_correlation_sensitivity.md"
    lines = [
        "# Initial height-DBH correlation sensitivity",
        "",
        "The patrimonial initial condition is unchanged. Each row is a separate correlated Gaussian experiment.",
        "",
        "| rho requested | rho effective | N | G | Dm | Dg | sigma_D | Hm | H0 continuous | H0-Hm |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            "| {rho_requested:.3f} | {height_dbh_correlation_effective:.6f} | "
            "{stand_density:.3f} | {basal_area:.4f} | {mean_dbh_cm:.4f} | "
            "{quadratic_mean_dbh_cm:.4f} | {dbh_standard_deviation_cm:.4f} | "
            "{mean_height:.4f} | {continuous_top_height:.4f} | "
            "{continuous_H0_minus_Hm:.4f} |".format(**row)
        )
    lines.extend([
        "",
        "## Interpretation limits",
        "",
        "- Requested rho is the analytical Gaussian parameter; effective rho is computed on the truncated, discretized, normalized state.",
        "- Marginal moments may vary slightly with rho because the Gaussian is truncated by the finite size domain.",
        "- Matching observed H0 within this family does not identify the true joint distribution.",
    ])
    if target is not None:
        lines.extend([
            "",
            "## Descriptive target interpolation",
            "",
            f"Interpolated requested rho for observed H0: `{target['rho_requested_interpolated']:.6f}`.",
            "This value is descriptive only and is not a statistical estimate.",
        ])
    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    return {"rows": rows, "target": target, "csv_path": csv_path, "json_path": json_path, "markdown_path": markdown_path}


def _parse_rhos(value: str) -> tuple[float, ...]:
    return tuple(_validate_rho(item.strip()) for item in value.split(",") if item.strip())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default="outputs/initial_correlation_sensitivity")
    parser.add_argument(
        "--rhos",
        type=_parse_rhos,
        default=DEFAULT_RHOS,
        help="Comma-separated requested Gaussian correlations.",
    )
    args = parser.parse_args()
    result = run_sensitivity(args.output_dir, args.rhos)
    print(f"CSV: {result['csv_path'].resolve()}")
    print(f"JSON: {result['json_path'].resolve()}")
    print(f"Markdown: {result['markdown_path'].resolve()}")


if __name__ == "__main__":
    main()
