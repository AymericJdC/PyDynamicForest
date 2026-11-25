# SPDX-License-Identifier: LGPL-3.0-or-later
"""Sensitivity of height diagnostics to the completion of missing heights.

Two analyses (Online Resource 1, Table S5):

- diagnostics computed directly from the tree records with the residual
  completion and with a deterministic completion (one height per tree, the
  weighted mean of its components);
- comparison of the measured heights with the simulated mean height
  conditional on DBH, which uses no completed height.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from pydynamicforest.observation_operators import physical_dbh_nodes, physical_height_nodes


def tree_level_diagnostics(h: np.ndarray, d: np.ndarray, w: np.ndarray, dominant_stems_ha: float = 100.0) -> dict:
    h, d, w = (np.asarray(x, dtype=float) for x in (h, d, w))
    N = w.sum()
    hm = (w * h).sum() / N
    order = np.argsort(-d)
    cum = np.cumsum(w[order])
    take = np.clip(dominant_stems_ha - (cum - w[order]), 0.0, w[order])
    h0 = (take * h[order]).sum() / dominant_stems_ha
    dm = (w * d).sum() / N
    sh = np.sqrt((w * (h - hm) ** 2).sum() / N)
    sd = np.sqrt((w * (d - dm) ** 2).sum() / N)
    rho = (w * (h - hm) * (d - dm)).sum() / N / (sh * sd)
    return {"Hm": float(hm), "H0": float(h0), "H0_minus_Hm": float(h0 - hm), "rho_HD": float(rho)}


def deterministic_completion(rows: pd.DataFrame) -> pd.DataFrame:
    """One record per tree: weighted mean height of its components, total weight."""

    weighted = (rows.height_m * rows.weight_ha).groupby(rows.tree_id).sum()
    g = rows.groupby("tree_id")
    weight = g.weight_ha.sum()
    return pd.DataFrame({"height_m": weighted / weight, "diameter_cm": g.diameter_cm.first(), "weight_ha": weight})


def conditional_mean_height(U: np.ndarray, p) -> tuple[np.ndarray, np.ndarray]:
    """Simulated mean height conditional on DBH, at the DBH nodes (cm)."""

    h = physical_height_nodes(p)
    d = physical_dbh_nodes(p, unit="cm")
    wh = np.full(len(h), h[1] - h[0])
    wh[[0, -1]] /= 2
    mass = (U * wh[:, None]).sum(axis=0)
    with np.errstate(invalid="ignore", divide="ignore"):
        m = np.where(mass > 1e-9, (h[:, None] * U * wh[:, None]).sum(axis=0) / np.maximum(mass, 1e-300), np.nan)
    return d, m


def completion_sensitivity(assigned: pd.DataFrame, simulated: dict, p, initial_year: int) -> list[dict]:
    """Rows of Table S5, one per inventory."""

    out = []
    for year in sorted(assigned.year.unique()):
        rows = assigned[assigned.year == year]
        residual = tree_level_diagnostics(rows.height_m, rows.diameter_cm, rows.weight_ha)
        det = deterministic_completion(rows)
        deterministic = tree_level_diagnostics(det.height_m, det.diameter_cm, det.weight_ha)
        row = {"year": int(year),
               **{f"{k}_residual": v for k, v in residual.items()},
               **{f"{k}_deterministic": v for k, v in deterministic.items()},
               "measured_n": 0, "measured_minus_simulated_m": float("nan"), "standard_error_m": float("nan"),
               "share_measured_taller": float("nan")}
        measured = rows[rows.get("height_component_kind", pd.Series(index=rows.index, dtype=str)) == "measured_total_height"]
        if len(measured) > 1 and int(year) != initial_year and int(year) in simulated:
            d, m = conditional_mean_height(simulated[int(year)], p)
            ok = ~np.isnan(m)
            diff = measured.height_m.to_numpy() - np.interp(measured.diameter_cm.to_numpy(), d[ok], m[ok])
            row.update({"measured_n": int(len(diff)), "measured_minus_simulated_m": float(diff.mean()),
                        "standard_error_m": float(diff.std(ddof=1) / np.sqrt(len(diff))),
                        "share_measured_taller": float((diff > 0).mean())})
        out.append(row)
    return out
