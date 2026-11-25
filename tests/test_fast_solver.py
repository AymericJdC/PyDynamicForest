# SPDX-License-Identifier: LGPL-3.0-or-later
"""Regression tests: the vectorised scheme reproduces the legacy loop scheme."""

import numpy as np
import pytest
import scipy.sparse as sp

from pydynamicforest.fast_solver import (
    assemble_sparse_system_vectorised,
    compute_derived_quantities_vectorised,
    compute_transport_vectorised,
    cumulative_integral_2d_trapezoidal_vectorised,
    solve_linear_system,
)
from pydynamicforest.initial_conditions import build_initial_state
from pydynamicforest.model import evaluate_model_fields
from pydynamicforest.numerics import (
    compute_derived_quantities,
    cumulative_integral_2d_trapezoidal,
)
from pydynamicforest.solver import (
    advance_one_step_sparse_legacy,
    assemble_sparse_legacy_system,
    compute_transport_legacy,
    select_one_step_solver,
    simulate,
)
from pydynamicforest.types import State
from simulations.baseline.context import build_context
from simulations.baseline.initial_condition import build_initial_condition
from simulations.baseline.parameters import build_parameters


@pytest.fixture(scope="module")
def setup():
    x0 = build_initial_condition()
    p = build_parameters()
    c = build_context()
    state = build_initial_state(x0, p, c)
    return x0, p, c, state


def _random_state(p, seed=0):
    rng = np.random.default_rng(seed)
    g = p.numerics.grid
    return State(time=0.0, age=37.0, U=rng.random((g.nx, g.ny)), step_index=0)


def _close(a, b, rtol=1e-12):
    scale = max(np.max(np.abs(a)), np.max(np.abs(b)), 1e-300)
    return np.max(np.abs(a - b)) <= rtol * scale


def test_cumulative_integral_matches_legacy(setup):
    _, p, _, _ = setup
    U = _random_state(p).U
    g = p.numerics.grid
    assert _close(
        cumulative_integral_2d_trapezoidal_vectorised(U, g.dx, g.dy),
        cumulative_integral_2d_trapezoidal(U, g.dx, g.dy),
        rtol=1e-13,
    )


def test_derived_quantities_match_legacy(setup):
    _, p, _, state = setup
    a = compute_derived_quantities_vectorised(state, p)
    b = compute_derived_quantities(state, p)
    assert a.total_mass == pytest.approx(b.total_mass, rel=1e-13)
    assert _close(a.status_field, b.status_field, rtol=1e-13)


@pytest.mark.parametrize("signs", ["positive", "mixed"])
def test_transport_matches_legacy(setup, signs):
    _, p, _, _ = setup
    state = _random_state(p, seed=1)
    derived = compute_derived_quantities(state, p)
    fields = dict(evaluate_model_fields(p, 0.0))
    if signs == "mixed":
        # velocities of both signs exercise the two upwind branches
        rng = np.random.default_rng(2)
        fields["height_growth"] = rng.normal(size=state.U.shape)
        fields["dbh_growth"] = rng.normal(size=state.U.shape)
    assert _close(
        compute_transport_vectorised(state, p, derived, fields),
        compute_transport_legacy(state, p, derived, fields),
    )


@pytest.mark.parametrize("factors", [(1.0, 1.0), (0.5, 2.0), (0.0, 0.0)])
def test_assembled_system_matches_legacy(setup, factors):
    _, p, _, _ = setup
    state = _random_state(p, seed=3)
    derived = compute_derived_quantities(state, p)
    fields = evaluate_model_fields(p, p.numerics.time.dt)
    transport = compute_transport_legacy(state, p, derived, fields)
    kw = dict(diffusion_factor=factors[0], mortality_factor=factors[1])
    A1, b1 = assemble_sparse_system_vectorised(state, p, derived, fields, transport, **kw)
    A0, b0 = assemble_sparse_legacy_system(state, p, derived, fields, transport, **kw)
    assert _close(A1.toarray(), A0.toarray(), rtol=1e-14)
    assert _close(b1, b0, rtol=1e-14)


def test_assembled_matrix_is_symmetric_positive_definite(setup):
    _, p, _, state = setup
    derived = compute_derived_quantities(state, p)
    fields = evaluate_model_fields(p, p.numerics.time.dt)
    transport = np.zeros_like(state.U)
    A, _ = assemble_sparse_system_vectorised(state, p, derived, fields, transport)
    assert abs(A - A.T).max() == 0.0
    off = abs(A - sp.diags(A.diagonal()))
    assert np.all(A.diagonal() > np.asarray(off.sum(axis=1)).ravel())


def test_cg_matches_direct_solve(setup):
    _, p, _, state = setup
    derived = compute_derived_quantities(state, p)
    fields = evaluate_model_fields(p, p.numerics.time.dt)
    transport = compute_transport_legacy(state, p, derived, fields)
    A, b = assemble_sparse_system_vectorised(state, p, derived, fields, transport)
    x_direct = solve_linear_system(A, b, "direct")
    x_cg = solve_linear_system(A, b, "cg", x0=state.U.ravel())
    assert _close(x_cg, x_direct, rtol=1e-11)


def test_unknown_linear_solver_is_rejected(setup):
    _, p, _, state = setup
    derived = compute_derived_quantities(state, p)
    fields = evaluate_model_fields(p, p.numerics.time.dt)
    A, b = assemble_sparse_system_vectorised(state, p, derived, fields, np.zeros_like(state.U))
    with pytest.raises(ValueError):
        solve_linear_system(A, b, "gmres")


@pytest.mark.parametrize("name, rtol", [("vectorised", 1e-11), ("vectorised_cg", 1e-10)])
def test_one_step_matches_sparse_legacy(setup, name, rtol):
    _, p, _, state = setup
    step, _ = select_one_step_solver(p, name)
    assert _close(step(state, p).U, advance_one_step_sparse_legacy(state, p).U, rtol=rtol)


@pytest.mark.parametrize("name", ["vectorised", "vectorised_cg"])
def test_short_simulation_matches_sparse_legacy(setup, name):
    x0, p, c, _ = setup
    ref = simulate(x0, p, c, max_steps=10, solver_name="sparse")
    new = simulate(x0, p, c, max_steps=10, solver_name=name)
    assert new.metadata["solver"] in ("vectorised_direct", "vectorised_cg")
    assert _close(new.final_state.U, ref.final_state.U, rtol=1e-10)
    assert new.time_series.total_mass[-1] == pytest.approx(ref.time_series.total_mass[-1], rel=1e-12)
