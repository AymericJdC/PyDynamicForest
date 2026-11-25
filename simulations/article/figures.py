# SPDX-License-Identifier: LGPL-3.0-or-later
"""Generate publication figures from canonical saved outputs without rerunning the model."""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
import numpy as np

from simulations.article.figure_style import apply_article_figure_style

apply_article_figure_style()

TRAJECTORY_VARIABLES = (
    ("N", "Stem density (trees ha$^{-1}$)"),
    ("G", "Basal area (m$^2$ ha$^{-1}$)"),
    ("Dm", "Mean DBH (cm)"),
    ("sigma_D", "DBH standard deviation (cm)"),
    ("Hm", "Mean height (m)"),
    ("H0", "Dominant height (m)"),
)
SCENARIO_COLOR = "#1f4e79"
OBSERVATION_COLOR = "#b33a3a"
PANEL_LABELS = ("(a)", "(b)", "(c)", "(d)", "(e)", "(f)")
JOINT_DENSITY_DBH_MAX_CM = 80.0


def _git_value(*args: str) -> str:
    try:
        return subprocess.check_output(["git", *args], text=True, stderr=subprocess.DEVNULL).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unavailable"


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def _comparison_index(rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    grouped = defaultdict(list)
    for row in rows:
        grouped[row["observable"]].append(row)
    for values in grouped.values():
        values.sort(key=lambda row: float(row["requested_age"]))
    return dict(grouped)


def _save_figure(fig, output: Path, stem: str) -> list[Path]:
    paths = [output / f"{stem}.png", output / f"{stem}.pdf"]
    fig.savefig(paths[0], dpi=300, bbox_inches="tight")
    fig.savefig(paths[1], bbox_inches="tight")
    plt.close(fig)
    return paths


def plot_joint_density(rows: list[dict[str, str]], output: Path) -> list[Path]:
    ages = (18.0, 45.0, 69.0)
    values = np.array([float(row["weighted_stems_ha"]) for row in rows])
    positive = values[values > 0.0]
    if positive.size == 0:
        raise ValueError("Joint-density output contains no positive weighted mass.")
    vmax = float(positive.max())
    norm = LogNorm(vmin=max(float(positive.min()), vmax * 1.0e-5), vmax=vmax)
    fig, axes = plt.subplots(1, 3, figsize=(11.4, 3.55), sharex=True, sharey=True)
    image = None
    for panel, axis, age in zip(PANEL_LABELS, axes, ages):
        selected = [row for row in rows if float(row["requested_age"]) == age]
        if len(selected) != 1600:
            raise ValueError(f"Expected 1600 density cells at age {age}, found {len(selected)}.")
        heights = sorted({float(row["height_m"]) for row in selected})
        dbhs = sorted({float(row["dbh_cm"]) for row in selected})
        lookup = {(float(row["height_m"]), float(row["dbh_cm"])): float(row["weighted_stems_ha"]) for row in selected}
        matrix = np.array([[lookup[(height, dbh)] for dbh in dbhs] for height in heights])
        image = axis.imshow(
            np.ma.masked_less_equal(matrix, 0.0), origin="lower", aspect="auto",
            extent=[min(dbhs), max(dbhs), min(heights), max(heights)],
            norm=norm, cmap="viridis", interpolation="nearest",
        )
        axis.set_xlim(0.0, JOINT_DENSITY_DBH_MAX_CM)
        axis.text(0.04, 0.95, f"{panel} {int(age)} years", transform=axis.transAxes,
                  va="top", color="white", fontweight="bold",
                  bbox={"facecolor": "black", "alpha": 0.30, "edgecolor": "none", "pad": 2.0})
        axis.set_xlabel("DBH (cm)")
    axes[0].set_ylabel("Height (m)")
    colorbar = fig.colorbar(
        image,
        ax=axes,
        orientation="horizontal",
        fraction=0.075,
        pad=0.20,
        aspect=40,
    )
    colorbar.set_label(
        "Quadrature-weighted stem number "
        "(trees ha$^{-1}$; logarithmic scale)"
    )
    fig.subplots_adjust(
        left=0.075,
        right=0.98,
        bottom=0.25,
        top=0.98,
        wspace=0.08,
    )
    return _save_figure(fig, output, "figure_A_joint_height_dbh_density")


def plot_trajectories(
    rows: list[dict[str, str]],
    output: Path,
) -> list[Path]:
    grouped = _comparison_index(rows)

    fig, axes = plt.subplots(
        2,
        3,
        figsize=(11.4, 6.5),
        sharex=True,
    )

    axes = axes.ravel()
    legend_handles = None

    for index, (
        axis,
        (name, ylabel),
    ) in enumerate(
        zip(
            axes,
            TRAJECTORY_VARIABLES,
        )
    ):
        values = grouped[name]

        ages = np.array(
            [
                float(row["actual_simulated_age"])
                for row in values
            ]
        )

        simulated = np.array(
            [
                float(row["simulated_value"])
                for row in values
            ]
        )

        line, = axis.plot(
            ages,
            simulated,
            color=SCENARIO_COLOR,
            linewidth=1.25,
            solid_capstyle="round",
            solid_joinstyle="round",
            label="Simulation",
        )

        obs_rows = [
            row
            for row in values
            if row["observed_value"] != ""
        ]

        points = axis.scatter(
            [
                float(row["requested_age"])
                for row in obs_rows
            ],
            [
                float(row["observed_value"])
                for row in obs_rows
            ],
            facecolor="white",
            edgecolor=OBSERVATION_COLOR,
            linewidth=0.9,
            marker="o",
            s=24,
            zorder=3,
            label="Observation",
        )

        if legend_handles is None:
            legend_handles = (
                line,
                points,
            )

        axis.text(
            0.03,
            0.95,
            PANEL_LABELS[index],
            transform=axis.transAxes,
            va="top",
            fontweight="bold",
        )

        axis.set_ylabel(ylabel)

        if index >= 3:
            axis.set_xlabel(
                "Stand age (years)"
            )

        axis.set_axisbelow(True)

        axis.grid(
            color="0.88",
            linewidth=0.45,
            alpha=0.65,
        )

        axis.spines["top"].set_visible(False)
        axis.spines["right"].set_visible(False)

        axis.spines["left"].set_color(
            "0.35"
        )
        axis.spines["bottom"].set_color(
            "0.35"
        )

        axis.spines["left"].set_linewidth(
            0.7
        )
        axis.spines["bottom"].set_linewidth(
            0.7
        )

    fig.legend(
        legend_handles,
        (
            "Simulation",
            "Observation",
        ),
        loc="upper center",
        ncol=2,
        frameon=False,
        bbox_to_anchor=(0.5, 1.01),
    )

    fig.tight_layout(
        rect=(0, 0, 1, 0.955)
    )

    return _save_figure(
        fig,
        output,
        "figure_B_stand_trajectories",
    )


def plot_structure_diagnostic(
    rows: list[dict[str, str]],
    output: Path,
) -> list[Path]:
    grouped = _comparison_index(rows)

    fig, axes = plt.subplots(
        1,
        2,
        figsize=(8.6, 3.55),
        sharex=True,
    )

    specifications = (
        (
            "sigma_D",
            "DBH standard deviation (cm)",
        ),
        (
            "H0_minus_Hm",
            "$H_0-H_m$ (m)",
        ),
    )

    legend_handles = None

    for index, (
        axis,
        (name, ylabel),
    ) in enumerate(
        zip(
            axes,
            specifications,
        )
    ):
        values = grouped[name]

        ages = np.array(
            [
                float(row["actual_simulated_age"])
                for row in values
            ]
        )

        simulated = np.array(
            [
                float(row["simulated_value"])
                for row in values
            ]
        )

        line, = axis.plot(
            ages,
            simulated,
            color=SCENARIO_COLOR,
            linewidth=1.25,
            solid_capstyle="round",
            solid_joinstyle="round",
            label="Simulation",
        )

        obs_rows = [
            row
            for row in values
            if row["observed_value"] != ""
        ]

        points = axis.scatter(
            [
                float(row["requested_age"])
                for row in obs_rows
            ],
            [
                float(row["observed_value"])
                for row in obs_rows
            ],
            facecolor="white",
            edgecolor=OBSERVATION_COLOR,
            linewidth=0.9,
            marker="o",
            s=24,
            zorder=3,
            label="Derived from observations",
        )

        if legend_handles is None:
            legend_handles = (
                line,
                points,
            )

        axis.text(
            0.03,
            0.95,
            PANEL_LABELS[index],
            transform=axis.transAxes,
            va="top",
            fontweight="bold",
        )

        axis.set_xlabel(
            "Stand age (years)"
        )
        axis.set_ylabel(ylabel)

        axis.set_axisbelow(True)

        axis.grid(
            color="0.88",
            linewidth=0.45,
            alpha=0.65,
        )

        axis.spines["top"].set_visible(False)
        axis.spines["right"].set_visible(False)

        axis.spines["left"].set_color(
            "0.35"
        )
        axis.spines["bottom"].set_color(
            "0.35"
        )

        axis.spines["left"].set_linewidth(
            0.7
        )
        axis.spines["bottom"].set_linewidth(
            0.7
        )

    fig.legend(
        legend_handles,
        (
            "Simulation",
            "Derived from observations",
        ),
        loc="upper center",
        ncol=2,
        frameon=False,
        bbox_to_anchor=(0.5, 1.02),
    )

    fig.tight_layout(
        rect=(0, 0, 1, 0.92)
    )

    return _save_figure(
        fig,
        output,
        "figure_C_size_structure_diagnostic",
    )

def generate_figures(input_dir: str | Path, output_dir: str | Path) -> dict:
    source = Path(input_dir)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    comparison_path = source / "observations_simulation.csv"
    density_path = source / "joint_densities_primary_ages.csv"
    metadata_path = source / "metadata.json"
    reproducibility_path = source / "reproducibility.json"
    for path in (comparison_path, density_path, metadata_path, reproducibility_path):
        if not path.is_file():
            raise FileNotFoundError(f"Required canonical output not found: {path}")
    comparison_rows = _read_rows(comparison_path)
    density_rows = _read_rows(density_path)
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    reproducibility = json.loads(reproducibility_path.read_text(encoding="utf-8"))
    files = []

    try:
        files.extend(
            plot_joint_density(
                density_rows,
                output,
            )
        )

        files.extend(
            plot_trajectories(
                comparison_rows,
                output,
            )
        )

        files.extend(
            plot_structure_diagnostic(
                comparison_rows,
                output,
            )
        )

    except Exception:
        plt.close("all")
        raise
    captions = r"""# Figure captions

**Figure A. Evolution of the simulated joint height-diameter distribution.** Quadrature-weighted stem number is represented at stand ages (a) 18, (b) 45, and (c) 69 years using a common logarithmic colour scale. The initial state is a correlated truncated bivariate Gaussian reconstructed from the available stand-level observations. The states at ages 45 and 69 result from the height-diameter transport, diffusion, and mortality processes of the reduced model. All panels use the same physical height range, the same displayed diameter range, and the same colour mapping; the numerical diameter domain extends beyond the displayed 80 cm limit.

**Figure B. Observed and simulated stand trajectories.** The numerical simulation is compared with 15 inventories of the selected Douglas-fir series for (a) stem density $N$, (b) basal area $G$, (c) mean diameter $D_m$, (d) diameter standard deviation $\sigma_D$, (e) mean height $H_m$, and (f) dominant height $H_0$. Diameter standard deviation is derived from observed stem density, basal area, and mean diameter. Height observations unavailable at stand ages 51, 53, and 57 years are left missing and are not interpolated. The simulation starts from the correlated distributed state reconstructed at age 18.

**Figure C. Diagnostic of excessive size-structure differentiation.** Simulated (a) diameter standard deviation and (b) dominant-minus-mean height are compared with the corresponding quantities derived from the stand observations. The model rapidly overestimates both the spread of the diameter distribution and the separation between dominant and mean height. These discrepancies arise despite comparatively close agreement for several aggregate stand variables shown in Figure B. Missing height observations at ages 51, 53, and 57 years are not interpolated.
"""
    captions_path = output / "figure_captions.md"
    captions_path.write_text(captions, encoding="utf-8")
    files.append(captions_path)
    figure_metadata = {
        "purpose": "publication figure generation from saved canonical outputs",
        "trajectory_commit": reproducibility.get("git_commit", "unavailable"),
        "postprocessing_commit": _git_value("rev-parse", "HEAD"),
        "source_output_directory": str(source),
        "trajectory_elapsed_seconds": metadata.get("elapsed_seconds"),
        "figures": [path.name for path in files],
        "style": {
            "simulation_color": SCENARIO_COLOR,
            "observation_color": OBSERVATION_COLOR,
            "png_dpi": 300,
            "formats": ["png", "pdf"],
        },
    }
    figure_metadata_path = output / "figure_metadata.json"
    figure_metadata_path.write_text(json.dumps(figure_metadata, indent=2) + "\n", encoding="utf-8")
    files.append(figure_metadata_path)
    return {"files": files, "metadata": figure_metadata}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", default="outputs/article_simulation")
    parser.add_argument("--output-dir", default="outputs/article_figures")
    args = parser.parse_args()
    result = generate_figures(args.input_dir, args.output_dir)
    for path in result["files"]:
        print(path.resolve())


if __name__ == "__main__":
    main()
