# SPDX-License-Identifier: LGPL-3.0-or-later
"""Correlated initial condition proposed for the manuscript simulation.

The marginal Gaussian parameters and target mass are inherited from the
article-associated configuration. The dependence parameter is a reconstruction
constraint chosen to reproduce the initial dominant-height contrast within the
truncated bivariate Gaussian family. It is not an estimate from individual-tree
data.
"""

from __future__ import annotations

from copy import deepcopy

from pydynamicforest.types import InitialCondition
from simulations.article_submission_legacy.config import ARTICLE_SUBMISSION_CONFIG

DEFAULT_HEIGHT_DBH_CORRELATION = 0.8490113967


def build_correlated_initial_condition(
    config: dict | None = None,
    correlation: float = DEFAULT_HEIGHT_DBH_CORRELATION,
) -> InitialCondition:
    """Build the correlated Gaussian initial condition without changing legacy defaults."""
    source = ARTICLE_SUBMISSION_CONFIG if config is None else config
    config_copy = deepcopy(source)
    ages = config_copy["ages"]
    initial = config_copy["initial_condition"]
    return InitialCondition(
        name="article_submission_correlated_gaussian_initial_condition",
        initial_age=ages["initial_age"],
        mass_target=initial["mass_target"],
        distribution_kind="gaussian_2d",
        distribution_parameters={
            "h0_physical": initial["h0_physical"],
            "d0_physical": initial["d0_physical"],
            "sigma_h_physical": initial["sigma_h_physical"],
            "sigma_d_physical": initial["sigma_d_physical"],
            "height_dbh_correlation": float(correlation),
        },
        source=(
            "reconstruction constrained by the initial dominant-height contrast; "
            "not estimated from individual-tree data"
        ),
        description=(
            "Truncated correlated bivariate Gaussian proposed for the manuscript "
            "simulation. Marginal parameters come from the article-associated "
            "configuration; dependence remains provisional pending complete inventories."
        ),
    )
