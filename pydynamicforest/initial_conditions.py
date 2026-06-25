"""
Initial condition builders for PyDynamicForest.

This module converts conceptual InitialCondition objects into discretized
State objects on the numerical grid.
"""

import numpy as np

from pydynamicforest.types import InitialCondition, Parameters, SimulationContext, State


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


def integrate_2d_trapezoidal(V: np.ndarray, dx: float, dy: float) -> float:
    """
    Integrate a 2D field using the tensor-product trapezoidal rule.
    """

    nx, ny = V.shape
    weights = trapezoidal_weights_2d(nx, ny)
    return float(dx * dy * np.sum(weights * V))


def build_gaussian_initial_density(
    x0: InitialCondition,
    p: Parameters,
) -> np.ndarray:
    """
    Build a normalized 2D Gaussian initial density on the model grid.

    The Gaussian parameters are given in physical units in x0 and converted
    to normalized coordinates using p.model.physical_scales.
    """

    grid = p.numerics.grid
    scales = p.model.physical_scales

    x = grid.x
    y = grid.y
    dx = grid.dx
    dy = grid.dy

    params = x0.distribution_parameters

    h0 = params["h0_physical"] / scales.height_scale
    d0 = params["d0_physical"] / scales.dbh_scale

    sigma_h = params["sigma_h_physical"] / scales.height_scale
    sigma_d = params["sigma_d_physical"] / scales.dbh_scale

    X, Y = np.meshgrid(x, y, indexing="ij")

    gaussian = np.exp(
        -((X - h0) ** 2) / (2.0 * sigma_h**2)
        -((Y - d0) ** 2) / (2.0 * sigma_d**2)
    )

    integral = integrate_2d_trapezoidal(gaussian, dx, dy)

    if integral <= 0.0:
        raise ValueError("Initial Gaussian integral is non-positive.")

    U0 = gaussian * x0.mass_target / integral

    return U0


def build_initial_state(
    x0: InitialCondition,
    p: Parameters,
    c: SimulationContext,
) -> State:
    """
    Build the initial State from an InitialCondition, Parameters and Context.

    This function is the first concrete realization of the conceptual API:

        state0 = build_initial_state(x0, p, c)
    """

    if x0.U0 is not None:
        U0 = np.array(x0.U0, dtype=float, copy=True)
    elif x0.distribution_kind == "gaussian_2d":
        U0 = build_gaussian_initial_density(x0, p)
    else:
        raise NotImplementedError(
            f"Unsupported initial distribution kind: {x0.distribution_kind}"
        )

    if np.any(~np.isfinite(U0)):
        raise ValueError("Initial density contains NaN or infinite values.")

    if np.min(U0) < -p.numerics.positivity_tolerance:
        raise ValueError("Initial density contains negative values.")

    return State(
        time=p.numerics.time.t_start,
        age=c.initial_age,
        U=U0,
        step_index=0,
    )