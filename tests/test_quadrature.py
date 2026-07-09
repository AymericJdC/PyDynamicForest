# SPDX-License-Identifier: LGPL-3.0-or-later
import numpy as np

from pydynamicforest.numerics import (
    trapezoidal_weights_2d,
    integrate_2d_trapezoidal,
)


def test_trapezoidal_weights_2d_shape_and_values():
    weights = trapezoidal_weights_2d(4, 5)

    assert weights.shape == (4, 5)

    # Corners
    assert weights[0, 0] == 0.25
    assert weights[0, -1] == 0.25
    assert weights[-1, 0] == 0.25
    assert weights[-1, -1] == 0.25

    # Edges
    assert weights[0, 2] == 0.5
    assert weights[-1, 2] == 0.5
    assert weights[2, 0] == 0.5
    assert weights[2, -1] == 0.5

    # Interior
    assert weights[1, 1] == 1.0


def test_integrate_constant_field_on_unit_square():
    nx = 11
    ny = 11

    V = np.ones((nx, ny))

    dx = 1.0 / (nx - 1)
    dy = 1.0 / (ny - 1)

    integral = integrate_2d_trapezoidal(V, dx, dy)

    assert np.isclose(integral, 1.0)


def test_integrate_linear_field_on_unit_square():
    nx = 21
    ny = 21

    x = np.linspace(0.0, 1.0, nx)
    y = np.linspace(0.0, 1.0, ny)

    X, Y = np.meshgrid(x, y, indexing="ij")

    V = X + Y

    dx = 1.0 / (nx - 1)
    dy = 1.0 / (ny - 1)

    integral = integrate_2d_trapezoidal(V, dx, dy)

    # Integral of x + y over [0,1]x[0,1] is 1.
    assert np.isclose(integral, 1.0)