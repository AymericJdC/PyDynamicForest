# SPDX-License-Identifier: LGPL-3.0-or-later

from dataclasses import replace

import numpy as np

from simulations.baseline.context import build_context
from simulations.baseline.initial_condition import build_initial_condition
from simulations.baseline.parameters import build_parameters

from pydynamicforest.initial_conditions import build_initial_state
from pydynamicforest.model import evaluate_state_model_fields
from pydynamicforest.types import CoefficientLaw


def test_evaluate_model_fields_returns_expected_shapes():
    x0 = build_initial_condition()
    p = build_parameters()
    c = build_context()

    state = build_initial_state(x0, p, c)

    fields = evaluate_state_model_fields(
        p,
        state,
        derived=None,
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
    assert fields.status is None


def test_evaluate_model_fields_preserves_baseline_laws():
    x0 = build_initial_condition()
    p = build_parameters()
    c = build_context()

    state = build_initial_state(x0, p, c)

    fields = evaluate_state_model_fields(
        p,
        state,
        derived=None,
        context=c,
    )

    grid = p.numerics.grid

    diffusion_value = p.model.diffusion_law.parameters["value"]
    mortality_value = p.model.mortality_law.parameters["value"]

    height_rate = p.model.height_growth_law.parameters["normalized_rate"]
    dbh_rate = p.model.dbh_growth_law.parameters["normalized_rate"]

    expected_height_growth = np.zeros((grid.nx, grid.ny))
    expected_dbh_growth = np.zeros((grid.nx, grid.ny))

    for i, x in enumerate(grid.x):
        for j, y in enumerate(grid.y):
            expected_height_growth[i, j] = height_rate * (1.0 - x)
            expected_dbh_growth[i, j] = dbh_rate * (1.0 - y)

    assert np.allclose(fields.diffusion, diffusion_value)
    assert np.allclose(fields.mortality, mortality_value)
    assert np.allclose(fields.height_growth, expected_height_growth)
    assert np.allclose(fields.dbh_growth, expected_dbh_growth)


def test_evaluate_model_fields_supports_context_dependent_law():
    x0 = build_initial_condition()
    p = build_parameters()
    c = build_context()

    state = build_initial_state(x0, p, c)

    def context_dependent_mortality(
        t,
        x,
        y,
        state=None,
        derived=None,
        context=None,
        parameters=None,
    ):
        base = parameters["base"]

        if context is not None and context.name.endswith("_context"):
            return base + parameters["context_increment"]

        return base

    mortality_law = CoefficientLaw(
        name="context_dependent_mortality_test",
        function=context_dependent_mortality,
        parameters={
            "base": 0.1,
            "context_increment": 0.2,
        },
        units="1/year",
    )

    modified_model = replace(
        p.model,
        mortality_law=mortality_law,
    )

    modified_parameters = replace(
        p,
        model=modified_model,
    )

    fields = evaluate_state_model_fields(
        modified_parameters,
        state,
        derived=None,
        context=c,
    )

    assert np.allclose(fields.mortality, 0.3)