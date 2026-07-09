# SPDX-License-Identifier: LGPL-3.0-or-later

from dataclasses import replace

import numpy as np
import pytest

from simulations.baseline.context import build_context
from simulations.baseline.initial_condition import build_initial_condition
from simulations.baseline.parameters import build_parameters
from simulations.baseline.config import build_baseline_config_from_preset

from pydynamicforest.initial_conditions import build_initial_state
from pydynamicforest.solver import (
    evaluate_model_fields_for_solver,
    simulate)
from pydynamicforest.types import ModelFields

def get_field(fields, name):
    """
    Return a model field from either the legacy dictionary format
    or the state-aware ModelFields format.
    """

    if isinstance(fields, dict):
        return fields[name]

    return getattr(fields, name)

def test_solver_model_field_evaluation_defaults_to_legacy():
    x0 = build_initial_condition()
    p = build_parameters()
    c = build_context()

    state = build_initial_state(x0, p, c)

    fields = evaluate_model_fields_for_solver(
        state,
        p,
        context=c,
    )

    assert fields is not None


def test_solver_model_field_evaluation_legacy_mode_matches_expected_diffusion():
    x0 = build_initial_condition()
    p = build_parameters()
    c = build_context()

    state = build_initial_state(x0, p, c)

    p = replace(
        p,
        numerics=replace(
            p.numerics,
            model_field_evaluation="legacy",
        ),
    )

    fields = evaluate_model_fields_for_solver(
        state,
        p,
        context=c,
    )

    expected_diffusion = p.model.diffusion_law.parameters["value"]

    assert isinstance(fields, dict)
    assert "diffusion" in fields
    assert np.allclose(fields["diffusion"], expected_diffusion)


def test_solver_model_field_evaluation_state_mode_returns_legacy_compatible_dict():
    x0 = build_initial_condition()
    p = build_parameters()
    c = build_context()

    state = build_initial_state(x0, p, c)

    p = replace(
        p,
        numerics=replace(
            p.numerics,
            model_field_evaluation="state",
        ),
    )

    fields = evaluate_model_fields_for_solver(
        state,
        p,
        context=c,
    )

    expected_shape = (
        p.numerics.grid.nx,
        p.numerics.grid.ny,
    )

    assert isinstance(fields, dict)

    for name in [
        "diffusion",
        "mortality",
        "height_growth",
        "dbh_growth",
    ]:
        assert name in fields
        assert fields[name].shape == expected_shape


def test_solver_model_field_evaluation_unknown_mode_raises():
    x0 = build_initial_condition()
    p = build_parameters()
    c = build_context()

    state = build_initial_state(x0, p, c)

    p = replace(
        p,
        numerics=replace(
            p.numerics,
            model_field_evaluation="unknown",
        ),
    )

    with pytest.raises(ValueError, match="Unknown model_field_evaluation mode"):
        evaluate_model_fields_for_solver(
            state,
            p,
            context=c,
        )
        
def test_legacy_and_state_model_field_modes_match_for_baseline():
    """
    For the current baseline laws, the legacy time-based and state-aware
    model-field evaluation modes should produce the same coefficient fields.

    This test provides a guard before any future migration of the solver
    toward the state-aware pathway.
    """

    x0 = build_initial_condition()
    p = build_parameters()
    c = build_context()

    state = build_initial_state(x0, p, c)

    legacy_p = replace(
        p,
        numerics=replace(
            p.numerics,
            model_field_evaluation="legacy",
        ),
    )

    state_p = replace(
        p,
        numerics=replace(
            p.numerics,
            model_field_evaluation="state",
        ),
    )

    legacy_fields = evaluate_model_fields_for_solver(
        state,
        legacy_p,
        context=c,
    )

    state_fields = evaluate_model_fields_for_solver(
        state,
        state_p,
        context=c,
    )

    assert isinstance(legacy_fields, dict)
    assert isinstance(state_fields, dict)

    field_names = [
        "diffusion",
        "mortality",
        "height_growth",
        "dbh_growth",
    ]

    for name in field_names:
        legacy_field = get_field(legacy_fields, name)
        state_field = get_field(state_fields, name)

        assert legacy_field.shape == state_field.shape
        assert np.allclose(legacy_field, state_field)

def test_short_simulation_runs_with_state_model_field_evaluation():
    x0 = build_initial_condition()
    p = build_parameters()
    c = build_context()

    p = replace(
        p,
        numerics=replace(
            p.numerics,
            model_field_evaluation="state",
        ),
    )

    results = simulate(
        x0,
        p,
        c,
        max_steps=2,
    )

    assert results.final_state.step_index == 2
    assert results.metadata["n_steps_run"] == 2

def test_short_simulation_matches_between_legacy_and_state_model_field_modes():
    """
    For the current baseline laws, a short simulation should give the same
    numerical results when model fields are evaluated through the legacy
    pathway or through the state-aware pathway.

    This test is a guard before any future migration of the solver toward
    state-aware model laws.
    """

    config = build_baseline_config_from_preset("short-debug")

    x0 = build_initial_condition(config)
    p = build_parameters(config)
    c = build_context(config)

    legacy_p = replace(
        p,
        numerics=replace(
            p.numerics,
            model_field_evaluation="legacy",
        ),
    )

    state_p = replace(
        p,
        numerics=replace(
            p.numerics,
            model_field_evaluation="state",
        ),
    )

    legacy_results = simulate(
        x0,
        legacy_p,
        c,
        max_steps=5,
    )

    state_results = simulate(
        x0,
        state_p,
        c,
        max_steps=5,
    )

    assert legacy_results.final_state.step_index == state_results.final_state.step_index
    assert legacy_results.final_state.time == state_results.final_state.time
    assert legacy_results.final_state.age == state_results.final_state.age

    assert np.allclose(
        legacy_results.final_state.U,
        state_results.final_state.U,
        rtol=1e-12,
        atol=1e-14,
    )

    time_series_fields = [
        "total_mass",
        "legacy_mass",
        "minimum_density",
        "top_height",
        "basal_area",
    ]

    for field_name in time_series_fields:
        legacy_values = np.asarray(
            getattr(legacy_results.time_series, field_name)
        )
        state_values = np.asarray(
            getattr(state_results.time_series, field_name)
        )

        assert np.allclose(
            legacy_values,
            state_values,
            rtol=1e-12,
            atol=1e-14,
        )