# SPDX-License-Identifier: LGPL-3.0-or-later
"""
Numerical utilities for PyDynamicForest.

This module contains low-level numerical operations used by the solver:
    - grid indexing,
    - cumulative 2D integration,
    - status field computation,
    - derived numerical quantities.

The goal is to keep these operations separate from:
    - model definitions,
    - scenario definitions,
    - forest diagnostics,
    - plotting and exports.
"""

import numpy as np

from pydynamicforest.types import DerivedQuantities, Parameters, State


def flatten_index(i: int, j: int, ny: int) -> int:
    """
    Convert a 2D grid index (i, j) into a 1D vector index.

    This matches the legacy convention:

        p = i * Ny + j
    """

    return i * ny + j

def trapezoidal_weights_1d(
    n_points: int,
    spacing: float,
) -> np.ndarray:
    """Return dimensional one-dimensional trapezoidal quadrature weights.

    The first and last nodes receive half weights, and interior nodes receive
    full weights. The weights include ``spacing`` so their sum is the length
    of a uniform grid interval.
    """

    if n_points < 2:
        raise ValueError("At least two grid points are required.")
    if spacing <= 0.0:
        raise ValueError("Grid spacing must be strictly positive.")

    weights = np.full(n_points, spacing, dtype=float)
    weights[0] *= 0.5
    weights[-1] *= 0.5
    return weights


def height_trapezoidal_weights(p: Parameters) -> np.ndarray:
    """Return trapezoidal weights for the normalized height coordinate."""

    grid = p.numerics.grid
    return trapezoidal_weights_1d(grid.nx, grid.dx)


def dbh_trapezoidal_weights(p: Parameters) -> np.ndarray:
    """Return trapezoidal weights for the normalized DBH coordinate."""

    grid = p.numerics.grid
    return trapezoidal_weights_1d(grid.ny, grid.dy)


def product_trapezoidal_weights(p: Parameters) -> np.ndarray:
    """Return dimensional tensor-product weights in height-DBH axis order."""

    return np.outer(
        height_trapezoidal_weights(p),
        dbh_trapezoidal_weights(p),
    )


def trapezoidal_weights_2d(nx: int, ny: int) -> np.ndarray:
    """
    Return 2D trapezoidal weights on a tensor-product grid.

    Interior points have weight 1.
    Boundary points have weight 1/2 in the corresponding direction.
    Corners have weight 1/4.
    """

    wx = np.ones(nx)
    wy = np.ones(ny)

    wx[0] = 0.5
    wx[-1] = 0.5

    wy[0] = 0.5
    wy[-1] = 0.5

    return np.outer(wx, wy)


def integrate_2d_trapezoidal(
    V: np.ndarray,
    dx: float,
    dy: float,
) -> float:
    """
    Integrate a 2D field using the tensor-product trapezoidal rule.
    """

    nx, ny = V.shape
    weights = trapezoidal_weights_2d(nx, ny)

    return float(dx * dy * np.sum(weights * V))

def cumulative_integral_2d_trapezoidal(
    U: np.ndarray,
    dx: float,
    dy: float,
) -> np.ndarray:
    """
    Compute the cumulative 2D trapezoidal integral of U.

    J[i, j] approximates:

        integral_0^x_i integral_0^y_j U(xi, eta) d eta d xi

    This reproduces the cumulative integration logic used in the legacy code.
    """

    nx, ny = U.shape

    J = np.zeros((nx, ny), dtype=float)

    for i in range(1, nx):
        for j in range(1, ny):
            J[i, j] = (
                J[i - 1, j]
                + J[i, j - 1]
                - J[i - 1, j - 1]
                + 0.25
                * dx
                * dy
                * (
                    U[i, j]
                    + U[i - 1, j]
                    + U[i, j - 1]
                    + U[i - 1, j - 1]
                )
            )

    return J


def compute_status_field(
    cumulative_distribution: np.ndarray,
    total_mass: float,
    epsilon_zero_mass: float,
) -> np.ndarray:
    """
    Compute the status field S = J / total_mass.

    If total_mass is too small, epsilon_zero_mass is used to avoid division
    by zero.
    """

    denominator = max(total_mass, epsilon_zero_mass)
    return cumulative_distribution / denominator


def compute_derived_quantities(
    state: State,
    p: Parameters,
) -> DerivedQuantities:
    """
    Compute numerical quantities derived from a State.

    These quantities are used by the numerical scheme and by diagnostic
    checks, but they are not part of the minimal dynamic state.
    """

    grid = p.numerics.grid

    J = cumulative_integral_2d_trapezoidal(
        state.U,
        grid.dx,
        grid.dy,
    )

    total_mass = float(J[-1, -1])

    S = compute_status_field(
        cumulative_distribution=J,
        total_mass=total_mass,
        epsilon_zero_mass=p.numerics.epsilon_zero_mass,
    )

    min_u = float(np.min(state.U))

    return DerivedQuantities(
        cumulative_distribution=J,
        status_field=S,
        total_mass=total_mass,
        minimum_density=min_u,
    )


def check_status_field_bounds(
    S: np.ndarray,
    tolerance: float = 1e-12,
) -> bool:
    """
    Check whether the status field is approximately within [0, 1].
    """

    return bool(
        np.min(S) >= -tolerance
        and np.max(S) <= 1.0 + tolerance
    )
