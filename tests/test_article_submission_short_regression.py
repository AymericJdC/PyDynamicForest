import numpy as np
import pytest

from pydynamicforest.diagnostics import (
    basal_area,
    legacy_mass,
    legacy_top_height,
    trapezoidal_mass,
)
from pydynamicforest.initial_conditions import build_initial_state
from pydynamicforest.solver import simulate
from simulations.article_submission_legacy.context import build_context
from simulations.article_submission_legacy.initial_condition import build_initial_condition
from simulations.article_submission_legacy.legacy_reference import run_reference_steps
from simulations.article_submission_legacy.parameters import build_parameters


@pytest.fixture(scope="module")
def article_submission_objects():
    return build_initial_condition(), build_parameters(), build_context()


@pytest.mark.parametrize("n_steps", [1, 10, 100])
def test_sparse_refactor_matches_independent_legacy_reference(
    article_submission_objects,
    n_steps,
):
    x0, p, c = article_submission_objects
    initial_state = build_initial_state(x0, p, c)

    U_reference = run_reference_steps(initial_state.U, p, n_steps)
    results = simulate(x0, p, c, max_steps=n_steps, solver_name="sparse")
    U_refactor = results.final_state.U

    np.testing.assert_allclose(U_refactor, U_reference, rtol=1.0e-12, atol=1.0e-10)

    assert trapezoidal_mass(U_refactor, p) == pytest.approx(
        trapezoidal_mass(U_reference, p), rel=1.0e-12, abs=1.0e-10
    )
    assert legacy_mass(U_refactor, p) == pytest.approx(
        legacy_mass(U_reference, p), rel=1.0e-12, abs=1.0e-10
    )
    assert basal_area(U_refactor, p) == pytest.approx(
        basal_area(U_reference, p), rel=1.0e-12, abs=1.0e-12
    )
    assert legacy_top_height(U_refactor, p) == pytest.approx(
        legacy_top_height(U_reference, p), rel=1.0e-12, abs=1.0e-10
    )
    assert float(np.min(U_refactor)) == pytest.approx(
        float(np.min(U_reference)), rel=1.0e-12, abs=1.0e-12
    )


def test_reference_zero_steps_returns_an_independent_copy(article_submission_objects):
    x0, p, c = article_submission_objects
    initial_state = build_initial_state(x0, p, c)

    U_reference = run_reference_steps(initial_state.U, p, 0)

    np.testing.assert_array_equal(U_reference, initial_state.U)
    assert U_reference is not initial_state.U
