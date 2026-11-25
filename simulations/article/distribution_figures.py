# SPDX-License-Identifier: LGPL-3.0-or-later
"""Alternative joint-distribution figures from saved canonical states.

A2 is the main candidate: six ages shown as light filled contours.
A3 is an exploratory three-dimensional surface representation.
A4 is a nine-age supplementary view.
No numerical trajectory is recomputed.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
from matplotlib.ticker import LogLocator
import numpy as np

from pydynamicforest.numerics import product_trapezoidal_weights
from pydynamicforest.observation_operators import physical_dbh_nodes, physical_height_nodes
from simulations.article.parameters import build_parameters
from simulations.article.figure_style import (
    apply_article_figure_style,
)

apply_article_figure_style()

MAIN_AGES = (18.0, 28.0, 38.0, 45.0, 54.0, 69.0)
EXPLORATORY_3D_AGES = (18.0, 45.0, 69.0)
SUPPLEMENTARY_AGES = (18.0, 22.0, 28.0, 33.0, 38.0, 45.0, 54.0, 63.0, 69.0)
DISPLAY_DBH_MAX_CM = 80.0
DISPLAY_HEIGHT_MAX_M = 50.0
N_LOG_LEVELS = 21
RELATIVE_DISPLAY_FLOOR = 1.0e-4
PANEL_LABELS = tuple(f"({chr(97 + index)})" for index in range(9))


def _git_value(*args: str) -> str:
    try:
        return subprocess.check_output(
            ["git", *args], text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unavailable"


def _state_path(output_dir: Path, age: float) -> Path:
    label = str(int(age)) if float(age).is_integer() else str(age).replace(".", "p")
    return output_dir / f"state_age_{label}.npz"


def load_weighted_density(output_dir: str | Path, age: float, p=None) -> dict:
    output = Path(output_dir)
    path = _state_path(output, age)
    if not path.is_file():
        raise FileNotFoundError(f"Saved state not found: {path}")
    if p is None:
        p = build_parameters()
    with np.load(path) as payload:
        requested_age = float(payload["requested_age"])
        actual_age = float(payload["actual_age"])
        U = np.array(payload["U"], dtype=float, copy=True)
    if requested_age != float(age):
        raise ValueError(
            f"Stored requested age {requested_age} does not match requested age {age}."
        )
    weights = product_trapezoidal_weights(p)
    return {
        "requested_age": float(age),
        "actual_age": actual_age,
        "height_m": physical_height_nodes(p),
        "dbh_cm": physical_dbh_nodes(p, unit="cm"),
        "weighted_density": weights * U,
    }


def _load_series(output_dir: str | Path, ages: tuple[float, ...]) -> list[dict]:
    p = build_parameters()
    return [load_weighted_density(output_dir, age, p) for age in ages]


def _common_levels(series: list[dict]) -> tuple[np.ndarray, LogNorm, float]:
    values = np.concatenate([item["weighted_density"].ravel() for item in series])
    positive = values[values > 0.0]
    if positive.size == 0:
        raise ValueError("Saved states contain no positive quadrature-weighted density.")
    vmax = float(positive.max())
    vmin = max(float(positive.min()), RELATIVE_DISPLAY_FLOOR * vmax)
    levels = np.geomspace(vmin, vmax, N_LOG_LEVELS)
    return levels, LogNorm(vmin=vmin, vmax=vmax), vmin


def _light_colormap():
    return plt.get_cmap("viridis").with_extremes(
        under="white",
        bad="white",
    )


def _panel_contours(axis, item: dict, label: str, levels, norm, vmin):
    density = np.ma.masked_less(item["weighted_density"], vmin)
    filled = axis.contourf(
        item["dbh_cm"],
        item["height_m"],
        density,
        levels=levels,
        norm=norm,
        cmap=_light_colormap(),
        extend="min",
    )
    contour_levels = levels[4::5]
    axis.contour(
        item["dbh_cm"],
        item["height_m"],
        density,
        levels=contour_levels,
        norm=norm,
        colors="0.38",
        linewidths=0.35,
        alpha=0.65,
    )
    axis.set_xlim(0.0, DISPLAY_DBH_MAX_CM)
    axis.set_ylim(0.0, DISPLAY_HEIGHT_MAX_M)
    axis.text(
        0.035,
        0.95,
        f"{label} {item['requested_age']:g} years",
        transform=axis.transAxes,
        va="top",
        fontweight="bold",
    )
    return filled


def _horizontal_colorbar(fig, mappable, label: str, bounds):
    colorbar_axis = fig.add_axes(bounds)
    colorbar = fig.colorbar(
        mappable,
        cax=colorbar_axis,
        orientation="horizontal",
        ticks=LogLocator(base=10.0, numticks=6),
    )
    colorbar.set_label(label, labelpad=4)
    colorbar.ax.tick_params(labelsize=8, pad=2)
    return colorbar


def plot_six_age_contours(output_dir: str | Path, figure_dir: str | Path) -> list[Path]:
    series = _load_series(output_dir, MAIN_AGES)
    levels, norm, vmin = _common_levels(series)
    fig, axes = plt.subplots(2, 3, figsize=(11.4, 6.35), sharex=True, sharey=True)
    flat = axes.ravel()
    mappable = None
    for index, (axis, item) in enumerate(zip(flat, series)):
        mappable = _panel_contours(axis, item, PANEL_LABELS[index], levels, norm, vmin)
        if index >= 3:
            axis.set_xlabel("DBH (cm)")
        if index % 3 == 0:
            axis.set_ylabel("Height (m)")
    fig.subplots_adjust(
        left=0.075,
        right=0.985,
        top=0.975,
        bottom=0.24,
        wspace=0.08,
        hspace=0.14,
    )
    _horizontal_colorbar(
        fig,
        mappable,
        "Quadrature-weighted stem number (trees ha$^{-1}$; logarithmic scale)",
        bounds=[0.22, 0.075, 0.56, 0.028],
    )
    return _save(fig, figure_dir, "figure_A2_joint_density_six_ages")


def plot_nine_age_contours(output_dir: str | Path, figure_dir: str | Path) -> list[Path]:
    series = _load_series(output_dir, SUPPLEMENTARY_AGES)
    levels, norm, vmin = _common_levels(series)
    fig, axes = plt.subplots(3, 3, figsize=(10.4, 8.55), sharex=True, sharey=True)
    flat = axes.ravel()
    mappable = None
    for index, (axis, item) in enumerate(zip(flat, series)):
        mappable = _panel_contours(axis, item, PANEL_LABELS[index], levels, norm, vmin)
        if index >= 6:
            axis.set_xlabel("DBH (cm)")
        if index % 3 == 0:
            axis.set_ylabel("Height (m)")
    fig.subplots_adjust(
        left=0.075,
        right=0.985,
        top=0.98,
        bottom=0.19,
        wspace=0.08,
        hspace=0.14,
    )
    _horizontal_colorbar(
        fig,
        mappable,
        "Quadrature-weighted stem number (trees ha$^{-1}$; logarithmic scale)",
        bounds=[0.22, 0.055, 0.56, 0.024],
    )
    return _save(fig, figure_dir, "figure_A4_joint_density_nine_ages")


def plot_three_age_surfaces(output_dir: str | Path, figure_dir: str | Path) -> list[Path]:
    series = _load_series(output_dir, EXPLORATORY_3D_AGES)
    _, _, vmin = _common_levels(series)
    transformed_max = max(
        float(np.log10(1.0 + item["weighted_density"]).max()) for item in series
    )
    fig = plt.figure(figsize=(13.6, 4.35))
    cmap = _light_colormap()
    for index, item in enumerate(series, start=1):
        axis = fig.add_subplot(1, 3, index, projection="3d")
        dbh_grid, height_grid = np.meshgrid(item["dbh_cm"], item["height_m"])
        density = item["weighted_density"]
        visible = np.where(density >= vmin, density, np.nan)
        z = np.log10(1.0 + visible)
        axis.plot_surface(
            dbh_grid,
            height_grid,
            z,
            cmap=cmap,
            vmin=0.0,
            vmax=transformed_max,
            linewidth=0.0,
            antialiased=True,
            alpha=0.94,
            rcount=40,
            ccount=40,
        )
        axis.contour(
            dbh_grid,
            height_grid,
            np.nan_to_num(z, nan=0.0),
            levels=5,
            zdir="z",
            offset=0.0,
            colors="0.45",
            linewidths=0.45,
            alpha=0.55,
        )
        axis.set_xlim(0.0, DISPLAY_DBH_MAX_CM)
        axis.set_ylim(0.0, DISPLAY_HEIGHT_MAX_M)
        axis.set_zlim(0.0, transformed_max)
        axis.view_init(elev=25, azim=-125)
        axis.set_xlabel("DBH (cm)", labelpad=4)
        if index == 1:
            axis.set_ylabel("Height (m)", labelpad=4)
        else:
            axis.set_yticklabels([])
        axis.set_zlabel("")
        axis.set_title(
            f"{PANEL_LABELS[index - 1]} {item['requested_age']:g} years",
            pad=8,
        )
        axis.grid(False)
        axis.xaxis.pane.fill = False
        axis.yaxis.pane.fill = False
        axis.zaxis.pane.fill = False
        axis.tick_params(pad=0, labelsize=7)
    fig.text(
        0.985,
        0.50,
        "log$_{10}$(1 + stem density)",
        rotation=90,
        va="center",
        ha="right",
    )
    fig.subplots_adjust(
        left=0.015,
        right=0.965,
        bottom=0.09,
        top=0.90,
        wspace=0.10,
    )
    return _save(fig, figure_dir, "figure_A3_joint_density_3d")


def _save(fig, figure_dir: str | Path, stem: str) -> list[Path]:
    output = Path(figure_dir)
    output.mkdir(parents=True, exist_ok=True)
    paths = [output / f"{stem}.png", output / f"{stem}.pdf"]
    fig.savefig(paths[0], dpi=300, bbox_inches="tight")
    fig.savefig(paths[1], bbox_inches="tight")
    plt.close(fig)
    return paths


def generate_distribution_variants(
    input_dir: str | Path,
    output_dir: str | Path,
) -> dict:
    source = Path(input_dir)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    files = []
    files.extend(plot_six_age_contours(source, output))
    files.extend(plot_three_age_surfaces(source, output))
    files.extend(plot_nine_age_contours(source, output))
    captions = r"""# Alternative joint-distribution figure captions

