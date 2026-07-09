# SPDX-License-Identifier: LGPL-3.0-or-later

from dataclasses import replace

import numpy as np
import pytest

from simulations.baseline.context import build_context
from simulations.baseline.initial_condition import build_initial_condition
from simulations.baseline.parameters import build_parameters

from pydynamicforest.initial_conditions import build_initial_state
from pydynamicforest.solver import evaluate_model_fields_for_solver
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


def test_solver_model_field_evaluation_state_mode_returns_model_fields():
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

    assert fields.diffusion.shape == expected_shape
    assert fields.mortality.shape == expected_shape
    assert fields.height_growth.shape == expected_shape
    assert fields.dbh_growth.shape == expected_shape


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
    assert isinstance(state_fields, ModelFields)

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