# SPDX-License-Identifier: LGPL-3.0-or-later
"""Quadrature-consistent stand-level observation operators.

The distributed state is integrated in normalized height-DBH coordinates.
Physical height and DBH values enter only through moments and unit conversion.
Historical diagnostics remain in :mod:`pydynamicforest.diagnostics`.
"""

from __future__ import annotations

import numpy as np

from pydynamicforest.numerics import (
    dbh_trapezoidal_weights,
    height_trapezoidal_weights,
    product_trapezoidal_weights,
)
from pydynamicforest.types import Parameters


def _validated_density(U: np.ndarray, p: Parameters) -> np.ndarray:
    """Return a non-negative density after explicit tolerance validation."""

    expected_shape = (p.numerics.grid.nx, p.numerics.grid.ny)
    if U.shape != expected_shape:
        raise ValueError(
            f"Density shape {U.shape} does not match grid shape {expected_shape}."
        )
    if not np.all(np.isfinite(U)):
        raise ValueError("Density must contain only finite values.")

    minimum = float(np.min(U))
    tolerance = p.numerics.positivity_tolerance
    if minimum < -tolerance:
        raise ValueError(
            "Observation operators require a non-negative density. "
            f"Minimum value: {minimum}."
        )
    return np.maximum(U, 0.0)


def physical_height_nodes(p: Parameters) -> np.ndarray:
    """Return height nodes in metres."""

    return p.numerics.grid.x * p.model.physical_scales.height_scale


def physical_dbh_nodes(p: Parameters, unit: str = "m") -> np.ndarray:
    """Return DBH nodes in metres or centimetres."""

    values_m = p.numerics.grid.y * p.model.physical_scales.dbh_scale
    if unit == "m":
        return values_m
    if unit == "cm":
        return 100.0 * values_m
    raise ValueError("DBH unit must be 'm' or 'cm'.")


def stand_density(U: np.ndarray, p: Parameters) -> float:
    """Return total stem number in trees per hectare."""

    density = _validated_density(U, p)
    return float(np.sum(product_trapezoidal_weights(p) * density))


def mean_height(U: np.ndarray, p: Parameters) -> float:
    """Return arithmetic mean tree height in metres."""

    density = _validated_density(U, p)
    total = stand_density(density, p)
    if total <= 0.0:
        return float("nan")
    height = physical_height_nodes(p)[:, None]
    return float(np.sum(product_trapezoidal_weights(p) * height * density) / total)


def quadratic_mean_dbh(U: np.ndarray, p: Parameters, unit: str = "m") -> float:
    """Return quadratic mean DBH in metres or centimetres."""

    density = _validated_density(U, p)
    total = stand_density(density, p)
    if total <= 0.0:
        return float("nan")
    dbh_m = physical_dbh_nodes(p, unit="m")[None, :]
    value_m = float(
        np.sqrt(np.sum(product_trapezoidal_weights(p) * dbh_m**2 * density) / total)
    )
    if unit == "m":
        return value_m
    if unit == "cm":
        return 100.0 * value_m
    raise ValueError("DBH unit must be 'm' or 'cm'.")


def basal_area_consistent(U: np.ndarray, p: Parameters) -> float:
    """Return basal area in square metres per hectare."""

    density = _validated_density(U, p)
    dbh_m = physical_dbh_nodes(p, unit="m")[None, :]
    second_moment = float(
        np.sum(product_trapezoidal_weights(p) * dbh_m**2 * density)
    )
    return 0.25 * np.pi * second_moment


def height_marginal_density(
    U: np.ndarray,
    p: Parameters,
) -> tuple[np.ndarray, np.ndarray]:
    """Return height nodes and marginal density in trees ha-1 m-1."""

    density = _validated_density(U, p)
    dbh_weights = dbh_trapezoidal_weights(p)
    height_scale = p.model.physical_scales.height_scale
    marginal_per_m = (density @ dbh_weights) / height_scale
    return physical_height_nodes(p), marginal_per_m


def dbh_marginal_density(
    U: np.ndarray,
    p: Parameters,
    unit: str = "m",
) -> tuple[np.ndarray, np.ndarray]:
    """Return DBH nodes and marginal density per metre or per centimetre.

    For ``unit='m'``, density units are trees ha-1 m-1. For ``unit='cm'``,
    values are converted to trees ha-1 cm-1 and nodes to centimetres.
    """

    density = _validated_density(U, p)
    height_weights = height_trapezoidal_weights(p)
    dbh_scale = p.model.physical_scales.dbh_scale
    marginal_per_m = (height_weights @ density) / dbh_scale

    if unit == "m":
        return physical_dbh_nodes(p, unit="m"), marginal_per_m
    if unit == "cm":
        return physical_dbh_nodes(p, unit="cm"), marginal_per_m / 100.0
    raise ValueError("DBH unit must be 'm' or 'cm'.")
