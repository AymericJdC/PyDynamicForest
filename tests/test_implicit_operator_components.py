import numpy as np
import pytest
from scipy.sparse import identity

from pydynamicforest.initial_conditions import build_initial_state
from pydynamicforest.model import evaluate_model_fields
from pydynamicforest.numerics import compute_derived_quantities
from pydynamicforest.solver import (
    advance_one_step_sparse_legacy,
    assemble_dense_legacy_system,
    assemble_sparse_legacy_system,
    compute_transport_legacy,
    evaluate_model_fields_for_solver,
)
from pydynamicforest.types import State
from simulations.article_submission_legacy.config import make_short_debug_config
from simulations.article_submission_legacy.context import build_context
from simulations.article_submission_legacy.initial_condition import build_initial_condition
from simulations.article_submission_legacy.parameters import build_parameters


def _assembly_inputs(nx=7, ny=6, random_state=False):
    config = make_short_debug_config()
    config["grid"].update({"nx": nx, "ny": ny})
    x0 = build_initial_condition(config)
    p = build_parameters(config)
    c = build_context(config)
    state = build_initial_state(x0, p, c)
    if random_state:
        rng = np.random.default_rng(9041)
        state = State(
            time=state.time,
            age=state.age,
            U=rng.uniform(0.1, 4.0, size=state.U.shape),
            step_index=state.step_index,
        )
    derived = compute_derived_quantities(state, p)
    fields_current = evaluate_model_fields_for_solver(state, p)
    fields_next = evaluate_model_fields(p, state.time + p.numerics.time.dt)
    transport = compute_transport_legacy(state, p, derived, fields_current)
    return state, p, derived, fields_next, transport


def _dense(*, diffusion_factor=1.0, mortality_factor=1.0, random_state=False):
    state, p, derived, fields_next, transport = _assembly_inputs(
        random_state=random_state
    )
    return assemble_dense_legacy_system(
        state,
        p,
        derived,
        fields_next,
        transport,
        diffusion_factor=diffusion_factor,
        mortality_factor=mortality_factor,
    )


def _sparse(*, diffusion_factor=1.0, mortality_factor=1.0, random_state=False):
    state, p, derived, fields_next, transport = _assembly_inputs(
        random_state=random_state
    )
    return assemble_sparse_legacy_system(
        state,
        p,
        derived,
        fields_next,
        transport,
        diffusion_factor=diffusion_factor,
        mortality_factor=mortality_factor,
    )


def test_explicit_unit_factors_match_default_dense_and_sparse_assemblies():
    state, p, derived, fields_next, transport = _assembly_inputs(random_state=True)

    A_dense_default, b_dense_default = assemble_dense_legacy_system(
        state, p, derived, fields_next, transport
    )
    A_dense_explicit, b_dense_explicit = assemble_dense_legacy_system(
        state,
        p,
        derived,
        fields_next,
        transport,
        diffusion_factor=1.0,
        mortality_factor=1.0,
    )
    A_sparse_default, b_sparse_default = assemble_sparse_legacy_system(
        state, p, derived, fields_next, transport
    )
    A_sparse_explicit, b_sparse_explicit = assemble_sparse_legacy_system(
        state,
        p,
        derived,
        fields_next,
        transport,
        diffusion_factor=1.0,
        mortality_factor=1.0,
    )

    np.testing.assert_array_equal(A_dense_default, A_dense_explicit)
    np.testing.assert_array_equal(b_dense_default, b_dense_explicit)
    np.testing.assert_array_equal(A_sparse_default.toarray(), A_sparse_explicit.toarray())
    np.testing.assert_array_equal(b_sparse_default, b_sparse_explicit)
    np.testing.assert_array_equal(A_dense_default, A_sparse_default.toarray())
    np.testing.assert_array_equal(b_dense_default, b_sparse_default)


def test_zero_factors_produce_identity_matrix_without_changing_rhs():
    state, p, derived, fields_next, transport = _assembly_inputs()
    A, b = assemble_sparse_legacy_system(
        state,
        p,
        derived,
        fields_next,
        transport,
        diffusion_factor=0.0,
        mortality_factor=0.0,
    )
    expected_rhs = (state.U - p.numerics.time.dt * transport).reshape(-1)

    np.testing.assert_array_equal(A.toarray(), identity(A.shape[0]).toarray())
    np.testing.assert_array_equal(b, expected_rhs)


def test_mortality_only_matrix_is_diagonal():
    A, _ = _sparse(diffusion_factor=0.0, mortality_factor=1.0)
    off_diagonal = A.toarray() - np.diag(np.diag(A.toarray()))

    np.testing.assert_array_equal(off_diagonal, np.zeros_like(off_diagonal))
    assert np.all(A.diagonal() >= 1.0)


def test_diffusion_only_matrix_has_no_mortality_increment():
    A_diffusion, _ = _sparse(diffusion_factor=1.0, mortality_factor=0.0)
    A_identity, _ = _sparse(diffusion_factor=0.0, mortality_factor=0.0)
    difference = A_diffusion - A_identity

    np.testing.assert_allclose(
        np.asarray(difference.sum(axis=1)).ravel(),
        np.zeros(A_diffusion.shape[0]),
        rtol=0.0,
        atol=1.0e-15,
    )
    assert np.all(difference.diagonal() >= 0.0)


def test_complete_matrix_recomposes_from_diffusion_and_mortality_parts():
    A_full, b_full = _sparse(diffusion_factor=1.0, mortality_factor=1.0)
    A_diffusion, b_diffusion = _sparse(
        diffusion_factor=1.0, mortality_factor=0.0
    )
    A_mortality, b_mortality = _sparse(
        diffusion_factor=0.0, mortality_factor=1.0
    )
    A_identity, b_identity = _sparse(
        diffusion_factor=0.0, mortality_factor=0.0
    )

    recomposed = A_diffusion + A_mortality - A_identity
    np.testing.assert_allclose(
        A_full.toarray(), recomposed.toarray(), rtol=0.0, atol=1.0e-15
    )
    np.testing.assert_array_equal(b_full, b_diffusion)
    np.testing.assert_array_equal(b_full, b_mortality)
    np.testing.assert_array_equal(b_full, b_identity)


def test_component_factors_are_validated():
    state, p, derived, fields_next, transport = _assembly_inputs()

    for name, kwargs in (
        ("diffusion_factor", {"diffusion_factor": -1.0}),
        ("mortality_factor", {"mortality_factor": np.nan}),
    ):
        with pytest.raises(ValueError, match=name):
            assemble_sparse_legacy_system(
                state, p, derived, fields_next, transport, **kwargs
            )


def test_default_sparse_step_remains_equal_to_explicit_default_assembly():
    state, p, derived, fields_next, transport = _assembly_inputs()
    expected = advance_one_step_sparse_legacy(state, p)
    A, b = assemble_sparse_legacy_system(
        state,
        p,
        derived,
        fields_next,
        transport,
        diffusion_factor=1.0,
        mortality_factor=1.0,
    )
    from scipy.sparse.linalg import spsolve

    U_next = spsolve(A, b).reshape(state.U.shape)
    np.testing.assert_array_equal(U_next, expected.U)
