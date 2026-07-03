import numpy as np

from simulations.baseline.initial_condition import build_initial_condition
from simulations.baseline.parameters import build_parameters
from simulations.baseline.context import build_context

from pydynamicforest.solver import simulate


def test_sparse_short_simulation_matches_dense_short_simulation():
    x0 = build_initial_condition()
    p = build_parameters()
    c = build_context()

    dense_results = simulate(
        x0,
        p,
        c,
        max_steps=5,
        solver_name="dense",
    )

    sparse_results = simulate(
        x0,
        p,
        c,
        max_steps=5,
        solver_name="sparse",
    )

    assert dense_results.final_state.step_index == sparse_results.final_state.step_index
    assert np.isclose(dense_results.final_state.time, sparse_results.final_state.time)
    assert np.isclose(dense_results.final_state.age, sparse_results.final_state.age)

    assert np.allclose(
        dense_results.final_state.U,
        sparse_results.final_state.U,
        rtol=1e-10,
        atol=1e-10,
    )

    assert np.allclose(
        dense_results.time_series.total_mass,
        sparse_results.time_series.total_mass,
        rtol=1e-10,
        atol=1e-10,
    )

    assert np.allclose(
        dense_results.time_series.legacy_mass,
        sparse_results.time_series.legacy_mass,
        rtol=1e-10,
        atol=1e-10,
    )

    assert np.allclose(
        dense_results.time_series.top_height,
        sparse_results.time_series.top_height,
        rtol=1e-10,
        atol=1e-10,
    )

    assert np.allclose(
        dense_results.time_series.basal_area,
        sparse_results.time_series.basal_area,
        rtol=1e-10,
        atol=1e-10,
    )
    