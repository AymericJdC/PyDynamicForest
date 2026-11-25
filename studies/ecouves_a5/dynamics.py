# SPDX-License-Identifier: LGPL-3.0-or-later
"""Steps 3 and 4: simulation of the trajectory and stand-level diagnostics."""

from __future__ import annotations

from collections.abc import Mapping

import numpy as np

from pydynamicforest.fast_solver import ConstantCoefficientStepper
from pydynamicforest.numerics import trapezoidal_weights_2d
from pydynamicforest.observation_operators import (
    basal_area_consistent,
    continuous_dominant_height,
    height_dbh_correlation,
    mean_dbh,
    mean_height,
    quadratic_mean_dbh,
    stand_density,
)


def summarize(U: np.ndarray, p) -> dict[str, float]:
    """Stand variables and structural diagnostics of a state (article Sect. 5.3)."""

    n = stand_density(U, p)
    dm = mean_dbh(U, p, unit="cm")
    dg = quadratic_mean_dbh(U, p, unit="cm")
    hm = mean_height(U, p)
    h0 = continuous_dominant_height(U, p)
    return {
        "N": n,
        "G": basal_area_consistent(U, p),
        "Dm": dm,
        "Dg": dg,
        "sigma_D": float(np.sqrt(max(0.0, dg * dg - dm * dm))),
        "Hm": hm,
        "H0": h0,
        "H0_minus_Hm": h0 - hm,
        "rho_HD": height_dbh_correlation(U, p),
    }


def mean_status(U: np.ndarray, p, stepper: ConstantCoefficientStepper | None = None) -> float:
    stepper = stepper or ConstantCoefficientStepper(p, check_time_independence=False)
    S = stepper.status(U)
    g = p.numerics.grid
    W = trapezoidal_weights_2d(g.nx, g.ny)
    return float(np.sum(W * U * S) / np.sum(W * U))


def inventory_steps(ages: Mapping[int, float], dt: float) -> dict[int, int]:
    """Time-step index of each inventory, counted from the first one."""

    a0 = min(ages.values())
    return {year: int(round((age - a0) / dt)) for year, age in ages.items()}


def simulate_inventories(
    U0: np.ndarray,
    p,
    ages: Mapping[int, float],
    linear_solver: str = "cg",
    height_status_exponent: float = 1.0,
    record_every: int | None = None,
    progress=None,
) -> tuple[dict[int, np.ndarray], list[dict]]:
    """Run from the first inventory to the last; return the states at each inventory.

    ``record_every`` (in steps) also returns a time series of the diagnostics.
    """

    stepper = ConstantCoefficientStepper(p, linear_solver=linear_solver, height_status_exponent=height_status_exponent)
    dt = p.numerics.time.dt
    steps = inventory_steps(ages, dt)
    last = max(steps.values())
    a0 = min(ages.values())
    U = np.array(U0, dtype=float, copy=True)
    saved, series = {}, []
    for k in range(last + 1):
        for year, s in steps.items():
            if s == k:
                saved[year] = U.copy()
        if record_every and k % record_every == 0:
            series.append({"age": a0 + k * dt, **summarize(U, p),
                           "mean_status": mean_status(U, p, stepper), "min_U": float(U.min())})
        if k == last:
            break
        U = stepper.step(U)
        if progress is not None:
            progress(k + 1, last)
    return saved, series


def comparison_rows(simulated: Mapping[int, np.ndarray], observed: Mapping[int, np.ndarray], p) -> list[dict]:
    """Long table year x metric with simulated and regularised observed values."""

    rows = []
    for year in sorted(observed):
        so, ss = summarize(observed[year], p), summarize(simulated[year], p)
        for metric in ss:
            rows.append({"year": year, "metric": metric, "simulated": ss[metric], "observed": so[metric],
                         "relative_difference": (ss[metric] - so[metric]) / so[metric] if so[metric] else float("nan")})
        rows.append({"year": year, "metric": "mean_status", "simulated": mean_status(simulated[year], p),
                     "observed": mean_status(observed[year], p), "relative_difference": float("nan")})
    return rows
