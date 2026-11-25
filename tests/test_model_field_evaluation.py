# SPDX-License-Identifier: LGPL-3.0-or-later

from dataclasses import replace
from types import SimpleNamespace

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

def test_evaluate_model_fields_supports_derived_dependent_law():
    x0 = build_initial_condition()
    p = build_parameters()
    c = build_context()

    state = build_initial_state(x0, p, c)

    status_field = np.zeros_like(state.U)

    derived = SimpleNamespace(
        total_mass=1234.0,
        status_field=status_field,
    )

    def derived_dependent_mortality(
        t,
        x,
        y,
        state=None,
        derived=None,
        context=None,
        parameters=None,
    ):
        return parameters["base"] + parameters["alpha"] * derived.total_mass

    mortality_law = CoefficientLaw(
        name="derived_dependent_mortality_test",
        function=derived_dependent_mortality,
        parameters={
            "base": 0.1,
            "alpha": 0.001,
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
        derived=derived,
        context=c,
    )

    expected_mortality = 0.1 + 0.001 * 1234.0

    assert np.allclose(fields.mortality, expected_mortality)


def test_evaluate_model_fields_propagates_derived_status_field():
    x0 = build_initial_condition()
    p = build_parameters()
    c = build_context()

    state = build_initial_state(x0, p, c)

    status_field = np.ones_like(state.U) * 0.75

    derived = SimpleNamespace(
        total_mass=1234.0,
        status_field=status_field,
    )

    fields = evaluate_state_model_fields(
        p,
        state,
        derived=derived,
        context=c,
    )

    assert fields.status is not None
    assert np.allclose(fields.status, status_field)


def test_evaluate_model_fields_supports_local_derived_status_law():
    x0 = build_initial_condition()
    p = build_parameters()
    c = build_context()

    state = build_initial_state(x0, p, c)

    grid = p.numerics.grid

    status_field = np.zeros_like(state.U)

    for i, x in enumerate(grid.x):
        for j, y in enumerate(grid.y):
            status_field[i, j] = x + y

    derived = SimpleNamespace(
        total_mass=1234.0,
        status_field=status_field,
    )

    def status_dependent_height_growth(
        t,
        x,
        y,
        state=None,
        derived=None,
        context=None,
        parameters=None,
    ):
        # Here we deliberately reconstruct the grid index from x and y
        # for test purposes. This is not meant as a production pattern.
        grid = parameters["grid"]

        i = int(np.argmin(np.abs(grid.x - x)))
        j = int(np.argmin(np.abs(grid.y - y)))

        return parameters["base"] * (1.0 - derived.status_field[i, j])

    height_growth_law = CoefficientLaw(
        name="status_dependent_height_growth_test",
        function=status_dependent_height_growth,
        parameters={
            "base": 0.5,
            "grid": grid,
        },
        units="normalized_height/year",
    )

    modified_model = replace(
        p.model,
        height_growth_law=height_growth_law,
    )

    modified_parameters = replace(
        p,
        model=modified_model,
    )

    fields = evaluate_state_model_fields(
        modified_parameters,
        state,
        derived=derived,
        context=c,
    )

    expected_height_growth = 0.5 * (1.0 - status_field)

    assert np.allclose(fields.height_growth, expected_height_growth)