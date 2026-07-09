# SPDX-License-Identifier: LGPL-3.0-or-later

from dataclasses import replace

import numpy as np
import pytest

from simulations.baseline.context import build_context
from simulations.baseline.initial_condition import build_initial_condition
from simulations.baseline.parameters import build_parameters

from pydynamicforest.initial_conditions import build_initial_state
from pydynamicforest.solver import evaluate_model_fields_for_solver


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
