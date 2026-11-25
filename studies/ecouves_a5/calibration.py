# SPDX-License-Identifier: LGPL-3.0-or-later
"""Sequential calibration of the mortality coefficient and DBH growth rate.

With T the inventories after the initial one,

    J_N(K)     = sum_T (log N[n](t_k)  - log N[n_k^reg])^2,
    J_D(c_phi) = sum_T (log Dm[n](t_k) - log Dm[n_k^reg])^2.

K minimises J_N for fixed c_phi, then c_phi minimises J_D for fixed K, by
bounded one-dimensional minimisation; the two minimisations alternate for a
given number of passes (article Sect. 5.4).
"""

from __future__ import annotations

import math
from collections.abc import Callable, Mapping

import numpy as np
from scipy.optimize import minimize_scalar

from .dynamics import simulate_inventories, summarize


def log_objective(metric: str, simulated: Mapping[int, np.ndarray], observed_summary: Mapping[int, dict], p, years) -> float:
    return float(sum((math.log(summarize(simulated[y], p)[metric]) - math.log(observed_summary[y][metric])) ** 2
                     for y in years))


def calibrate(
    U0: np.ndarray,
    observed: Mapping[int, np.ndarray],
    ages: Mapping[int, float],
    make_parameters: Callable[[float, float], object],
    K0: float,
    cphi0: float,
    passes: int = 2,
    relative_bracket: float = 0.03,
    relative_tolerance: float = 1e-4,
    linear_solver: str = "cg",
    log: Callable[[str], None] = print,
) -> dict:
    """Return the calibrated ``K`` and ``c_phi`` and the evaluation history.

    ``make_parameters(K, cphi)`` builds the model parameters; ``observed`` maps
    every inventory year to its regularised state, the first one being the
    initial condition.
    """

    first = min(ages, key=ages.get)
    years = [y for y in sorted(ages) if y != first]
    p_ref = make_parameters(K0, cphi0)
    target = {y: summarize(observed[y], p_ref) for y in years}
    history = []

    def objective(metric: str, K: float, cphi: float) -> float:
        p = make_parameters(K, cphi)
        states, _ = simulate_inventories(U0, p, ages, linear_solver=linear_solver)
        value = log_objective(metric, states, target, p, years)
        history.append({"metric": metric, "K": K, "cphi": cphi, "objective": value})
        log(f"J_{'N' if metric == 'N' else 'D'}  K={K:.6f}  cphi={cphi:.6f}  {value:.6e}")
        return value

    K, cphi = float(K0), float(cphi0)
    for _ in range(int(passes)):
        r = minimize_scalar(lambda k: objective("N", k, cphi), method="bounded",
                            bounds=(K * (1 - relative_bracket), K * (1 + relative_bracket)),
                            options={"xatol": relative_tolerance * K})
        K = float(r.x)
        r = minimize_scalar(lambda c: objective("Dm", K, c), method="bounded",
                            bounds=(cphi * (1 - relative_bracket), cphi * (1 + relative_bracket)),
                            options={"xatol": relative_tolerance * cphi})
        cphi = float(r.x)
    return {"mortality": K, "dbh_growth_rate": cphi, "history": history}
