# SPDX-License-Identifier: LGPL-3.0-or-later
"""Diagnose apparent stem-loss rates between successive inventory ages.

This post-processing module uses the canonical observation-simulation table and
does not rerun the numerical model. Apparent rates describe changes in stand
density; their biological interpretation depends on plot history, interventions,
disturbances, and inventory continuity.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import subprocess
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

from simulations.article.figure_style import apply_article_figure_style
from simulations.article.observations import SOURCE_PROVENANCE

apply_article_figure_style()

INTERVAL_FIELDS = [
    "initial_age",
    "final_age",
    "interval_years",
    "initial_observed_N",
    "final_observed_N",
    "observed_stem_loss",
    "observed_annual_stem_loss",
    "observed_apparent_mortality_rate",
    "initial_simulated_N",
    "final_simulated_N",
    "simulated_stem_loss",
    "simulated_annual_stem_loss",
    "simulated_apparent_mortality_rate",
    "mortality_rate_difference",
    "mortality_rate_ratio",
    "initial_observed_G",
    "initial_simulated_G",
    "empirical_interpretation_status",
    "empirical_notes",
]

SIMULATION_COLOR = "#1f4e79"
OBSERVATION_COLOR = "#b33a3a"


def _git_value(*args: str) -> str:
    try:
        return subprocess.check_output(
            ["git", *args], text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unavailable"


def apparent_mortality_rate(initial_N: float, final_N: float, years: float) -> float:
    """Return the annual logarithmic apparent stem-loss rate."""
    if initial_N <= 0.0 or final_N <= 0.0:
        raise ValueError("Stand densities must be strictly positive.")
    if years <= 0.0:
        raise ValueError("Interval length must be strictly positive.")
    return -math.log(final_N / initial_N) / years


def _read_comparison(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def _observable_by_age(rows: list[dict[str, str]], observable: str) -> dict[float, dict]:
    selected = {}
    for row in rows:
        if row["observable"] != observable:
            continue
        age = float(row["requested_age"])
        observed = row["observed_value"]
        selected[age] = {
            "simulated": float(row["simulated_value"]),
            "observed": None if observed == "" else float(observed),
            "actual_simulated_age": float(row["actual_simulated_age"]),
        }
    return selected


def build_interval_rows(comparison_rows: list[dict[str, str]]) -> list[dict]:
    density = _observable_by_age(comparison_rows, "N")
    basal_area = _observable_by_age(comparison_rows, "G")
    ages = sorted(density)
    if len(ages) < 2:
        raise ValueError("At least two inventory ages are required.")
    rows = []
    for initial_age, final_age in zip(ages[:-1], ages[1:]):
        years = final_age - initial_age
        initial_obs = density[initial_age]["observed"]
        final_obs = density[final_age]["observed"]
        if initial_obs is None or final_obs is None:
            raise ValueError("Observed stand density is missing for an interval.")
        initial_sim = density[initial_age]["simulated"]
        final_sim = density[final_age]["simulated"]
        observed_loss = initial_obs - final_obs
        simulated_loss = initial_sim - final_sim
        observed_rate = apparent_mortality_rate(initial_obs, final_obs, years)
        simulated_rate = apparent_mortality_rate(initial_sim, final_sim, years)
        rows.append(
            {
                "initial_age": initial_age,
                "final_age": final_age,
                "interval_years": years,
                "initial_observed_N": initial_obs,
                "final_observed_N": final_obs,
                "observed_stem_loss": observed_loss,
                "observed_annual_stem_loss": observed_loss / years,
                "observed_apparent_mortality_rate": observed_rate,
                "initial_simulated_N": initial_sim,
                "final_simulated_N": final_sim,
                "simulated_stem_loss": simulated_loss,
                "simulated_annual_stem_loss": simulated_loss / years,
                "simulated_apparent_mortality_rate": simulated_rate,
                "mortality_rate_difference": simulated_rate - observed_rate,
                "mortality_rate_ratio": (
                    "" if abs(observed_rate) < 1.0e-15
                    else simulated_rate / observed_rate
                ),
                "initial_observed_G": basal_area[initial_age]["observed"],
                "initial_simulated_G": basal_area[initial_age]["simulated"],
                "empirical_interpretation_status": "pending_data_review",
                "empirical_notes": "",
            }
        )
    return rows


def _write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=INTERVAL_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def _write_markdown(path: Path, rows: list[dict]) -> None:
    lines = [
        "# Apparent stem-loss rates between inventories",
        "",
        "These rates quantify changes in stand density. They must not be "
        "interpreted as natural competition mortality until plot history, "
        "interventions, disturbances, and inventory continuity are confirmed.",
        "",
        "| Interval | Observed loss | Simulated loss | Observed rate | Simulated rate | Rate ratio | Status |",
        "|:---|---:|---:|---:|---:|---:|:---|",
    ]
    for row in rows:
        ratio = row["mortality_rate_ratio"]
        ratio_text = "" if ratio == "" else f"{ratio:.3f}"
        lines.append(
            f"| {row['initial_age']:g}-{row['final_age']:g} | "
            f"{row['observed_stem_loss']:.3f} | "
            f"{row['simulated_stem_loss']:.3f} | "
            f"{100.0 * row['observed_apparent_mortality_rate']:.3f}% yr^-1 | "
            f"{100.0 * row['simulated_apparent_mortality_rate']:.3f}% yr^-1 | "
            f"{ratio_text} | {row['empirical_interpretation_status']} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _plot(path_png: Path, path_pdf: Path, rows: list[dict]) -> None:
    midpoints = np.array(
        [0.5 * (row["initial_age"] + row["final_age"]) for row in rows]
    )
    widths = np.array([row["interval_years"] for row in rows])
    observed = 100.0 * np.array(
        [row["observed_apparent_mortality_rate"] for row in rows]
    )
    simulated = 100.0 * np.array(
        [row["simulated_apparent_mortality_rate"] for row in rows]
    )
    fig, axis = plt.subplots(figsize=(8.7, 4.1))
    axis.step(
        midpoints,
        simulated,
        where="mid",
        color=SIMULATION_COLOR,
        linewidth=1.25,
        label="Simulation",
    )
    axis.scatter(
        midpoints,
        observed,
        facecolor="white",
        edgecolor=OBSERVATION_COLOR,
        linewidth=0.9,
        s=26,
        zorder=3,
        label="Observed density change",
    )
    for midpoint, width, value in zip(midpoints, widths, observed):
        axis.hlines(
            value,
            midpoint - 0.5 * width,
            midpoint + 0.5 * width,
            color=OBSERVATION_COLOR,
            linewidth=0.8,
            alpha=0.60,
        )
    axis.axhline(0.0, color="0.45", linewidth=0.7)
    axis.set_xlabel("Stand age (years)")
    axis.set_ylabel("Apparent stem-loss rate (% yr$^{-1}$)")
    axis.set_axisbelow(True)
    axis.grid(color="0.89", linewidth=0.45, alpha=0.65)
    axis.spines["top"].set_visible(False)
    axis.spines["right"].set_visible(False)
    axis.legend(frameon=False, loc="upper left")
    fig.tight_layout()
    fig.savefig(path_png, dpi=300, bbox_inches="tight")
    fig.savefig(path_pdf, bbox_inches="tight")
    plt.close(fig)


def generate_mortality_interval_diagnostic(
    input_dir: str | Path,
    output_dir: str | Path,
) -> dict:
    source = Path(input_dir)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    comparison_path = source / "observations_simulation.csv"
    reproducibility_path = source / "reproducibility.json"
    if not comparison_path.is_file():
        raise FileNotFoundError(f"Canonical comparison not found: {comparison_path}")
    comparison_rows = _read_comparison(comparison_path)
    interval_rows = build_interval_rows(comparison_rows)
    paths = {
        "csv": output / "mortality_intervals.csv",
        "markdown": output / "mortality_intervals.md",
        "figure_png": output / "figure_mortality_intervals.png",
        "figure_pdf": output / "figure_mortality_intervals.pdf",
        "metadata": output / "mortality_interval_metadata.json",
    }
    _write_csv(paths["csv"], interval_rows)
    _write_markdown(paths["markdown"], interval_rows)
    _plot(paths["figure_png"], paths["figure_pdf"], interval_rows)
    trajectory_commit = "unavailable"
    if reproducibility_path.is_file():
        payload = json.loads(reproducibility_path.read_text(encoding="utf-8"))
        trajectory_commit = payload.get("git_commit", "unavailable")
    metadata = {
        "purpose": "interval diagnosis of apparent observed and simulated stem-density losses",
        "warning": (
            "Observed density changes are not assigned to natural mortality until "
            "plot history, interventions, disturbances, and inventory continuity are confirmed."
        ),
        "rate_definition": "-log(N_final/N_initial)/(final_age-initial_age)",
        "trajectory_commit": trajectory_commit,
        "postprocessing_commit": _git_value("rev-parse", "HEAD"),
        "observation_source": SOURCE_PROVENANCE,
        "n_intervals": len(interval_rows),
        "files": {name: path.name for name, path in paths.items()},
    }
    paths["metadata"].write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
    )
    return {"rows": interval_rows, "paths": paths, "metadata": metadata}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", default="outputs/article_simulation")
    parser.add_argument("--output-dir", default="outputs/article_mortality_intervals")
    args = parser.parse_args()
    result = generate_mortality_interval_diagnostic(args.input_dir, args.output_dir)
    for name, path in result["paths"].items():
        print(f"{name}: {path.resolve()}")


if __name__ == "__main__":
    main()
