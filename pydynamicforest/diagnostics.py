"""
Forest diagnostics for PyDynamicForest.

This module contains post-processing functions that compute interpretable
forest indicators from a State or from a density array U.

Diagnostics are kept separate from the solver.
"""

import numpy as np

from pydynamicforest.numerics import integrate_2d_trapezoidal
from pydynamicforest.types import Parameters, State


def trapezoidal_mass(U: np.ndarray, p: Parameters) -> float:
    """
    Compute total population mass using the 2D trapezoidal rule.

    This is the preferred diagnostic mass in the refactored code.
    """

    grid = p.numerics.grid
    return integrate_2d_trapezoidal(U, grid.dx, grid.dy)


def legacy_mass(U: np.ndarray, p: Parameters) -> float:
    """
    Compute total population mass using the legacy formula.

    Legacy formula:
        dx * dy * np.sum(U[1:, 1:])

    This is intentionally kept for regression comparisons with the
    original script.
    """

    grid = p.numerics.grid
    return float(grid.dx * grid.dy * np.sum(U[1:, 1:]))


def total_mass(U: np.ndarray, p: Parameters) -> float:
    """
    Compute total population mass.

    By default, this function uses the trapezoidal mass convention.
    It is kept as the main diagnostic mass function for backward
    compatibility in the refactored code.
    """

    return trapezoidal_mass(U, p)


def physical_height_grid(p: Parameters) -> np.ndarray:
    """
    Return height grid in physical units.
    """

    grid = p.numerics.grid
    Hphys = p.model.physical_scales.height_scale
    return grid.x * Hphys


def physical_dbh_grid(p: Parameters) -> np.ndarray:
    """
    Return DBH grid in physical units.
    """

    grid = p.numerics.grid
    Dphys = p.model.physical_scales.dbh_scale
    return grid.y * Dphys


def basal_area(U: np.ndarray, p: Parameters) -> float:
    """
    Compute basal area in m²/ha.

    Formula:
        G = pi / 4 * integral d² u(h, d) dh dd

    The density U is defined on normalized coordinates.
    DBH is converted to physical units before computing d².
    """

    grid = p.numerics.grid
    d_phys = physical_dbh_grid(p)

    D2 = d_phys[np.newaxis, :] ** 2

    integrand = (np.pi / 4.0) * D2 * U

    return integrate_2d_trapezoidal(integrand, grid.dx, grid.dy)


def top_height(
    U: np.ndarray,
    p: Parameters,
    target_stems_per_ha: float = 100.0,
) -> float:
    """
    Approximate top height.

    The top height is computed as the mean height of the target number
    of stems per hectare with the largest DBH.

    This reproduces the logic of the legacy code, but uses a more explicit
    structure.
    """

    grid = p.numerics.grid

    h_phys = physical_height_grid(p)
    d_phys = physical_dbh_grid(p)

    cells = []

    for i in range(grid.nx):
        for j in range(grid.ny):
            number_of_trees = grid.dx * grid.dy * U[i, j]

            if number_of_trees > 0.0:
                cells.append(
                    (
                        d_phys[j],
                        h_phys[i],
                        number_of_trees,
                    )
                )

    if not cells:
        return float("nan")

    cells.sort(key=lambda z: z[0], reverse=True)

    total_trees = 0.0
    height_sum = 0.0

    for dbh, height, number_trees in cells:
        remaining = target_stems_per_ha - total_trees
        used_trees = min(number_trees, remaining)

        height_sum += used_trees * height
        total_trees += used_trees

        if total_trees >= target_stems_per_ha:
            break

    if total_trees <= 0.0:
        return float("nan")

    return height_sum / total_trees


def minimum_density(U: np.ndarray) -> float:
    """
    Return the minimum density value.
    """

    return float(np.min(U))


def height_distribution(U: np.ndarray, p: Parameters) -> tuple[np.ndarray, np.ndarray]:
    """
    Compute marginal distribution by height class.

    Returns:
        h_phys, counts
    """

    grid = p.numerics.grid
    h_phys = physical_height_grid(p)

    counts = grid.dx * grid.dy * np.sum(U, axis=1)

    return h_phys, counts


def dbh_distribution(U: np.ndarray, p: Parameters) -> tuple[np.ndarray, np.ndarray]:
    """
    Compute marginal distribution by DBH class.

    Returns:
        dbh_cm, counts
    """

    grid = p.numerics.grid
    d_phys = physical_dbh_grid(p)
    dbh_cm = d_phys * 100.0

    counts = grid.dx * grid.dy * np.sum(U, axis=0)

    return dbh_cm, counts


def state_diagnostics(state: State, p: Parameters) -> dict[str, float]:
    """
    Compute a minimal diagnostic dictionary for a State.
    """

    return {
        "time": state.time,
        "age": state.age,
        "total_mass": total_mass(state.U, p),
        "legacy_mass": legacy_mass(state.U, p),
        "minimum_density": minimum_density(state.U),
        "top_height": top_height(state.U, p),
        "basal_area": basal_area(state.U, p),
    } 


def mass_diagnostics(U: np.ndarray, p: Parameters) -> dict[str, float]:
    """
    Return both mass conventions for comparison and traceability.
    """

    trap_mass = trapezoidal_mass(U, p)
    leg_mass = legacy_mass(U, p)

    return {
        "trapezoidal_mass": trap_mass,
        "legacy_mass": leg_mass,
        "absolute_difference": abs(trap_mass - leg_mass),
    }
