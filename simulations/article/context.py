# SPDX-License-Identifier: LGPL-3.0-or-later
"""Simulation context retained for the manuscript."""

from simulations.article.config import ARTICLE_CONFIG
from simulations.article_submission_legacy.context import build_context as _build_context


def build_context(config: dict | None = None):
    return _build_context(ARTICLE_CONFIG if config is None else config)
