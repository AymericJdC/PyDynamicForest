# SPDX-License-Identifier: LGPL-3.0-or-later
"""Sequential calibration of model rates against stand variables.

With T the inventories after the initial one, each calibrated rate minimises a
log objective on one stand variable,

    J_X(rate) = sum_T (log X[n](t_k) - log X[n_k^reg])^2,

for fixed values of the other rates, by bounded one-dimensional minimisation;
the minimisations alternate for a given number of passes. The article
calibrates the mortality coefficient K on stand density N and the DBH growth
rate c_phi on mean DBH Dm (Sect. 5.4); the height growth rate c_h can be added
with mean height Hm as target.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Mapping, Sequence

import numpy as np
from scipy.optimize import minimize_scalar

from .dynamics import simulate_inventories, summarize

# rate name -> stand variable used as target
DEFAULT_TARGETS = {"mortality": "N", "dbh_growth_rate": "Dm", "height_growth_rate": "Hm"}


def log_objective(metric: str, simulated: Mapping[int, np.ndarray], observed_summary: Mapping[int, dict], p, years) -> float:
    return float(sum((math.log(summarize(simulated[y], p)[metric]) - math.log(observed_summary[y][metric])) ** 2
                     for y in years))


def calibrate_rates(
    U0: np.ndarray,
    observed: Mapping[int, np.ndarray],
    ages: Mapping[int, float],
    make_parameters: Callable[[dict], object],
    initial: Mapping[str, float],
    rates: Sequence[str],
    bounds: Mapping[str, tuple[float, float]] | None = None,
    passes: int = 2,
    relative_bracket: float = 0.03,
    relative_tolerance: float = 1e-4,
    targets: Mapping[str, str] = DEFAULT_TARGETS,
    linear_solver: str = "cg",
    log: Callable[[str], None] = print,
) -> dict:
    """Return the calibrated rates, the final objectives and the evaluation history.

    ``make_parameters(values)`` builds model parameters from a dict of rates;
    ``bounds`` gives absolute bounds per rate, otherwise the bracket is
    ``value * (1 +/- relative_bracket)``.
    """

    first = min(ages, key=ages.get)
    years = [y for y in sorted(ages) if y != first]
    values = dict(initial)
    p_ref = make_parameters(values)
    target = {y: summarize(observed[y], p_ref) for y in years}
    history = []

    def objective(rate: str, x: float) -> float:
        trial = {**values, rate: float(x)}
        p = make_parameters(trial)
        states, _ = simulate_inventories(U0, p, ages, linear_solver=linear_solver)
        value = log_objective(targets[rate], states, target, p, years)
        history.append({**trial, "rate": rate, "metric": targets[rate], "objective": value})
        log(f"J_{targets[rate]}  " + "  ".join(f"{k}={v:.6g}" for k, v in trial.items()) + f"  {value:.6e}")
        return value

    for _ in range(int(passes)):
        for rate in rates:
            v = values[rate]
            lo, hi = (bounds or {}).get(rate, (v * (1 - relative_bracket), v * (1 + relative_bracket)))
            r = minimize_scalar(lambda x, rate=rate: objective(rate, x), method="bounded", bounds=(lo, hi),
                                options={"xatol": relative_tolerance * v})
            values[rate] = float(r.x)
    return {**values, "history": history}


def calibrate(
    U0, observed, ages, make_parameters: Callable[[float, float], object], K0: float, cphi0: float,
    passes: int = 2, relative_bracket: float = 0.03, relative_tolerance: float = 1e-4,
    linear_solver: str = "cg", log: Callable[[str], None] = print,
) -> dict:
    """Calibration of the article: K on N, then c_phi on Dm."""

    result = calibrate_rates(
        U0, observed, ages, lambda v: make_parameters(v["mortality"], v["dbh_growth_rate"]),
        {"mortality": K0, "dbh_growth_rate": cphi0}, ["mortality", "dbh_growth_rate"],
        passes=passes, relative_bracket=relative_bracket, relative_tolerance=relative_tolerance,
        linear_solver=linear_solver, log=log)
    return {"mortality": result["mortality"], "dbh_growth_rate": result["dbh_growth_rate"], "history": result["history"]}
