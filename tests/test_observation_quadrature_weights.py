from copy import deepcopy

import numpy as np
import pytest

from pydynamicforest.numerics import (
    dbh_trapezoidal_weights,
    height_trapezoidal_weights,
    integrate_2d_trapezoidal,
    product_trapezoidal_weights,
    trapezoidal_weights_1d,
)
from simulations.article_submission_legacy.config import ARTICLE_SUBMISSION_CONFIG
from simulations.article_submission_legacy.parameters import build_parameters


def make_parameters(nx=5, ny=4, x_min=0.0, x_max=1.0, y_min=0.0, y_max=1.0):
    config = deepcopy(ARTICLE_SUBMISSION_CONFIG)
    config["grid"].update(
        {
            "nx": nx,
            "ny": ny,
            "x_min": x_min,
            "x_max": x_max,
            "y_min": y_min,
            "y_max": y_max,
        }
    )
    return build_parameters(config)


def test_one_dimensional_weights_have_half_boundary_weights():
    weights = trapezoidal_weights_1d(5, spacing=0.25)

    np.testing.assert_allclose(weights, [0.125, 0.25, 0.25, 0.25, 0.125])
    assert np.sum(weights) == pytest.approx(1.0)


def test_grid_specific_weights_sum_to_coordinate_domain_lengths():
    p = make_parameters(
        nx=7,
        ny=6,
        x_min=0.2,
        x_max=1.0,
        y_min=-0.5,
        y_max=1.5,
    )

    height_weights = height_trapezoidal_weights(p)
    dbh_weights = dbh_trapezoidal_weights(p)

    assert np.sum(height_weights) == pytest.approx(0.8)
    assert np.sum(dbh_weights) == pytest.approx(2.0)
    assert height_weights[0] == pytest.approx(0.5 * p.numerics.grid.dx)
    assert dbh_weights[-1] == pytest.approx(0.5 * p.numerics.grid.dy)


def test_product_weights_use_height_then_dbh_axis_order():
    p = make_parameters(nx=5, ny=4)
    weights = product_trapezoidal_weights(p)

    assert weights.shape == (5, 4)
    assert weights[0, 0] == pytest.approx(0.25 * p.numerics.grid.dx * p.numerics.grid.dy)
    assert weights[2, 2] == pytest.approx(p.numerics.grid.dx * p.numerics.grid.dy)
    assert np.sum(weights) == pytest.approx(1.0)


def test_product_weights_match_existing_two_dimensional_integrator():
    p = make_parameters(nx=8, ny=6)
    grid = p.numerics.grid
    X, Y = np.meshgrid(grid.x, grid.y, indexing="ij")
    field = 2.0 + 3.0 * X - 4.0 * Y + X * Y

    weighted_value = float(np.sum(product_trapezoidal_weights(p) * field))
    existing_value = integrate_2d_trapezoidal(field, grid.dx, grid.dy)

    assert weighted_value == pytest.approx(existing_value, rel=1.0e-15, abs=1.0e-15)


@pytest.mark.parametrize(
    "field_builder, expected",
    [
        (lambda X, Y: np.ones_like(X), 1.0),
        (lambda X, Y: X, 0.5),
        (lambda X, Y: Y, 0.5),
        (lambda X, Y: X + Y, 1.0),
    ],
)
def test_product_rule_integrates_constant_and_linear_fields_exactly(
    field_builder,
    expected,
):
    p = make_parameters(nx=9, ny=7)
    grid = p.numerics.grid
    X, Y = np.meshgrid(grid.x, grid.y, indexing="ij")

    value = float(np.sum(product_trapezoidal_weights(p) * field_builder(X, Y)))

    assert value == pytest.approx(expected, rel=1.0e-14, abs=1.0e-14)


def test_minimal_two_by_two_grid_has_corner_weights_only():
    p = make_parameters(nx=2, ny=2)
    weights = product_trapezoidal_weights(p)

    np.testing.assert_allclose(weights, np.full((2, 2), 0.25))
    assert np.sum(weights) == pytest.approx(1.0)


@pytest.mark.parametrize(
    "n_points, spacing, message",
    [
        (1, 1.0, "At least two"),
        (3, 0.0, "strictly positive"),
        (3, -1.0, "strictly positive"),
    ],
)
def test_one_dimensional_weights_reject_invalid_grids(n_points, spacing, message):
    with pytest.raises(ValueError, match=message):
        trapezoidal_weights_1d(n_points, spacing)
