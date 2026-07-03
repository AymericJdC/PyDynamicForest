# SPDX-License-Identifier: LGPL-3.0-or-later
import numpy as np

from simulations.baseline.initial_condition import build_initial_condition
from simulations.baseline.parameters import build_parameters
from simulations.baseline.context import build_context

from pydynamicforest.solver import simulate


def test_simulate_runs_short_baseline():
    x0 = build_initial_condition()
    p = build_parameters()
    c = build_context()

    results = simulate(x0, p, c, max_steps=3)

    assert results.final_state.step_index == 3
    assert results.metadata["n_steps_run"] == 3
    assert results.metadata["max_steps"] == 3

    assert len(results.time_series.times) == 4
    assert len(results.time_series.ages) == 4
    assert len(results.time_series.total_mass) == 4
    assert len(results.time_series.legacy_mass) == 4
    assert len(results.time_series.top_height) == 4
    assert len(results.time_series.basal_area) == 4

    assert results.final_state.U.shape == (
        p.numerics.grid.nx,
        p.numerics.grid.ny,
    )

    assert np.all(np.isfinite(results.final_state.U))
    assert results.time_series.total_mass[-1] > 0.0