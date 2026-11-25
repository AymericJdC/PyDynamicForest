# SPDX-License-Identifier: LGPL-3.0-or-later
"""Frozen configuration of the numerical simulation retained for the manuscript."""

from copy import deepcopy

from simulations.article_submission_legacy.config import ARTICLE_SUBMISSION_CONFIG

ARTICLE_CONFIG = deepcopy(ARTICLE_SUBMISSION_CONFIG)
ARTICLE_CONFIG["name"] = "article"
ARTICLE_CONFIG["description"] = (
    "Numerical simulation retained for the manuscript. It uses the analysed "
    "reduced system and a correlated truncated bivariate Gaussian initial state."
)
ARTICLE_CONFIG["initial_condition"] = {
    **ARTICLE_CONFIG["initial_condition"],
    "name": "article_correlated_gaussian_initial_condition",
    "source": "reconstruction_from_initial_stand_observables",
    "height_dbh_correlation": 0.8490113967,
    "dependence_status": (
        "Initial joint-distribution reconstruction constrained by the observed "
        "dominant-height contrast; not estimated from individual-tree records."
    ),
}
