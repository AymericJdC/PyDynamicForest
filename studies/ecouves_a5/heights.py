# SPDX-License-Identifier: LGPL-3.0-or-later
"""Step 1: completion of missing total heights.

For each inventory, a log-DBH allometry ``h = b0 + b1 log(D)`` is fitted by
least squares on the measured height--DBH pairs of plots A1, A2 and A5.
Measured A5 heights are kept unchanged. A tree without measured height is
represented by ``m`` components ``b0 + b1 log(D) + e_l``, where ``e_l`` are
the centred residuals of the fit, each with weight ``w / m``. The completed
sample therefore conserves stand density and carries the empirical residual
distribution around the allometry. Heights reported as ``HbH``/``ht_vv`` are
never used as total heights.

This module ports ``legacy/ecouves_prototype/build_ecouves_regularized_targets.py`` (steps 1 to 5 of
that script) into testable functions.
"""

from __future__ import annotations

import math
from collections.abc import Mapping

import numpy as np
import pandas as pd

ASSIGNED_COLUMNS = (
    "year", "age", "tree_id", "diameter_cm", "weight_ha", "height_m",
    "height_component_kind", "residual_component_m", "component_index",
    "component_count", "measured_height_available", "allometry_source_year",
)
FRANCOIS_SUFFIX = {2001: "01", 2016: "16", 2020: "20"}


def positive(value) -> float | None:
    try:
        x = float(value)
    except (TypeError, ValueError):
        return None
    return x if math.isfinite(x) and x > 0 else None


def tree_key(value) -> str:
    try:
        return str(int(float(value)))
    except (TypeError, ValueError):
        return str(value).strip()


def _height_in_metres(h: float) -> float:
    # some records are in centimetres
    return h / 100.0 if h > 100.0 else h


def fit_allometry(dbh_cm: np.ndarray, height_m: np.ndarray) -> dict:
    """Least-squares fit of ``h = b0 + b1 log(D)`` with centred residuals."""

    d = np.asarray(dbh_cm, dtype=float)
    h = np.asarray(height_m, dtype=float)
    if len(d) < 3 or np.any(d <= 0):
        raise ValueError("at least three positive diameters are required")
    X = np.column_stack([np.ones(len(d)), np.log(d)])
    beta = np.linalg.lstsq(X, h, rcond=None)[0]
    residuals = h - X @ beta
    residuals = residuals - residuals.mean()
    return {
        "beta0": float(beta[0]),
        "beta1": float(beta[1]),
        "residuals": residuals,
        "n": int(len(d)),
        "residual_sd_m": float(np.std(residuals, ddof=1)),
    }


def read_gis_measured_heights(path, plot_codes: Mapping[str, int], years=(1985, 1992)) -> pd.DataFrame:
    """Measured total heights (``hauteur_ech``) of the GIS Coop workbook."""

    measures = pd.read_excel(path, "Mesure", engine="xlrd")
    trees = pd.read_excel(path, "Arbre", engine="xlrd")
    z = trees.merge(measures[["co_placette", "no_mesure", "an_mesure"]],
                    on=["co_placette", "no_mesure"], how="left", validate="many_to_one")
    rows = []
    for plot, code in plot_codes.items():
        for year in years:
            for _, r in z[(z.co_placette == code) & (z.an_mesure == year)].iterrows():
                c, h = positive(r.circonference130), positive(r.hauteur_ech)
                if c is None or h is None:
                    continue
                rows.append({"plot": plot, "tree_id": tree_key(r.no_arb), "year": year,
                             "circumference_cm": c, "dbh_cm": c / math.pi,
                             "height_m": _height_in_metres(h), "origin": "GIS_hauteur_ech"})
    return pd.DataFrame(rows)


def read_francois_measured_heights(path, plots) -> pd.DataFrame:
    """Measured total heights (``Ht01``, ``Ht16``, ``Ht20``) of the field workbook."""

    rows = []
    for plot in plots:
        sheet = pd.read_excel(path, plot, engine="xlrd")
        for year, s in FRANCOIS_SUFFIX.items():
            for _, r in sheet.iterrows():
                c, h = positive(r.get(f"c{s}")), positive(r.get(f"Ht{s}"))
                if c is None or h is None:
                    continue
                rows.append({"plot": plot, "tree_id": tree_key(r.Num), "year": year,
                             "circumference_cm": c, "dbh_cm": c / math.pi,
                             "height_m": _height_in_metres(h), "origin": f"Francois_Ht{s}"})
    return pd.DataFrame(rows)


MEASURED_HEIGHT_COLUMNS = ("plot", "tree_id", "year", "circumference_cm", "height_m", "origin")


