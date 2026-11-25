# SPDX-License-Identifier: LGPL-3.0-or-later
"""Step 6: figures 1 to 3 of the article from regularised and simulated states.

Ported from ``generate_ecouves_A5_regularized_figures.py``. The states are read
from the pipeline outputs; target observables are recomputed from the
regularised states with the same operators as the simulated ones.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
import numpy as np



def configure_fonts(usetex: bool) -> None:
    """LaTeX fonts (needs a LaTeX installation with cm-super) or matplotlib's Computer Modern."""

    if usetex:
        plt.rcParams.update({"text.usetex": True, "font.family": "serif"})
    else:
        plt.rcParams.update({
            "text.usetex": False,
            "font.family": "serif",
            "font.serif": ["cmr10"],
            "mathtext.fontset": "cm",
            "axes.formatter.use_mathtext": True,
            "axes.unicode_minus": False,
        })


YEARS = (1985, 1992, 1998, 2016, 2020)
AGES = {1985: 37, 1992: 44, 1998: 50, 2016: 68, 2020: 72}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_npz_u(path: Path) -> np.ndarray:
    with np.load(path, allow_pickle=False) as payload:
        key = "U0" if "U0" in payload.files else "U"
        return np.array(payload[key], dtype=float, copy=True)


def make_figures(target_dir: Path, simulation_dir: Path, output_dir: Path, parameters, usetex: bool = False) -> list[Path]:
    """Write the figures and their manifest in ``output_dir``; return the files written."""

    configure_fonts(usetex)
    from pydynamicforest.numerics import product_trapezoidal_weights
    from pydynamicforest.observation_operators import (
        basal_area_consistent,
        continuous_dominant_height,
        height_dbh_correlation,
        mean_dbh,
        mean_height,
        physical_dbh_nodes,
        physical_height_nodes,
        quadratic_mean_dbh,
        stand_density,
    )

    height_nodes = physical_height_nodes(parameters)
    dbh_nodes = physical_dbh_nodes(parameters, unit="cm")
    quadrature_weights = product_trapezoidal_weights(parameters)

    frozen_dir = Path(simulation_dir).resolve()
    target_dir = Path(target_dir).resolve()
    output_dir = Path(output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    target_paths = {
        year: target_dir / f"observed_state_{year}.npz"
        for year in YEARS
    }
    simulation_paths = {
        year: frozen_dir / f"simulated_state_{year}.npz"
        for year in YEARS
    }
    for path in (*target_paths.values(), *simulation_paths.values()):
        if not path.is_file():
            raise FileNotFoundError(path)

    targets = {year: load_npz_u(path) for year, path in target_paths.items()}
    simulated = {year: load_npz_u(path) for year, path in simulation_paths.items()}

    shapes = {array.shape for array in (*targets.values(), *simulated.values())}
    if len(shapes) != 1 or next(iter(shapes)) != quadrature_weights.shape:
        raise RuntimeError(
            f"Incompatible state shapes: states={sorted(shapes)}, "
            f"quadrature={quadrature_weights.shape}"
        )

    # Figure 1: inventory years in rows, target and simulation in columns.
    states_by_kind = (("Regularised observations", targets), ("Simulation", simulated))
    masses = [state * quadrature_weights
              for state in (*targets.values(), *simulated.values())]
    MASS_DISPLAY_THRESHOLD = 1.0e-2
    positive = np.concatenate([m[m >= MASS_DISPLAY_THRESHOLD] for m in masses])
    if positive.size == 0:
        raise ValueError("No cell exceeds the display threshold.")
    norm = LogNorm(vmin=MASS_DISPLAY_THRESHOLD, vmax=float(np.max(positive)))

    # Common quantitative scales for the two types of marginal distributions.
    dbh_marginal_limit = 1.05 * max(float(np.max(m.sum(axis=0))) for m in masses)
    height_marginal_limit = 1.05 * max(float(np.max(m.sum(axis=1))) for m in masses)

    FOREST_BLUE = "#276A9F"
    EARTH_ORANGE = "#D97820"
    HEIGHT_MIN, HEIGHT_MAX = 15.0, 50.0
    DBH_MIN, DBH_MAX = 0.0, 80.0

    # A4 portrait layout. The larger left margin separates row labels,
    # the global height label and the y tick labels.
    fig = plt.figure(figsize=(7.05, 9.80))
    outer = fig.add_gridspec(
        len(YEARS), 2,
        left=0.150, right=0.955,
        bottom=0.105, top=0.940,
        wspace=0.22, hspace=0.24,
    )

    image = None
    for row, year in enumerate(YEARS):
        for column, (column_title, states) in enumerate(states_by_kind):
            inner = outer[row, column].subgridspec(
                2, 2,
                width_ratios=(5.00, 0.78),
                height_ratios=(4.35, 0.82),
                wspace=0.045, hspace=0.045,
            )
            ax_joint = fig.add_subplot(inner[0, 0])
            ax_dbh = fig.add_subplot(inner[1, 0], sharex=ax_joint)
            ax_height = fig.add_subplot(inner[0, 1], sharey=ax_joint)

            mass = states[year] * quadrature_weights
            shown = np.ma.masked_less(mass, MASS_DISPLAY_THRESHOLD)
            image = ax_joint.pcolormesh(
                dbh_nodes, height_nodes, shown,
                shading="auto", norm=norm, cmap="viridis", rasterized=True,
            )
            ax_dbh.plot(dbh_nodes, mass.sum(axis=0), color=FOREST_BLUE, linewidth=0.80)
            ax_height.plot(mass.sum(axis=1), height_nodes, color=EARTH_ORANGE, linewidth=0.80)

            ax_joint.set(xlim=(DBH_MIN, DBH_MAX), ylim=(HEIGHT_MIN, HEIGHT_MAX))
            ax_joint.set_xticks([0, 20, 40, 60, 80])
            ax_joint.set_yticks([20, 30, 40, 50])
            ax_dbh.set(xlim=(DBH_MIN, DBH_MAX), ylim=(0.0, dbh_marginal_limit))
            ax_height.set(xlim=(0.0, height_marginal_limit), ylim=(HEIGHT_MIN, HEIGHT_MAX))

            for axis in (ax_joint, ax_dbh, ax_height):
                axis.spines[["top", "right"]].set_visible(False)
                axis.spines[["left", "bottom"]].set_linewidth(0.55)
                axis.tick_params(direction="out", width=0.55, length=2.2,
                                 labelsize=8.0, pad=1.5)
            ax_joint.tick_params(labelbottom=False)
            ax_dbh.set_yticks([])
            ax_dbh.tick_params(labelleft=False, left=False)
            ax_height.set_xticks([])
            ax_height.tick_params(labelbottom=False, bottom=False,
                                  labelleft=False, left=False)
            if column == 1:
                ax_joint.tick_params(labelleft=False)
            if row == 0:
                ax_joint.set_title(column_title, fontsize=10.0, pad=5.0)
            if column == 0:
                ax_joint.text(
                    -0.36, 0.50, f"{year}\n(age {AGES[year]})",
                    transform=ax_joint.transAxes, rotation=90,
                    ha="center", va="center", fontsize=8.8,
                    linespacing=1.0, clip_on=False,
                )

    if image is None:
        raise RuntimeError("Figure 1 did not create a colour-mapped image.")

    fig.text(0.525, 0.072, r"DBH, $\phi$ (cm)",
             ha="center", va="center", fontsize=9.2)
    # Positioned between the inventory labels and the y tick labels.
    fig.text(0.097, 0.520, r"Tree height, $h$ (m)",
             rotation=90, ha="center", va="center", fontsize=9.2)

    cbar_ax = fig.add_axes([0.245, 0.035, 0.520, 0.016])
    colorbar = fig.colorbar(image, cax=cbar_ax, orientation="horizontal")
    colorbar.set_label(r"Stem number (trees ha$^{-1}$)", fontsize=8.8, labelpad=2.5)
    colorbar.ax.tick_params(labelsize=7.8, width=0.55, length=2.2, pad=1.5)

    fig.savefig(output_dir / "figure_1_joint_states_regularized.pdf")
    fig.savefig(output_dir / "figure_1_joint_states_regularized.png", dpi=300)
    plt.close(fig)

    def target_metrics(state: np.ndarray) -> dict[str, float]:
        dm = mean_dbh(state, parameters, unit="cm")
        dg = quadratic_mean_dbh(state, parameters, unit="cm")
        hm = mean_height(state, parameters)
        h0 = continuous_dominant_height(state, parameters)
        return {
            "N": stand_density(state, parameters),
            "G": basal_area_consistent(state, parameters),
            "Dm": dm,
            "Dg": dg,
            "sigma_D": float(np.sqrt(max(0.0, dg * dg - dm * dm))),
            "Hm": hm,
            "H0": h0,
            "H0_minus_Hm": h0 - hm,
            "rho_HD": height_dbh_correlation(state, parameters),
        }

    target_summary = {year: target_metrics(targets[year]) for year in YEARS}
    simulated_summary = {year: target_metrics(simulated[year]) for year in YEARS}

    # Shared graphic language for Figures 2 and 3.
    SIMULATION_COLOR = "#276A9F"
    OBSERVATION_COLOR = "#D97820"
    PANEL_LETTERS = "abcdef"

    def style_trajectory_axis(axis: plt.Axes, panel_letter: str) -> None:
        axis.spines[["top", "right"]].set_visible(False)
        axis.spines[["left", "bottom"]].set_linewidth(0.60)
        axis.tick_params(
            direction="out",
            width=0.60,
            length=2.5,
            labelsize=8.0,
            pad=2.0,
        )
        axis.grid(
            axis="y",
            color="0.82",
            linewidth=0.45,
            alpha=0.60,
        )
        axis.set_axisbelow(True)
        axis.text(
            0.025,
            0.965,
            f"({panel_letter})",
            transform=axis.transAxes,
            ha="left",
            va="top",
            fontsize=8.5,
        )

    def plot_trajectory_panel(
        axis: plt.Axes,
        metric: str,
        ylabel: str,
        panel_letter: str,
    ) -> None:
        axis.plot(
            YEARS,
            [simulated_summary[year][metric] for year in YEARS],
            color=SIMULATION_COLOR,
            linewidth=1.25,
            label="Simulation",
            zorder=2,
        )
        axis.plot(
            YEARS,
            [target_summary[year][metric] for year in YEARS],
            linestyle="none",
            marker="o",
            markersize=5.2,
            markerfacecolor="white",
            markeredgecolor=OBSERVATION_COLOR,
            markeredgewidth=1.10,
            label="Regularised observations",
            zorder=3,
        )
        axis.set_ylabel(ylabel, fontsize=8.5)
        axis.set_xticks(YEARS)
        axis.set_xlim(YEARS[0] - 1.5, YEARS[-1] + 1.5)
        style_trajectory_axis(axis, panel_letter)

    # Figure 2: conventional stand-level trajectories.
    stand_panels = (
        ("N", r"Stand density, $N$ (trees ha$^{-1}$)"),
        ("G", r"Basal area, $G$ (m$^2$ ha$^{-1}$)"),
        ("Dm", r"Mean DBH, $D_m$ (cm)"),
        ("Dg", r"Quadratic mean DBH, $D_g$ (cm)"),
        ("Hm", r"Mean height, $H_m$ (m)"),
        ("H0", r"Dominant height, $H_0$ (m)"),
    )
    fig, axes = plt.subplots(
        2,
        3,
        figsize=(7.05, 4.85),
        sharex=True,
        constrained_layout=False,
    )
    fig.subplots_adjust(
        left=0.095,
        right=0.985,
        bottom=0.105,
        top=0.895,
        wspace=0.34,
        hspace=0.22,
    )
    for axis, (metric, ylabel), letter in zip(
        axes.ravel(), stand_panels, PANEL_LETTERS
    ):
        plot_trajectory_panel(axis, metric, ylabel, letter)

    for axis in axes[0]:
        axis.tick_params(labelbottom=False)
    for axis in axes[1]:
        axis.set_xlabel("Inventory year", fontsize=8.5)
        axis.tick_params(axis="x", labelrotation=30)
        for label in axis.get_xticklabels():
            label.set_horizontalalignment("right")

    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(
        handles,
        labels,
        loc="upper center",
        bbox_to_anchor=(0.54, 0.985),
        ncol=2,
        frameon=False,
        fontsize=8.5,
        handlelength=2.6,
        columnspacing=1.6,
    )
    fig.savefig(output_dir / "figure_2_stand_trajectories_regularized.pdf")
    fig.savefig(
        output_dir / "figure_2_stand_trajectories_regularized.png",
        dpi=300,
    )
    plt.close(fig)

    # Figure 3: complementary structural diagnostics. Mean height is omitted
    # because it already appears in Figure 2.
    diagnostic_panels = (
        ("sigma_D", r"DBH standard deviation, $\sigma_D$ (cm)"),
        ("H0_minus_Hm", r"Height contrast, $H_0-H_m$ (m)"),
        ("rho_HD", ("Height--DBH" if usetex else "Height-DBH") + r" correlation, $\rho_{H,D}$"),
    )
    fig, axes = plt.subplots(
        1,
        3,
        figsize=(7.05, 2.65),
        sharex=True,
        constrained_layout=False,
    )
    fig.subplots_adjust(
        left=0.095,
        right=0.985,
        bottom=0.235,
        top=0.815,
        wspace=0.36,
    )
    for axis, (metric, ylabel), letter in zip(
        axes, diagnostic_panels, PANEL_LETTERS
    ):
        plot_trajectory_panel(axis, metric, ylabel, letter)
        axis.set_xlabel("Inventory year", fontsize=8.5)
        axis.tick_params(axis="x", labelrotation=30)
        for label in axis.get_xticklabels():
            label.set_horizontalalignment("right")

    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(
        handles,
        labels,
        loc="upper center",
        bbox_to_anchor=(0.54, 0.985),
        ncol=2,
        frameon=False,
        fontsize=8.5,
        handlelength=2.6,
        columnspacing=1.6,
    )
    fig.savefig(output_dir / "figure_3_structural_diagnostics_regularized.pdf")
    fig.savefig(
        output_dir / "figure_3_structural_diagnostics_regularized.png",
        dpi=300,
    )
    plt.close(fig)

    # Export the recomputed target values for audit and later tables.
    rows = []
    for year in YEARS:
        for metric in target_summary[year]:
            rows.append(
                {
                    "year": year,
                    "metric": metric,
                    "regularized_target_value": target_summary[year][metric],
                    "frozen_simulated_value": simulated_summary[year][metric],
                    "simulation_minus_target": (
                        simulated_summary[year][metric] - target_summary[year][metric]
                    ),
                }
            )
    with (output_dir / "regularized_targets_vs_frozen_simulation.csv").open(
        "w", newline="", encoding="utf-8-sig"
    ) as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    captions = """# Figure captions - regularized observations

## Figure 1
Comparison of the regularized empirical and simulated joint height-diameter distributions for the Écouves A5 stand in 1985, 1992, 1998, 2016, and 2020. The left column shows the regularized observations and the right column the corresponding simulated states. Colours represent the contribution of each numerical grid node to stand density after trapezoidal quadrature. All panels use the same logarithmic colour scale and physical axes; cells below the common display threshold of 10^-2 trees ha^-1 are left white. Blue curves below the joint distributions and orange curves to their right show the corresponding diameter and height marginals, respectively. A common scale is used for each type of marginal across all years and both columns.

## Figure 2
Observed and simulated stand-level trajectories for the Écouves A5 inventories in 1985, 1992, 1998, 2016, and 2020: (a) stand density N, (b) basal area G, (c) arithmetic mean DBH D_m, (d) quadratic mean DBH D_g, (e) mean height H_m, and (f) dominant height H_0. Solid blue lines show the frozen simulated trajectory and open orange circles show quantities recomputed from the regularized observations. Dynamic parameters are unchanged from the frozen calibrated trajectory.

## Figure 3
Structural diagnostics for the Écouves A5 inventories in 1985, 1992, 1998, 2016, and 2020: (a) DBH standard deviation sigma_D, (b) dominant-minus-mean height contrast H_0-H_m, and (c) height-DBH correlation rho_H,D. Solid blue lines show the frozen simulated trajectory and open orange circles show quantities recomputed from the regularized observations. The three diagnostics characterize diameter dispersion, vertical differentiation, and dependence between height and diameter, respectively.
"""
    (output_dir / "figure_captions_regularized.md").write_text(captions, encoding="utf-8")

    manifest = {
        "purpose": "visual comparison of the regularised observations with the simulation",
        "simulation_dir": str(frozen_dir),
        "regularized_target_dir": str(target_dir),
        "years": list(YEARS),
        "simulation_policy": "states written by the simulate step of the pipeline",
        "target_policy": "measured heights retained; missing heights integrated over centered empirical residuals",
        "target_sha256": {str(year): sha256(path) for year, path in target_paths.items()},
        "simulation_sha256": {str(year): sha256(path) for year, path in simulation_paths.items()},
        "outputs": sorted(path.name for path in output_dir.iterdir()),
    }
    (output_dir / "figure_manifest_regularized.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    return sorted(output_dir.iterdir())
