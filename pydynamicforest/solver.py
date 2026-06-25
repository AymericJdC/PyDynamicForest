"""
Solver routines for PyDynamicForest.

This module contains the time-stepping logic.

At this stage, we implement a dense legacy-like one-step solver:
    state_next = advance_one_step_dense_legacy(state, p)

The purpose is to reproduce the original numerical logic before later
improving the implementation.
"""

import numpy as np

from pydynamicforest.model import evaluate_model_fields
from pydynamicforest.numerics import (
    compute_derived_quantities,
    flatten_index,
)
from pydynamicforest.types import Parameters, State


def compute_transport_legacy(
    state: State,
    p: Parameters,
    derived,
    fields: dict[str, np.ndarray],
) -> np.ndarray:
    """
    Compute the explicit upwind transport term.

    This function reproduces the transport discretization of the legacy code.

    The transported quantity is S[u] * u, where S is the status field.
    """

    U = state.U
    J = derived.cumulative_distribution
    S = derived.status_field

    Ch = fields["height_growth"]
    Cd = fields["dbh_growth"]

    grid = p.numerics.grid
    nx = grid.nx
    ny = grid.ny
    dx = grid.dx
    dy = grid.dy

    den = max(derived.total_mass, p.numerics.epsilon_zero_mass)

    transport = np.zeros_like(U)

    for i in range(nx):
        for j in range(ny):
            Sij = S[i, j]

            upwindx_plus = 0.0
            upwindx_minus = 0.0
            upwindy_plus = 0.0
            upwindy_minus = 0.0

            # Right face in x direction
            if i < nx - 1:
                condx_plus = Ch[i, j] + Ch[i + 1, j]

                if condx_plus >= 0.0:
                    upwindx_plus = Sij * U[i, j]
                else:
                    upwindx_plus = (J[i + 1, j] / den) * U[i + 1, j]

            # Left face in x direction
            if i > 0:
                condx_minus = Ch[i, j] + Ch[i - 1, j]

                if condx_minus >= 0.0:
                    upwindx_minus = (J[i - 1, j] / den) * U[i - 1, j]
                else:
                    upwindx_minus = Sij * U[i, j]

            # Upper face in y direction
            if j < ny - 1:
                condy_plus = Cd[i, j] + Cd[i, j + 1]

                if condy_plus >= 0.0:
                    upwindy_plus = Sij * U[i, j]
                else:
                    upwindy_plus = (J[i, j + 1] / den) * U[i, j + 1]

            # Lower face in y direction
            if j > 0:
                condy_minus = Cd[i, j] + Cd[i, j - 1]

                if condy_minus >= 0.0:
                    upwindy_minus = (J[i, j - 1] / den) * U[i, j - 1]
                else:
                    upwindy_minus = Sij * U[i, j]

            # Interior points
            if i > 0 and i < nx - 1 and j > 0 and j < ny - 1:
                transport[i, j] = (
                    (
                        0.5 * (Ch[i + 1, j] + Ch[i, j]) * upwindx_plus
                        - 0.5 * (Ch[i, j] + Ch[i - 1, j]) * upwindx_minus
                    )
                    / dx
                    + (
                        0.5 * (Cd[i, j + 1] + Cd[i, j]) * upwindy_plus
                        - 0.5 * (Cd[i, j] + Cd[i, j - 1]) * upwindy_minus
                    )
                    / dy
                )

            # Left boundary
            elif i == 0 and j > 0 and j < ny - 1:
                transport[i, j] = (
                    (
                        0.5 * (Ch[i + 1, j] + Ch[i, j]) * upwindx_plus
                    )
                    / dx
                    + (
                        0.5 * (Cd[i, j + 1] + Cd[i, j]) * upwindy_plus
                        - 0.5 * (Cd[i, j] + Cd[i, j - 1]) * upwindy_minus
                    )
                    / dy
                )

            # Right boundary
            elif i == nx - 1 and j > 0 and j < ny - 1:
                transport[i, j] = (
                    (
                        -0.5 * (Ch[i, j] + Ch[i - 1, j]) * upwindx_minus
                    )
                    / dx
                    + (
                        0.5 * (Cd[i, j + 1] + Cd[i, j]) * upwindy_plus
                        - 0.5 * (Cd[i, j] + Cd[i, j - 1]) * upwindy_minus
                    )
                    / dy
                )

            # Bottom boundary
            elif j == 0 and i < nx - 1 and i > 0:
                transport[i, j] = (
                    (
                        0.5 * (Ch[i + 1, j] + Ch[i, j]) * upwindx_plus
                        - 0.5 * (Ch[i, j] + Ch[i - 1, j]) * upwindx_minus
                    )
                    / dx
                    + (
                        0.5 * (Cd[i, j + 1] + Cd[i, j]) * upwindy_plus
                    )
                    / dy
                )

            # Top boundary
            elif j == ny - 1 and i < nx - 1 and i > 0:
                transport[i, j] = (
                    (
                        0.5 * (Ch[i + 1, j] + Ch[i, j]) * upwindx_plus
                        - 0.5 * (Ch[i, j] + Ch[i - 1, j]) * upwindx_minus
                    )
                    / dx
                    + (
                        -0.5 * (Cd[i, j] + Cd[i, j - 1]) * upwindy_minus
                    )
                    / dy
                )

            # Bottom-left corner
            elif i == 0 and j == 0:
                transport[i, j] = (
                    0.5 * (Ch[i + 1, j] + Ch[i, j]) * upwindx_plus / dx
                    + 0.5 * (Cd[i, j + 1] + Cd[i, j]) * upwindy_plus / dy
                )

            # Top-left corner
            elif i == 0 and j == ny - 1:
                transport[i, j] = (
                    0.5 * (Ch[i + 1, j] + Ch[i, j]) * upwindx_plus / dx
                    - 0.5 * (Cd[i, j] + Cd[i, j - 1]) * upwindy_minus / dy
                )

            # Bottom-right corner
            elif i == nx - 1 and j == 0:
                transport[i, j] = (
                    -0.5 * (Ch[i, j] + Ch[i - 1, j]) * upwindx_minus / dx
                    + 0.5 * (Cd[i, j + 1] + Cd[i, j]) * upwindy_plus / dy
                )

            # Top-right corner
            elif i == nx - 1 and j == ny - 1:
                transport[i, j] = (
                    -0.5 * (Ch[i, j] + Ch[i - 1, j]) * upwindx_minus / dx
                    - 0.5 * (Cd[i, j] + Cd[i, j - 1]) * upwindy_minus / dy
                )

    return transport


