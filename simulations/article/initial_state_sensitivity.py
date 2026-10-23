# SPDX-License-Identifier: LGPL-3.0-or-later
"""Sensitivity analysis for article initial states assembled by copula."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

from scipy.optimize import brentq

from pydynamicforest.types import Parameters
from simulations.article.copula_initial_condition import (
    CopulaInitialStateResult,
    build_gaussian_copula_initial_state,
)


DEFAULT_RHO_VALUES = (0.50, 0.60, 0.70, 0.80, 0.85, 0.90, 0.95)


@dataclass(frozen=True)
class SensitivityCandidate:
    """One compatible or non-compatible initial-state reconstruction."""

    requested_rho: float
    height_kernel_sd_m: float
    effective_rho: float
    reconstructed_height_sd_m: float
    reconstructed_H0_m: float
    target_H0_m: float
    H0_error_m: float
    maximum_scaled_error: float
    compatible: bool
    root_status: str
    result: CopulaInitialStateResult

    def record(self) -> dict[str, float | bool | str]:
        row: dict[str, float | bool | str] = {
            "requested_rho": self.requested_rho,
            "height_kernel_sd_m": self.height_kernel_sd_m,
            "effective_rho": self.effective_rho,
            "reconstructed_height_sd_m": self.reconstructed_height_sd_m,
            "target_H0_m": self.target_H0_m,
            "reconstructed_H0_m": self.reconstructed_H0_m,
            "H0_error_m": self.H0_error_m,
            "maximum_scaled_error": self.maximum_scaled_error,
            "compatible": self.compatible,
            "root_status": self.root_status,
        }
        for key, value in self.result.reconstructed_observables.items():
            row[f"reconstructed_{key}"] = value
        for key, value in self.result.absolute_errors.items():
            row[f"absolute_error_{key}"] = value
        return row


def _compatibility_score(result: CopulaInitialStateResult) -> float:
    scales = {
        "N": max(1.0e-6 * result.target_observables["N"], 1.0e-12),
        "G": 0.02,
        "Dm": 0.01,
        "Dg": 0.02,
        "sigma_D": 0.02,
        "Hm": 0.01,
        "H0": 0.02,
        "H0_minus_Hm": 0.02,
    }
    return max(
        abs(result.absolute_errors[key]) / scales[key]
        for key in scales
    )


def candidate_is_compatible(result: CopulaInitialStateResult) -> bool:
    """Apply numerical reconstruction tolerances, not empirical uncertainty."""
    selected_ok = abs(result.selected_stems_per_ha - 100.0) <= 1.0e-6
    return bool(
        result.marginal_calibration_success
        and selected_ok
        and _compatibility_score(result) <= 1.0
    )


def solve_height_dispersion_for_rho(
    *,
    observation: Mapping[str, float | None],
    p: Parameters,
    copula_rho: float,
    height_sd_bounds_m: tuple[float, float] = (0.5, 6.0),
) -> SensitivityCandidate:
    """Find height kernel SD reproducing dominant height for one copula rho."""
    target_H0 = observation.get("H0")
    if target_H0 is None:
        raise ValueError("the initial observation must contain dominant height.")
    lower, upper = map(float, height_sd_bounds_m)
    if not (0.0 < lower < upper):
        raise ValueError("height_sd_bounds_m must satisfy 0 < lower < upper.")

    cache: dict[float, CopulaInitialStateResult] = {}

    def build(sd: float) -> CopulaInitialStateResult:
        key = float(sd)
        if key not in cache:
            cache[key] = build_gaussian_copula_initial_state(
                observation=observation,
                p=p,
                height_kernel_sd_m=key,
                copula_rho=copula_rho,
            )
        return cache[key]

    def objective(sd: float) -> float:
        return build(sd).reconstructed_observables["H0"] - float(target_H0)

    f_lower = objective(lower)
    f_upper = objective(upper)
    if f_lower == 0.0:
        selected_sd = lower
        status = "lower_bound_exact"
    elif f_upper == 0.0:
        selected_sd = upper
        status = "upper_bound_exact"
    elif f_lower * f_upper < 0.0:
        selected_sd = float(
            brentq(objective, lower, upper, xtol=1.0e-8, rtol=1.0e-10)
        )
        status = "root_found"
    else:
        # Do not extrapolate. Retain the closer boundary and expose the status.
        selected_sd = lower if abs(f_lower) <= abs(f_upper) else upper
        status = "target_not_bracketed"

    result = build(selected_sd)
    error = result.reconstructed_observables["H0"] - float(target_H0)
    return SensitivityCandidate(
        requested_rho=float(copula_rho),
        height_kernel_sd_m=float(selected_sd),
        effective_rho=float(result.effective_rho),
        reconstructed_height_sd_m=float(result.reconstructed_height_sd_m),
        reconstructed_H0_m=float(result.reconstructed_observables["H0"]),
        target_H0_m=float(target_H0),
        H0_error_m=float(error),
        maximum_scaled_error=float(_compatibility_score(result)),
        compatible=candidate_is_compatible(result),
        root_status=status,
        result=result,
    )


def run_initial_state_sensitivity(
    *,
    observation: Mapping[str, float | None],
    p: Parameters,
    rho_values: Iterable[float] = DEFAULT_RHO_VALUES,
    height_sd_bounds_m: tuple[float, float] = (0.5, 6.0),
) -> tuple[SensitivityCandidate, ...]:
    """Evaluate the identifiable height-dispersion curve over copula rhos."""
    values = tuple(float(value) for value in rho_values)
    if not values:
        raise ValueError("rho_values must contain at least one value.")
    if len(set(values)) != len(values):
        raise ValueError("rho_values must not contain duplicates.")
    return tuple(
        solve_height_dispersion_for_rho(
            observation=observation,
            p=p,
            copula_rho=rho,
            height_sd_bounds_m=height_sd_bounds_m,
        )
        for rho in values
    )


def sensitivity_records(
    candidates: Iterable[SensitivityCandidate],
) -> list[dict[str, float | bool | str]]:
    """Return machine-readable rows without serialising density arrays."""
    return [candidate.record() for candidate in candidates]