def read_measured_heights(path) -> pd.DataFrame:
    """Measured height table of the published dataset (``ecouves_measured_heights.csv``).

    The table holds the pairs read by :func:`read_gis_measured_heights` and
    :func:`read_francois_measured_heights`, in the same order; DBH is recomputed
    from the circumference exactly as in those readers.
    """

    # read as text and convert with Python's float(), which is exact for the
    # shortest round-trip representation written by pandas
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    missing = set(MEASURED_HEIGHT_COLUMNS) - set(df.columns)
    if missing:
        raise ValueError(f"measured-height table lacks columns {sorted(missing)}")
    df["year"] = df["year"].map(int)
    df["circumference_cm"] = df["circumference_cm"].map(float)
    df["height_m"] = df["height_m"].map(float)
    df.insert(4, "dbh_cm", df["circumference_cm"] / math.pi)
    return df[["plot", "tree_id", "year", "circumference_cm", "dbh_cm", "height_m", "origin"]]


def read_population(path, years) -> pd.DataFrame:
    """Trees of plot A5 included in the reference state, for the given years."""

    inv = pd.read_csv(path, encoding="utf-8-sig")
    included = inv["included_in_reference_state"].map(lambda v: str(v).strip().lower() in {"true", "1", "yes"})
    keep = ((inv["plot"].astype(str) == "Ecouves A5") & included
            & pd.to_numeric(inv.diameter_cm, errors="coerce").gt(0)
            & pd.to_numeric(inv.year, errors="coerce").isin(years))
    pop = inv[keep].copy()
    pop["year"] = pd.to_numeric(pop.year).astype(int)
    pop["tree_id"] = pop.tree_id.map(tree_key)
    missing = set(years) - set(pop.year)
    if missing:
        raise ValueError(f"inventory years missing from the population: {sorted(missing)}")
    return pop


def complete_heights(
    population: pd.DataFrame,
    measured: pd.DataFrame,
    allometry_source_year: Mapping[int, int],
    minimum_sample: int = 10,
    measured_plot: str = "A5",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return the assigned-height table and a per-inventory summary.

    ``population`` needs ``year, age, tree_id, diameter_cm, expansion_factor_ha``;
    ``measured`` needs ``plot, tree_id, year, dbh_cm, height_m``.
    """

    if measured.duplicated(["plot", "tree_id", "year"]).any():
        raise ValueError("duplicate measured heights for the same plot, tree and year")
    models = {}
    for year, source in allometry_source_year.items():
        sample = measured[measured.year == int(source)]
        if len(sample) < minimum_sample:
            raise ValueError(f"insufficient measured pairs for {source}: {len(sample)}")
        models[int(year)] = fit_allometry(sample.dbh_cm, sample.height_m)
    lookup = {(int(r.year), tree_key(r.tree_id)): float(r.height_m)
              for r in measured.loc[measured["plot"] == measured_plot].itertuples()}
    rows, summary = [], []
    for year in sorted(models):
        pop = population[population.year == year]
        model, res = models[year], models[year]["residuals"]
        n_measured = 0
        for r in pop.itertuples():
            d, w = float(r.diameter_cm), float(r.expansion_factor_ha)
            base = {"year": year, "age": int(round(float(r.age))), "tree_id": tree_key(r.tree_id),
                    "diameter_cm": d, "allometry_source_year": int(allometry_source_year[year])}
            h = lookup.get((year, tree_key(r.tree_id)))
            if h is not None:
                n_measured += 1
                rows.append({**base, "weight_ha": w, "height_m": h, "component_count": 1,
                             "height_component_kind": "measured_total_height", "residual_component_m": 0.0,
                             "component_index": 0, "measured_height_available": True})
            else:
                mu = model["beta0"] + model["beta1"] * math.log(d)
                for j, e in enumerate(res):
                    rows.append({**base, "weight_ha": w / len(res), "height_m": mu + float(e),
                                 "component_count": len(res),
                                 "height_component_kind": "imputed_empirical_residual_component",
                                 "residual_component_m": float(e), "component_index": j,
                                 "measured_height_available": False})
        summary.append({"year": year, "population_trees": len(pop), "measured_heights": n_measured,
                        "imputed_trees": len(pop) - n_measured,
                        "allometry_source_year": int(allometry_source_year[year]),
                        "allometry_sample_n": model["n"], "beta0": model["beta0"], "beta1": model["beta1"],
                        "residual_sd_m": model["residual_sd_m"],
                        "N_population": float(pop.expansion_factor_ha.sum())})
    assigned = pd.DataFrame(rows, columns=list(ASSIGNED_COLUMNS))
    assigned["measured_height_available"] = assigned["measured_height_available"].astype(bool)
    return assigned, pd.DataFrame(summary)


def read_assigned_heights(path) -> pd.DataFrame:
    """Read an assigned-height table (this module's or the November 2026 one)."""

    df = pd.read_csv(path)
    if "is_missing" in df.columns:
        df = df[~df.is_missing.astype(str).str.lower().eq("true")].copy()
    if "measured_height_available" in df.columns:
        df["measured_height_available"] = df["measured_height_available"].astype(str).str.lower().isin({"true", "1"})
    required = {"year", "diameter_cm", "weight_ha", "height_m"}
    if not required <= set(df.columns):
        raise ValueError(f"assigned-height table lacks columns {sorted(required - set(df.columns))}")
    return df