def assemble_dense_legacy_system(
    state: State,
    p: Parameters,
    derived,
    fields_next: dict[str, np.ndarray],
    transport: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Assemble the dense linear system A U^{n+1} = b.

    This reproduces the legacy implicit diffusion-reaction system with
    explicit transport.
    """

    U = state.U
    S = derived.status_field

    grid = p.numerics.grid
    time = p.numerics.time

    nx = grid.nx
    ny = grid.ny
    dx = grid.dx
    dy = grid.dy
    dt = time.dt

    diffusion = fields_next["diffusion"]
    mortality = fields_next["mortality"]

    n_unknowns = nx * ny

    A = np.zeros((n_unknowns, n_unknowns), dtype=float)
    b = np.zeros(n_unknowns, dtype=float)

    for i in range(nx):
        for j in range(ny):
            if i < nx - 1:
                aE = 0.5 * (diffusion[i, j] + diffusion[i + 1, j]) / (dx * dx)
            else:
                aE = 0.0

            if i > 0:
                aW = 0.5 * (diffusion[i, j] + diffusion[i - 1, j]) / (dx * dx)
            else:
                aW = 0.0

            if j < ny - 1:
                aN = 0.5 * (diffusion[i, j] + diffusion[i, j + 1]) / (dy * dy)
            else:
                aN = 0.0

            if j > 0:
                aS = 0.5 * (diffusion[i, j] + diffusion[i, j - 1]) / (dy * dy)
            else:
                aS = 0.0

            aP = aE + aW + aN + aS

            row = flatten_index(i, j, ny)

            Sij = S[i, j]

            A[row, row] = (
                1.0
                + dt * aP
                + dt * mortality[i, j] * (1.0 - Sij)
            )

            if i < nx - 1:
                A[row, flatten_index(i + 1, j, ny)] = -dt * aE

            if i > 0:
                A[row, flatten_index(i - 1, j, ny)] = -dt * aW

            if j < ny - 1:
                A[row, flatten_index(i, j + 1, ny)] = -dt * aN

            if j > 0:
                A[row, flatten_index(i, j - 1, ny)] = -dt * aS

            b[row] = U[i, j] - dt * transport[i, j]

    return A, b


def advance_one_step_dense_legacy(
    state: State,
    p: Parameters,
) -> State:
    """
    Advance the model by one time step using the dense legacy scheme.

    This function intentionally keeps the legacy dense linear algebra
    approach. It will later be replaced or complemented by a sparse solver.
    """

    time = p.numerics.time
    dt = time.dt

    t_current = state.time
    t_next = t_current + dt

    derived = compute_derived_quantities(state, p)

    fields_current = evaluate_model_fields(p, t_current)
    fields_next = evaluate_model_fields(p, t_next)

    transport = compute_transport_legacy(
        state=state,
        p=p,
        derived=derived,
        fields=fields_current,
    )

    A, b = assemble_dense_legacy_system(
        state=state,
        p=p,
        derived=derived,
        fields_next=fields_next,
        transport=transport,
    )

    U_next_flat = np.linalg.solve(A, b)

    grid = p.numerics.grid
    U_next = U_next_flat.reshape((grid.nx, grid.ny))

    age_next = state.age + dt

    return State(
        time=t_next,
        age=age_next,
        U=U_next,
        step_index=state.step_index + 1,
    )