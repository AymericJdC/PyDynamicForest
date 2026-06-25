import numpy as np

from simulations.baseline.initial_condition import build_initial_condition
from simulations.baseline.parameters import build_parameters
from simulations.baseline.context import build_context

from pydynamicforest.initial_conditions import build_initial_state
from pydynamicforest.solver import (
    advance_one_step_dense_legacy,
    advance_one_step_sparse_legacy,
)


def test_sparse_one_step_matches_dense_one_step():
    """
    Check that the sparse one-step solver reproduces the dense legacy
    one-step solver on the baseline initial state.

    This test is important because the dense solver is our current
    regression reference, while the sparse solver is intended to become
    the efficient implementation.
    """

    x0 = build_initial_condition()
    p = build_parameters()
    c = build_context()

    state0 = build_initial_state(x0, p, c)

    dense_state = advance_one_step_dense_legacy(state0, p)
    sparse_state = advance_one_step_sparse_legacy(state0, p)

    assert dense_state.step_index == sparse_state.step_index
    assert np.isclose(dense_state.time, sparse_state.time)
    assert np.isclose(dense_state.age, sparse_state.age)

    assert dense_state.U.shape == sparse_state.U.shape
    assert np.all(np.isfinite(sparse_state.U))

    assert np.allclose(
        dense_state.U,
        sparse_state.U,
        rtol=1e-10,
        atol=1e-10,
    )


def test_sparse_one_step_preserves_basic_state_validity():
    """
    Check basic validity properties of the sparse one-step output.
    """

    x0 = build_initial_condition()
    p = build_parameters()
    c = build_context()

    state0 = build_initial_state(x0, p, c)
    sparse_state = advance_one_step_sparse_legacy(state0, p)

    assert sparse_state.step_index == 1
    assert sparse_state.time > state0.time
    assert sparse_state.age > state0.age

    assert sparse_state.U.shape == state0.U.shape
    assert np.all(np.isfinite(sparse_state.U))

    assert np.min(sparse_state.U) >= -1e-8
    assert np.max(sparse_state.U) > 0.0