**Figure A2. Evolution of the simulated joint height-diameter distribution at six stand ages.** Quadrature-weighted stem density is shown at ages (a) 18, (b) 28, (c) 38, (d) 45, (e) 54, and (f) 69 years. Filled contours interpolate, for visualization only, values computed on the 40 x 40 numerical grid. Colours represent each grid node's quadrature-weighted contribution to stand density. All panels use identical logarithmic levels and common physical axes. Cells below the common display threshold are left white. The displayed diameter range contains more than 99.9% of simulated stem mass at age 69.

**Figure A3. Three-dimensional exploratory representation of the simulated joint height-diameter distribution.** Surface height represents log10(1 + quadrature-weighted stem density) at ages (a) 18, (b) 45, and (c) 69 years. The three panels share the same axes, vertical transformation, and viewing angle. Surface interpolation is intended for visualization only and does not increase the 40 x 40 numerical resolution.

**Figure A4. Supplementary nine-age view of the simulated joint height-diameter distribution.** The common contour representation is shown at ages 18, 22, 28, 33, 38, 45, 54, 63, and 69 years to document the early development and later persistence of excessive size differentiation.
"""
    captions_path = output / "distribution_figure_captions.md"
    captions_path.write_text(captions, encoding="utf-8")
    files.append(captions_path)
    metadata = {
        "purpose": "alternative joint-distribution visualizations from saved canonical states",
        "trajectory_commit": _trajectory_commit(source),
        "postprocessing_commit": _git_value("rev-parse", "HEAD"),
        "numerical_grid": [40, 40],
        "main_ages": list(MAIN_AGES),
        "exploratory_3d_ages": list(EXPLORATORY_3D_AGES),
        "supplementary_ages": list(SUPPLEMENTARY_AGES),
        "display_dbh_max_cm": DISPLAY_DBH_MAX_CM,
        "relative_display_floor": RELATIVE_DISPLAY_FLOOR,
        "files": [path.name for path in files],
    }
    metadata_path = output / "distribution_figure_metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    files.append(metadata_path)
    return {"files": files, "metadata": metadata}


def _trajectory_commit(source: Path) -> str:
    path = source / "reproducibility.json"
    if not path.is_file():
        return "unavailable"
    return json.loads(path.read_text(encoding="utf-8")).get("git_commit", "unavailable")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", default="outputs/article_simulation")
    parser.add_argument("--output-dir", default="outputs/article_distribution_variants")
    args = parser.parse_args()
    result = generate_distribution_variants(args.input_dir, args.output_dir)
    for path in result["files"]:
        print(path.resolve())


if __name__ == "__main__":
    main()
