"""
Model laws and coefficient evaluation for PyDynamicForest.

This module contains utilities to evaluate the scientific model laws
defined in ModelParameters on the numerical grid.

It remains separate from:
    - initial condition construction,
    - numerical operators,
    - solver orchestration,
    - diagnostics and plotting.
"""

import numpy as np

from pydynamicforest.types import CoefficientLaw, Parameters


def evaluate_coefficient_on_grid(
    law: CoefficientLaw,
    p: Parameters,
    time: float,
) -> np.ndarray:
    """
    Evaluate a coefficient law on the spatial grid at a given time.

    Parameters
    ----------
    law:
        CoefficientLaw containing a callable function f(t, x, y).
    p:
        Full Parameters object.
    time:
        Time at which the coefficient is evaluated.

    Returns
    -------
    np.ndarray
        Array of shape (nx, ny) containing law(time, x_i, y_j).
    """

    grid = p.numerics.grid

    values = np.zeros((grid.nx, grid.ny), dtype=float)

    for i, x in enumerate(grid.x):
        for j, y in enumerate(grid.y):
            values[i, j] = law.function(time, x, y)

    return values


def evaluate_diffusion(p: Parameters, time: float) -> np.ndarray:
    """
    Evaluate the diffusion coefficient on the grid.
    """

    return evaluate_coefficient_on_grid(
        law=p.model.diffusion_law,
        p=p,
        time=time,
    )


def evaluate_mortality(p: Parameters, time: float) -> np.ndarray:
    """
    Evaluate the mortality coefficient on the grid.
    """

    return evaluate_coefficient_on_grid(
        law=p.model.mortality_law,
        p=p,
        time=time,
    )


def evaluate_height_growth(p: Parameters, time: float) -> np.ndarray:
    """
    Evaluate the height growth velocity on the grid.
    """

    return evaluate_coefficient_on_grid(
        law=p.model.height_growth_law,
        p=p,
        time=time,
    )


def evaluate_dbh_growth(p: Parameters, time: float) -> np.ndarray:
    """
    Evaluate the DBH growth velocity on the grid.
    """

    return evaluate_coefficient_on_grid(
        law=p.model.dbh_growth_law,
        p=p,
        time=time,
    )


def evaluate_model_fields(p: Parameters, time: float) -> dict[str, np.ndarray]:
    """
    Evaluate all model coefficient fields at a given time.

    Returns a dictionary containing:
        - diffusion
        - mortality
        - height_growth
        - dbh_growth
    """

    return {
        "diffusion": evaluate_diffusion(p, time),
        "mortality": evaluate_mortality(p, time),
        "height_growth": evaluate_height_growth(p, time),
        "dbh_growth": evaluate_dbh_growth(p, time),
    }


def check_model_fields_are_finite(fields: dict[str, np.ndarray]) -> bool:
    """
    Check that all evaluated coefficient fields contain finite values.
    """

    return all(np.all(np.isfinite(values)) for values in fields.values())


def check_model_fields_shapes(
    fields: dict[str, np.ndarray],
    expected_shape: tuple[int, int],
) -> bool:
    """
    Check that all evaluated coefficient fields have the expected shape.
    """

    return all(values.shape == expected_shape for values in fields.values())
