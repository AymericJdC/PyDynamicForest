# SPDX-License-Identifier: LGPL-3.0-or-later
"""Initial condition of the numerical simulation retained for the manuscript."""

from pydynamicforest.types import InitialCondition
from simulations.article.config import ARTICLE_CONFIG


def build_initial_condition(config: dict | None = None) -> InitialCondition:
    """Build the correlated truncated bivariate Gaussian initial condition."""
    if config is None:
        config = ARTICLE_CONFIG
    ages = config["ages"]
    initial = config["initial_condition"]
    return InitialCondition(
        name=initial["name"],
        initial_age=ages["initial_age"],
        mass_target=initial["mass_target"],
        distribution_kind=initial["distribution_kind"],
        distribution_parameters={
            "h0_physical": initial["h0_physical"],
            "d0_physical": initial["d0_physical"],
            "sigma_h_physical": initial["sigma_h_physical"],
            "sigma_d_physical": initial["sigma_d_physical"],
            "height_dbh_correlation": initial["height_dbh_correlation"],
        },
        source=initial["source"],
        description=initial["dependence_status"],
    )
