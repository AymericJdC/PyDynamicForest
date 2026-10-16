# SPDX-License-Identifier: LGPL-3.0-or-later
"""Shared typography and styling for manuscript figures."""

from __future__ import annotations

import matplotlib as mpl

ARTICLE_FIGURE_STYLE = {
    "font.family": "serif",
    "font.serif": [
        "CMU Serif",
        "Latin Modern Roman",
        "STIXGeneral",
        "DejaVu Serif",
    ],
    "mathtext.fontset": "stix",
    "font.size": 9.0,
    "axes.labelsize": 9.0,
    "axes.titlesize": 9.0,
    "axes.linewidth": 0.8,
    "xtick.labelsize": 8.0,
    "ytick.labelsize": 8.0,
    "xtick.major.width": 0.7,
    "ytick.major.width": 0.7,
    "legend.fontsize": 8.0,
    "figure.titlesize": 10.0,
    "axes.unicode_minus": False,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
}


def apply_article_figure_style() -> None:
    """Apply the common serif style used by all manuscript figures."""
    mpl.rcParams.update(ARTICLE_FIGURE_STYLE)
