# SPDX-License-Identifier: LGPL-3.0-or-later
"""Model and numerical parameters retained for the manuscript."""

from simulations.article.config import ARTICLE_CONFIG
from simulations.article_submission_legacy.parameters import build_parameters as _build_parameters


def build_parameters(config: dict | None = None):
    return _build_parameters(ARTICLE_CONFIG if config is None else config)
