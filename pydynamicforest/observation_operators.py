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


def _piecewise_linear_tail_integral(
    nodes: np.ndarray,
    values: np.ndarray,
    threshold: float,
) -> float:
    """Integrate a piecewise-linear function from ``threshold`` to the last node."""

    if threshold <= nodes[0]:
        return float(np.trapezoid(values, nodes))
    if threshold >= nodes[-1]:
        return 0.0

    interval = int(np.searchsorted(nodes, threshold, side="right") - 1)
    left = nodes[interval]
    right = nodes[interval + 1]
    width = right - left
    fraction = (threshold - left) / width
    threshold_value = values[interval] + fraction * (
        values[interval + 1] - values[interval]
    )

    partial = 0.5 * (threshold_value + values[interval + 1]) * (right - threshold)
    if interval + 1 < len(nodes) - 1:
        partial += float(np.trapezoid(values[interval + 1 :], nodes[interval + 1 :]))
    return float(partial)


def _threshold_from_piecewise_linear_tail(
    nodes: np.ndarray,
    marginal: np.ndarray,
    target: float,
    *,
    max_iterations: int = 80,
) -> tuple[float, int]:
    """Return the threshold whose piecewise-linear upper tail equals ``target``."""

    interval_areas = 0.5 * (marginal[:-1] + marginal[1:]) * np.diff(nodes)
    accumulated = 0.0

    for interval in range(len(nodes) - 2, -1, -1):
        area = float(interval_areas[interval])
        if accumulated + area < target:
            accumulated += area
            continue

        remaining = target - accumulated
        left = float(nodes[interval])
        right = float(nodes[interval + 1])

        # Bisection is deliberately used instead of an explicit quadratic
        # formula. It remains stable for nearly constant or nearly empty slopes.
        for _ in range(max_iterations):
            midpoint = 0.5 * (left + right)
            local_tail = _piecewise_linear_tail_integral(
                nodes[interval : interval + 2],
                marginal[interval : interval + 2],
                midpoint,
            )
            if local_tail > remaining:
                left = midpoint
            else:
                right = midpoint

        return 0.5 * (left + right), interval

    # The target equals the total mass up to floating-point roundoff.
    return float(nodes[0]), 0


def continuous_dominant_height_details(
    U: np.ndarray,
    p: Parameters,
    target_stems_per_ha: float = 100.0,
) -> dict[str, float | int]:
    """Return a continuous-DBH dominant-height estimate and threshold details.

    The DBH marginal density and its height-moment density are reconstructed by
    piecewise-linear interpolation in physical DBH. The threshold DBH is chosen
    so that the interpolated upper tail contains the target number of stems.
    The dominant height is the corresponding upper-tail height moment divided
    by the selected stem number.
    """

    if target_stems_per_ha <= 0.0:
        raise ValueError("target_stems_per_ha must be strictly positive.")

    density = _validated_density(U, p)
    dbh_nodes_m, dbh_marginal_per_m = dbh_marginal_density(
        density,
        p,
        unit="m",
    )
    total = stand_density(density, p)

    if total <= 0.0:
        return {
            "dominant_height": float("nan"),
            "threshold_dbh": float("nan"),
            "selected_stems": 0.0,
            "total_stems": 0.0,
            "threshold_interval_index": -1,
        }

    selected = min(float(target_stems_per_ha), total)
    height_weights = height_trapezoidal_weights(p)
    height_m = physical_height_nodes(p)
    dbh_scale = p.model.physical_scales.dbh_scale
    height_moment_per_dbh_m = (
        (height_weights * height_m) @ density
    ) / dbh_scale

    if total <= target_stems_per_ha:
        threshold = float(dbh_nodes_m[0])
        interval = 0
    else:
        threshold, interval = _threshold_from_piecewise_linear_tail(
            dbh_nodes_m,
            dbh_marginal_per_m,
            selected,
        )

    selected_from_tail = _piecewise_linear_tail_integral(
        dbh_nodes_m,
        dbh_marginal_per_m,
        threshold,
    )
    height_moment = _piecewise_linear_tail_integral(
        dbh_nodes_m,
        height_moment_per_dbh_m,
        threshold,
    )
    dominant_height = height_moment / selected_from_tail

    return {
        "dominant_height": float(dominant_height),
        "threshold_dbh": float(threshold),
        "selected_stems": float(selected_from_tail),
        "total_stems": float(total),
        "threshold_interval_index": int(interval),
    }


def continuous_dominant_height(
    U: np.ndarray,
    p: Parameters,
    target_stems_per_ha: float = 100.0,
) -> float:
    """Return dominant height from a continuous piecewise-linear DBH tail."""

    return float(
        continuous_dominant_height_details(
            U,
            p,
            target_stems_per_ha=target_stems_per_ha,
        )["dominant_height"]
    )

