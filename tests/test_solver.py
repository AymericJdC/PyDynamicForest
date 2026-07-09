# SPDX-License-Identifier: LGPL-3.0-or-later

import numpy as np

from simulations.baseline.initial_condition import build_initial_condition
from simulations.baseline.parameters import build_parameters
from simulations.baseline.context import build_context

from pydynamicforest.initial_conditions import build_initial_state
from pydynamicforest.solver import advance_one_step_dense_legacy


def test_advance_one_step_dense_legacy_returns_valid_state():
    x0 = build_initial_condition()
    p = build_parameters()
    c = build_context()

    state0 = build_initial_state(x0, p, c)
    state1 = advance_one_step_dense_legacy(state0, p)

    assert state1.step_index == state0.step_index + 1
    assert np.isclose(state1.time, state0.time + p.numerics.time.dt)
    assert np.isclose(state1.age, state0.age + p.numerics.time.dt)

    assert state1.U.shape == state0.U.shape
    assert np.all(np.isfinite(state1.U))

    assert np.min(state1.U) >= -1e-8
