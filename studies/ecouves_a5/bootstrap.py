# SPDX-License-Identifier: LGPL-3.0-or-later
"""Sampling uncertainty of the regularised observations (bootstrap over trees).

For each inventory, trees are resampled with replacement (all height
components of a drawn tree are kept, and a tree drawn ``k`` times receives
``k`` times its weight). The resampled records are regularised with the same
kernel and the diagnostics are recomputed. Percentile intervals then show
whether the differences between simulation and observation exceed the
sampling uncertainty of a single 0.12 ha plot. The simulation is not rerun:
the intervals concern the observed values only.
"""

from __future__ import annotations

from collections.abc import Callable

import numpy as np
import pandas as pd

from .dynamics import summarize
from .regularise import regularise_records


def resample_trees(rows: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    """One bootstrap sample of the trees of one inventory, components kept together."""

    trees = rows.tree_id.unique()
    draw = rng.choice(trees, size=len(trees), replace=True)
    counts = pd.Series(draw).value_counts()
    sample = rows[rows.tree_id.isin(counts.index)].copy()
    sample["weight_ha"] = sample["weight_ha"] * sample["tree_id"].map(counts).to_numpy()
    return sample


def bootstrap_diagnostics(
    assigned: pd.DataFrame,
    years,
    p,
    half_width_height_m: float,
    half_width_dbh_cm: float,
    replicates: int = 1000,
    seed: int = 20261125,
    progress: Callable[[int, int], None] | None = None,
) -> pd.DataFrame:
    """Long table (replicate, year, metric, value) of bootstrapped observed diagnostics."""

    rng = np.random.default_rng(seed)
    out = []
    for b in range(replicates):
        for year in years:
            sample = resample_trees(assigned[assigned.year == year], rng)
            U = regularise_records(sample.height_m.to_numpy(), sample.diameter_cm.to_numpy(),
                                   sample.weight_ha.to_numpy(), p, half_width_height_m, half_width_dbh_cm)
            for metric, value in summarize(U, p).items():
                out.append((b, year, metric, value))
        if progress is not None:
            progress(b + 1, replicates)
    return pd.DataFrame(out, columns=["replicate", "year", "metric", "value"])


def percentile_intervals(samples: pd.DataFrame, comparison: pd.DataFrame, level: float = 0.95) -> pd.DataFrame:
    """Percentile intervals of the observed diagnostics, with the simulated value.

    ``outside`` is true when the simulated value lies outside the interval of
    the observed value.
    """

    a = (1.0 - level) / 2.0
    q = samples.groupby(["year", "metric"]).value.quantile([a, 1.0 - a]).unstack()
    q.columns = ["lower", "upper"]
    sd = samples.groupby(["year", "metric"]).value.std(ddof=1).rename("bootstrap_sd")
    table = q.join(sd).reset_index()
    table = table.merge(comparison[["year", "metric", "simulated", "observed"]], on=["year", "metric"], how="left")
    table["outside"] = (table.simulated < table.lower) | (table.simulated > table.upper)
    return table
