# SPDX-License-Identifier: LGPL-3.0-or-later
"""Independent short-run transcription of ``Modele2DImpliciteV3.py``.

This module provides a regression reference for the manuscript-associated
legacy scenario. It transcribes the cumulative status, explicit upwind
transport, implicit diffusion-reaction matrix, and original model coefficients.

The sparse matrix representation changes storage only. The discrete equations
and update order follow the transmitted script. The module deliberately does
not call PyDynamicForest solver assembly or transport functions.
"""

from __future__ import annotations

import numpy as np
from scipy.sparse import lil_matrix
from scipy.sparse.linalg import spsolve

from pydynamicforest.types import Parameters


DIFFUSION = 1.0e-5
MORTALITY = 0.033
HEIGHT_GROWTH_PHYSICAL = 1.66
DBH_GROWTH_PHYSICAL = 0.0155


def _cumulative_trapezoidal(U: np.ndarray, dx: float, dy: float) -> np.ndarray:
    """Reproduce the 2D cumulative trapezoidal recurrence in the script."""

    nx, ny = U.shape
    J = np.zeros_like(U, dtype=float)

    for i in range(1, nx):
        for j in range(1, ny):
            J[i, j] = (
                J[i - 1, j]
                + J[i, j - 1]
                - J[i - 1, j - 1]
                + 0.25
                * dx
                * dy
                * (U[i, j] + U[i - 1, j] + U[i, j - 1] + U[i - 1, j - 1])
            )

    return J


def _transport(
    U: np.ndarray,
    J: np.ndarray,
    Ch: np.ndarray,
    Cd: np.ndarray,
    dx: float,
    dy: float,
    epsilon_zero_mass: float,
) -> np.ndarray:
    """Reproduce the eight transport cases of the transmitted script."""

    nx, ny = U.shape
    transport = np.zeros_like(U, dtype=float)
    den = max(float(J[-1, -1]), epsilon_zero_mass)

    for i in range(nx):
        for j in range(ny):
            Sij = J[i, j] / den

            if i < nx - 1:
                ch_plus = 0.5 * (Ch[i, j] + Ch[i + 1, j])
                upwind_x_plus = (
                    Sij * U[i, j]
                    if ch_plus >= 0.0
                    else (J[i + 1, j] / den) * U[i + 1, j]
                )
                flux_x_plus = ch_plus * upwind_x_plus
            else:
                flux_x_plus = 0.0

            if i > 0:
                ch_minus = 0.5 * (Ch[i - 1, j] + Ch[i, j])
                upwind_x_minus = (
                    (J[i - 1, j] / den) * U[i - 1, j]
                    if ch_minus >= 0.0
                    else Sij * U[i, j]
                )
                flux_x_minus = ch_minus * upwind_x_minus
            else:
                flux_x_minus = 0.0

            if j < ny - 1:
                cd_plus = 0.5 * (Cd[i, j] + Cd[i, j + 1])
                upwind_y_plus = (
                    Sij * U[i, j]
                    if cd_plus >= 0.0
                    else (J[i, j + 1] / den) * U[i, j + 1]
                )
                flux_y_plus = cd_plus * upwind_y_plus
            else:
                flux_y_plus = 0.0

            if j > 0:
                cd_minus = 0.5 * (Cd[i, j - 1] + Cd[i, j])
                upwind_y_minus = (
                    (J[i, j - 1] / den) * U[i, j - 1]
                    if cd_minus >= 0.0
                    else Sij * U[i, j]
                )
                flux_y_minus = cd_minus * upwind_y_minus
            else:
                flux_y_minus = 0.0

            transport[i, j] = (
                (flux_x_plus - flux_x_minus) / dx
                + (flux_y_plus - flux_y_minus) / dy
            )

    return transport


def advance_one_reference_step(U: np.ndarray, p: Parameters) -> np.ndarray:
    """Advance one step with an independent transcription of the legacy scheme."""

    grid = p.numerics.grid
    dt = p.numerics.time.dt
    nx, ny = grid.nx, grid.ny
    dx, dy = grid.dx, grid.dy
    size = nx * ny

    X, Y = np.meshgrid(grid.x, grid.y, indexing="ij")
    Ch = (HEIGHT_GROWTH_PHYSICAL / p.model.physical_scales.height_scale) * (1.0 - X)
    Cd = (DBH_GROWTH_PHYSICAL / p.model.physical_scales.dbh_scale) * (1.0 - Y)

    J = _cumulative_trapezoidal(U, dx, dy)
    den = max(float(J[-1, -1]), p.numerics.epsilon_zero_mass)
    transport = _transport(U, J, Ch, Cd, dx, dy, p.numerics.epsilon_zero_mass)

    A = lil_matrix((size, size), dtype=float)
    b = np.zeros(size, dtype=float)

    def idx(i: int, j: int) -> int:
        return i * ny + j

    for i in range(nx):
        for j in range(ny):
            aE = DIFFUSION / (dx * dx) if i < nx - 1 else 0.0
            aW = DIFFUSION / (dx * dx) if i > 0 else 0.0
            aN = DIFFUSION / (dy * dy) if j < ny - 1 else 0.0
            aS = DIFFUSION / (dy * dy) if j > 0 else 0.0
            aP = aE + aW + aN + aS

            row = idx(i, j)
            status = J[i, j] / den

            A[row, row] = 1.0 + dt * aP + dt * MORTALITY * (1.0 - status)

            if i < nx - 1:
                A[row, idx(i + 1, j)] = -dt * aE
            if i > 0:
                A[row, idx(i - 1, j)] = -dt * aW
            if j < ny - 1:
                A[row, idx(i, j + 1)] = -dt * aN
            if j > 0:
                A[row, idx(i, j - 1)] = -dt * aS

            b[row] = U[i, j] - dt * transport[i, j]

    return np.asarray(spsolve(A.tocsr(), b)).reshape((nx, ny))


def run_reference_steps(U0: np.ndarray, p: Parameters, n_steps: int) -> np.ndarray:
    """Run a short legacy-reference trajectory and return its final density."""

    if n_steps < 0:
        raise ValueError("n_steps must be non-negative.")

    U = np.array(U0, dtype=float, copy=True)
    for _ in range(n_steps):
        U = advance_one_reference_step(U, p)
    return U
