# SPDX-License-Identifier: LGPL-3.0-or-later
"""Article-specific initial states assembled with a Gaussian copula.

The marginal height and DBH densities are calibrated on the numerical grid.
Dependence is then introduced through a Gaussian copula and the resulting joint
density is normalised to the target stand density. This module is intentionally
kept in ``simulations.article`` while the reconstruction remains specific to
the manuscript.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

import numpy as np
from scipy.optimize import least_squares
from scipy.special import ndtri

from pydynamicforest.observation_operators import (
    basal_area_consistent,
    continuous_dominant_height_details,
    joint_moment_summary,
    quadratic_mean_dbh,
)
from pydynamicforest.types import Parameters


@dataclass(frozen=True)
class CopulaInitialStateResult:
    """A reconstructed initial density and its numerical diagnostics."""

    density: np.ndarray
    requested_rho: float
    effective_rho: float
    height_location_m: float
    height_kernel_sd_m: float
    reconstructed_height_sd_m: float
    dbh_location_m: float
    dbh_kernel_sd_m: float
    target_observables: dict[str, float]
    reconstructed_observables: dict[str, float]
    absolute_errors: dict[str, float]
    relative_errors: dict[str, float]
    selected_stems_per_ha: float
    dominant_dbh_threshold_m: float
    marginal_calibration_success: bool
    marginal_calibration_message: str


def _trapezoidal_weights(nodes: np.ndarray) -> np.ndarray:
    values = np.asarray(nodes, dtype=float)
    if values.ndim != 1 or values.size < 2:
        raise ValueError("nodes must be a one-dimensional array of size >= 2.")
    spacing = np.diff(values)
    if not np.all(spacing > 0.0):
        raise ValueError("nodes must be strictly increasing.")
    if not np.allclose(spacing, spacing[0], rtol=1.0e-12, atol=1.0e-15):
        raise ValueError("the article reconstruction requires a uniform grid.")
    weights = np.full(values.size, spacing[0], dtype=float)
    weights[[0, -1]] *= 0.5
    return weights


def _normalised_gaussian_marginal(
    nodes: np.ndarray,
    location: float,
    scale: float,
) -> np.ndarray:
    if not np.isfinite(location):
        raise ValueError("marginal location must be finite.")
    if not np.isfinite(scale) or scale <= 0.0:
        raise ValueError("marginal scale must be finite and strictly positive.")
    z = (np.asarray(nodes, dtype=float) - location) / scale
    values = np.exp(-0.5 * z * z)
    integral = float(np.sum(_trapezoidal_weights(nodes) * values))
    if not np.isfinite(integral) or integral <= 0.0:
        raise ValueError("marginal kernel has zero or non-finite mass.")
    return values / integral


def _cdf_from_density(nodes: np.ndarray, density: np.ndarray) -> np.ndarray:
    values = np.asarray(density, dtype=float)
    x = np.asarray(nodes, dtype=float)
    if values.shape != x.shape:
        raise ValueError("density and nodes must have the same shape.")
    increments = 0.5 * (values[:-1] + values[1:]) * np.diff(x)
    cdf = np.concatenate(([0.0], np.cumsum(increments)))
    cdf /= cdf[-1]
    return np.clip(cdf, 1.0e-12, 1.0 - 1.0e-12)


def gaussian_copula_density(
    height_cdf: np.ndarray,
    dbh_cdf: np.ndarray,
    rho: float,
) -> np.ndarray:
    """Return Gaussian-copula density values on a tensor-product grid."""
    if not np.isfinite(rho) or abs(rho) >= 1.0:
        raise ValueError("copula rho must be finite and strictly between -1 and 1.")
    u = np.asarray(height_cdf, dtype=float)
    v = np.asarray(dbh_cdf, dtype=float)
    if u.ndim != 1 or v.ndim != 1:
        raise ValueError("copula marginal CDF values must be one-dimensional.")
    if rho == 0.0:
        return np.ones((u.size, v.size), dtype=float)
    z_h = ndtri(np.clip(u, 1.0e-12, 1.0 - 1.0e-12))[:, None]
    z_d = ndtri(np.clip(v, 1.0e-12, 1.0 - 1.0e-12))[None, :]
    rho2 = rho * rho
    exponent = (
        2.0 * rho * z_h * z_d - rho2 * (z_h * z_h + z_d * z_d)
    ) / (2.0 * (1.0 - rho2))
    return np.exp(exponent) / np.sqrt(1.0 - rho2)


def _joint_density(
    *,
    p: Parameters,
    target_stems: float,
    height_location_m: float,
    height_kernel_sd_m: float,
    dbh_location_m: float,
    dbh_kernel_sd_m: float,
    rho: float,
) -> np.ndarray:
    if not np.isfinite(target_stems) or target_stems <= 0.0:
        raise ValueError("target_stems must be finite and strictly positive.")
    grid = p.numerics.grid
    scales = p.model.physical_scales
    height_nodes_m = grid.x * scales.height_scale
    dbh_nodes_m = grid.y * scales.dbh_scale

    height_marginal = _normalised_gaussian_marginal(
        height_nodes_m, height_location_m, height_kernel_sd_m
    )
    dbh_marginal = _normalised_gaussian_marginal(
        dbh_nodes_m, dbh_location_m, dbh_kernel_sd_m
    )
    copula = gaussian_copula_density(
        _cdf_from_density(height_nodes_m, height_marginal),
        _cdf_from_density(dbh_nodes_m, dbh_marginal),
        rho,
    )

    # Convert physical marginal densities to densities per normalised coordinate.
    density = (
        scales.height_scale
        * scales.dbh_scale
        * height_marginal[:, None]
        * dbh_marginal[None, :]
        * copula
    )
    weights = np.outer(
        _trapezoidal_weights(grid.x),
        _trapezoidal_weights(grid.y),
    )
    mass = float(np.sum(weights * density))
    if not np.isfinite(mass) or mass <= 0.0:
        raise ValueError("joint copula density has zero or non-finite mass.")
    result = target_stems * density / mass
    if not np.all(np.isfinite(result)) or np.any(result < 0.0):
        raise ValueError("joint copula density must be finite and non-negative.")
    return result


def evaluate_initial_state(
    density: np.ndarray,
    p: Parameters,
    *,
    target_dominant_stems_per_ha: float = 100.0,
) -> tuple[dict[str, float], dict[str, float]]:
    """Evaluate one initial density with the article observation operators."""
    moments = joint_moment_summary(density, p)
    dominant = continuous_dominant_height_details(
        density,
        p,
        target_stems_per_ha=target_dominant_stems_per_ha,
    )
    dbh_variance_cm2 = 10000.0 * moments["dbh_variance_m2"]
    observables = {
        "N": moments["stand_density"],
        "G": basal_area_consistent(density, p),
        "Dm": 100.0 * moments["mean_dbh_m"],
        "Dg": 100.0 * quadratic_mean_dbh(density, p, unit="m"),
        "sigma_D": float(np.sqrt(max(0.0, dbh_variance_cm2))),
        "Hm": moments["mean_height"],
        "H0": dominant["dominant_height"],
        "H0_minus_Hm": dominant["dominant_height"] - moments["mean_height"],
        "height_sd": float(np.sqrt(max(0.0, moments["height_variance_m2"]))),
        "effective_rho": moments["height_dbh_correlation"],
    }
    details = {
        "selected_stems_per_ha": dominant["selected_stems"],
        "dominant_dbh_threshold_m": dominant["threshold_dbh"],
    }
    return observables, details


def _required_targets(observation: Mapping[str, float | None]) -> dict[str, float]:
    keys = ("N", "G", "Dm", "Dg", "sigma_D", "Hm", "H0", "H0_minus_Hm")
    missing = [key for key in keys if observation.get(key) is None]
    if missing:
        raise ValueError(f"initial observation is missing required values: {missing}")
    return {key: float(observation[key]) for key in keys}


def build_gaussian_copula_initial_state(
    *,
    observation: Mapping[str, float | None],
    p: Parameters,
    height_kernel_sd_m: float,
    copula_rho: float,
    target_dominant_stems_per_ha: float = 100.0,
) -> CopulaInitialStateResult:
    """Build one discretely calibrated Gaussian-copula initial state.

    ``height_kernel_sd_m`` and ``copula_rho`` are sensitivity parameters. The
    height location, DBH location, and DBH kernel scale are calibrated after
    copula assembly so that the reconstructed mean height, mean DBH, and DBH
    standard deviation match their stand-level targets on the numerical grid.
    """
    targets = _required_targets(observation)
    if not np.isfinite(height_kernel_sd_m) or height_kernel_sd_m <= 0.0:
        raise ValueError("height_kernel_sd_m must be finite and positive.")
    if not np.isfinite(copula_rho) or abs(copula_rho) >= 1.0:
        raise ValueError("copula_rho must be finite and strictly between -1 and 1.")

    scales = p.model.physical_scales
    initial = np.array(
        [
            targets["Hm"],
            targets["Dm"] / 100.0,
            np.log(targets["sigma_D"] / 100.0),
        ],
        dtype=float,
    )
    lower = np.array([0.0, 0.0, np.log(1.0e-4)], dtype=float)
    upper = np.array(
        [scales.height_scale, scales.dbh_scale, np.log(scales.dbh_scale)],
        dtype=float,
    )

    def residual(vector: np.ndarray) -> np.ndarray:
        density = _joint_density(
            p=p,
            target_stems=targets["N"],
            height_location_m=float(vector[0]),
            height_kernel_sd_m=height_kernel_sd_m,
            dbh_location_m=float(vector[1]),
            dbh_kernel_sd_m=float(np.exp(vector[2])),
            rho=copula_rho,
        )
        values, _ = evaluate_initial_state(
            density,
            p,
            target_dominant_stems_per_ha=target_dominant_stems_per_ha,
        )
        return np.array(
            [
                (values["Hm"] - targets["Hm"]) / 0.01,
                (values["Dm"] - targets["Dm"]) / 0.01,
                (values["sigma_D"] - targets["sigma_D"]) / 0.02,
            ],
            dtype=float,
        )

    fit = least_squares(
        residual,
        initial,
        bounds=(lower, upper),
        xtol=1.0e-11,
        ftol=1.0e-11,
        gtol=1.0e-11,
        max_nfev=400,
    )
    height_location_m = float(fit.x[0])
    dbh_location_m = float(fit.x[1])
    dbh_kernel_sd_m = float(np.exp(fit.x[2]))
    density = _joint_density(
        p=p,
        target_stems=targets["N"],
        height_location_m=height_location_m,
        height_kernel_sd_m=height_kernel_sd_m,
        dbh_location_m=dbh_location_m,
        dbh_kernel_sd_m=dbh_kernel_sd_m,
        rho=copula_rho,
    )
    reconstructed, details = evaluate_initial_state(
        density,
        p,
        target_dominant_stems_per_ha=target_dominant_stems_per_ha,
    )
    absolute_errors = {
        key: reconstructed[key] - targets[key]
        for key in targets
    }
    relative_errors = {
        key: absolute_errors[key] / targets[key]
        if targets[key] != 0.0 else float("nan")
        for key in targets
    }
    return CopulaInitialStateResult(
        density=density,
        requested_rho=float(copula_rho),
        effective_rho=float(reconstructed["effective_rho"]),
        height_location_m=height_location_m,
        height_kernel_sd_m=float(height_kernel_sd_m),
        reconstructed_height_sd_m=float(reconstructed["height_sd"]),
        dbh_location_m=dbh_location_m,
        dbh_kernel_sd_m=dbh_kernel_sd_m,
        target_observables=targets,
        reconstructed_observables=reconstructed,
        absolute_errors=absolute_errors,
        relative_errors=relative_errors,
        selected_stems_per_ha=float(details["selected_stems_per_ha"]),
        dominant_dbh_threshold_m=float(details["dominant_dbh_threshold_m"]),
        marginal_calibration_success=bool(fit.success),
        marginal_calibration_message=str(fit.message),
    )
