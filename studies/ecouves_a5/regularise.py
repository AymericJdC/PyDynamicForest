# SPDX-License-Identifier: LGPL-3.0-or-later
"""Step 2: regularised height--DBH observations on the model grid.

Each height--DBH record of the assigned-height table is spread over the grid
nodes with a tensor-product triangular kernel whose half-widths are fixed in
physical units, and nodal masses are divided by the trapezoidal quadrature
weights. Because the kernel does not depend on the grid, the regularised
observations do not depend on the numerical resolution (up to quadrature).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from pydynamicforest.numerics import product_trapezoidal_weights
from pydynamicforest.observation_operators import physical_dbh_nodes, physical_height_nodes


def _kernel_weights(x: np.ndarray, nodes: np.ndarray, half_width: float):
    step = nodes[1] - nodes[0]
    if half_width <= 0:
        raise ValueError("kernel half-width must be positive")
    r = int(np.ceil(half_width / step)) + 1
    centre = np.rint(x / step).astype(int)
    idx = centre[:, None] + np.arange(-r, r + 1)[None, :]
    inside = (idx >= 0) & (idx < len(nodes))
    idx = np.clip(idx, 0, len(nodes) - 1)
    k = np.clip(1.0 - np.abs(nodes[idx] - x[:, None]) / half_width, 0.0, None) * inside
    total = k.sum(axis=1, keepdims=True)
    if np.any(total <= 0):
        raise ValueError("a record has no grid node within the kernel support")
    return idx, k / total


def regularise_records(
    height_m: np.ndarray,
    dbh_cm: np.ndarray,
    weight_ha: np.ndarray,
    p,
    half_width_height_m: float,
    half_width_dbh_cm: float,
) -> np.ndarray:
    """Nodal density (trees/ha per unit of the normalised grid) of weighted records."""

    grid = p.numerics.grid
    h_nodes = physical_height_nodes(p)
    d_nodes = physical_dbh_nodes(p, unit="cm")
    h = np.asarray(height_m, dtype=float)
    d = np.asarray(dbh_cm, dtype=float)
    w = np.asarray(weight_ha, dtype=float)
    ih, kh = _kernel_weights(h, h_nodes, half_width_height_m)
    jd, kd = _kernel_weights(d, d_nodes, half_width_dbh_cm)
    mass = np.zeros((grid.nx, grid.ny))
    I = np.broadcast_to(ih[:, :, None], (len(h), ih.shape[1], jd.shape[1]))
    J = np.broadcast_to(jd[:, None, :], I.shape)
    V = w[:, None, None] * kh[:, :, None] * kd[:, None, :]
    np.add.at(mass, (I.ravel(), J.ravel()), V.ravel())
    return mass / product_trapezoidal_weights(p)


def regularise_inventory(assigned: pd.DataFrame, year: int, p, half_width_height_m: float, half_width_dbh_cm: float) -> np.ndarray:
    rows = assigned[assigned.year == year]
    if rows.empty:
        raise ValueError(f"no assigned heights for {year}")
    return regularise_records(rows.height_m.to_numpy(), rows.diameter_cm.to_numpy(),
                              rows.weight_ha.to_numpy(), p, half_width_height_m, half_width_dbh_cm)
