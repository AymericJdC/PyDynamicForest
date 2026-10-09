import numpy as np
import pytest

from pydynamicforest.initial_conditions import build_initial_state
from pydynamicforest.numerics import compute_derived_quantities
from pydynamicforest.solver import (
    compute_transport_components_legacy,
    compute_transport_legacy,
    evaluate_model_fields_for_solver,
)
from pydynamicforest.types import State
from simulations.article_submission_legacy.config import make_short_debug_config
from simulations.article_submission_legacy.context import build_context
from simulations.article_submission_legacy.initial_condition import (
    build_initial_condition,
)
from simulations.article_submission_legacy.parameters import build_parameters


def _state_parameters_and_derived():
    config = make_short_debug_config()
    config["grid"].update({"nx": 7, "ny": 6})
    x0 = build_initial_condition(config)
    p = build_parameters(config)
    c = build_context(config)
    state = build_initial_state(x0, p, c)
    derived = compute_derived_quantities(state, p)
    return state, p, derived


def test_transport_components_sum_to_validated_legacy_total():
    state, p, derived = _state_parameters_and_derived()
    fields = evaluate_model_fields_for_solver(state, p)

    components = compute_transport_components_legacy(state, p, derived, fields)
    legacy_total = compute_transport_legacy(state, p, derived, fields)

    assert set(components) == {"height", "dbh", "total"}
    assert components["height"].shape == state.U.shape
    assert components["dbh"].shape == state.U.shape
    assert components["total"].shape == state.U.shape
    np.testing.assert_array_equal(
        components["total"],
        components["height"] + components["dbh"],
    )
    np.testing.assert_allclose(
        components["total"],
        legacy_total,
        rtol=0.0,
        atol=1.0e-15,
    )


def test_zero_dbh_growth_removes_only_dbh_transport():
    state, p, derived = _state_parameters_and_derived()
    fields = evaluate_model_fields_for_solver(state, p)
    fields = dict(fields)
    fields["dbh_growth"] = np.zeros_like(fields["dbh_growth"])

    components = compute_transport_components_legacy(state, p, derived, fields)
    legacy_total = compute_transport_legacy(state, p, derived, fields)

    np.testing.assert_array_equal(
        components["dbh"],
        np.zeros_like(state.U),
    )
    np.testing.assert_allclose(
        components["height"],
        legacy_total,
        rtol=0.0,
        atol=1.0e-15,
    )


def test_zero_height_growth_removes_only_height_transport():
    state, p, derived = _state_parameters_and_derived()
    fields = evaluate_model_fields_for_solver(state, p)
    fields = dict(fields)
    fields["height_growth"] = np.zeros_like(fields["height_growth"])

    components = compute_transport_components_legacy(state, p, derived, fields)
    legacy_total = compute_transport_legacy(state, p, derived, fields)

    np.testing.assert_array_equal(
        components["height"],
        np.zeros_like(state.U),
    )
    np.testing.assert_allclose(
        components["dbh"],
        legacy_total,
        rtol=0.0,
        atol=1.0e-15,
    )


def test_components_match_legacy_total_for_signed_spatially_varying_fields():
    state, p, _ = _state_parameters_and_derived()
    rng = np.random.default_rng(4319)
    positive_density = rng.uniform(0.1, 4.0, size=state.U.shape)
    state = State(
        time=state.time,
        age=state.age,
        U=positive_density,
        step_index=state.step_index,
    )
    derived = compute_derived_quantities(state, p)
    fields = {
        "height_growth": rng.uniform(-0.2, 0.2, size=state.U.shape),
        "dbh_growth": rng.uniform(-0.15, 0.15, size=state.U.shape),
    }

    components = compute_transport_components_legacy(state, p, derived, fields)
    legacy_total = compute_transport_legacy(state, p, derived, fields)

    np.testing.assert_allclose(
        components["total"],
        legacy_total,
        rtol=0.0,
        atol=1.0e-15,
    )


def test_component_operator_does_not_mutate_inputs():
    state, p, derived = _state_parameters_and_derived()
    fields = evaluate_model_fields_for_solver(state, p)
    U_before = state.U.copy()
    J_before = derived.cumulative_distribution.copy()
    S_before = derived.status_field.copy()
    fields_before = {
        name: np.array(values, copy=True)
        for name, values in fields.items()
    }

    compute_transport_components_legacy(state, p, derived, fields)

    np.testing.assert_array_equal(state.U, U_before)
    np.testing.assert_array_equal(derived.cumulative_distribution, J_before)
    np.testing.assert_array_equal(derived.status_field, S_before)
    for name, values in fields_before.items():
        np.testing.assert_array_equal(fields[name], values)


def test_component_operator_accepts_state_aware_model_fields():
    config = make_short_debug_config()
    config["grid"].update({"nx": 6, "ny": 5})
    config["solver"]["model_field_evaluation"] = "state"
    x0 = build_initial_condition(config)
    p = build_parameters(config)
    c = build_context(config)
    state = build_initial_state(x0, p, c)
    derived = compute_derived_quantities(state, p)
    fields = evaluate_model_fields_for_solver(state, p)

    components = compute_transport_components_legacy(state, p, derived, fields)
    legacy_total = compute_transport_legacy(state, p, derived, fields)

    np.testing.assert_allclose(
        components["total"],
        legacy_total,
        rtol=0.0,
        atol=1.0e-15,
    )
