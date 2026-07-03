# SPDX-License-Identifier: LGPL-3.0-or-later
"""
Plotting utilities for PyDynamicForest.

This module contains reusable plotting functions.

It should not perform simulations and should not contain project-specific
run logic. Scripts should call these functions.

The matplotlib backend is set to "Agg" so that figures can be generated
without requiring a graphical user interface. This is important for tests,
batch runs and headless environments.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np


def ensure_figure_dir(output_dir: str | Path) -> Path:
    """
    Ensure that a figure output directory exists.
    """

    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def plot_observation_density(
    observation: dict,
    output_dir: str | Path,
    filename: str | None = None,
) -> Path:
    """
    Plot the 2D density field U for one exported observation.

    The observation dictionary is typically produced by
    load_observation_npz(...).

    Expected keys:
        - U
        - age
        - height_grid_physical
        - dbh_grid_physical
    """

    output_path = ensure_figure_dir(output_dir)

    U = observation["U"]
    age = observation["age"]
    height = observation["height_grid_physical"]
    dbh = observation["dbh_grid_physical"]

    if filename is None:
        filename = f"density_age_{age:.3f}.png"

    figure_path = output_path / filename

    plt.figure(figsize=(6, 5))
    plt.pcolormesh(
        dbh,
        height,
        U,
        shading="auto",
    )
    plt.colorbar(label="Tree density")
    plt.xlabel("DBH (m)")
    plt.ylabel("Height (m)")
    plt.title(f"Density field at age {age:.3f}")
    plt.tight_layout()
    plt.savefig(figure_path, dpi=150)
    plt.close()

    return figure_path


def plot_height_distribution_from_observation(
    observation: dict,
    output_dir: str | Path,
    filename: str | None = None,
) -> Path:
    """
    Plot the marginal height distribution for one observation.
    """

    output_path = ensure_figure_dir(output_dir)

    U = observation["U"]
    age = observation["age"]
    height = observation["height_grid_physical"]

    height_normalized = observation["height_grid"]
    dbh_normalized = observation["dbh_grid"]

    if len(height_normalized) > 1:
        dx = height_normalized[1] - height_normalized[0]
    else:
        dx = 1.0

    if len(dbh_normalized) > 1:
        dy = dbh_normalized[1] - dbh_normalized[0]
    else:
        dy = 1.0

    counts = dx * dy * np.sum(U, axis=1)

    if filename is None:
        filename = f"height_distribution_age_{age:.3f}.png"

    figure_path = output_path / filename

    if len(height) > 1:
        width = height[1] - height[0]
    else:
        width = 1.0

    plt.figure(figsize=(6, 4))
    plt.bar(height, counts, width=width)
    plt.xlabel("Height (m)")
    plt.ylabel("Number of trees")
    plt.title(f"Height distribution at age {age:.3f}")
    plt.tight_layout()
    plt.savefig(figure_path, dpi=150)
    plt.close()

    return figure_path


def plot_dbh_distribution_from_observation(
    observation: dict,
    output_dir: str | Path,
    filename: str | None = None,
) -> Path:
    """
    Plot the marginal DBH distribution for one observation.
    """

    output_path = ensure_figure_dir(output_dir)

    U = observation["U"]
    age = observation["age"]
    dbh = observation["dbh_grid_physical"]
    dbh_cm = dbh * 100.0

    height_normalized = observation["height_grid"]
    dbh_normalized = observation["dbh_grid"]

    if len(height_normalized) > 1:
        dx = height_normalized[1] - height_normalized[0]
    else:
        dx = 1.0

    if len(dbh_normalized) > 1:
        dy = dbh_normalized[1] - dbh_normalized[0]
    else:
        dy = 1.0

    counts = dx * dy * np.sum(U, axis=0)

    if filename is None:
        filename = f"dbh_distribution_age_{age:.3f}.png"

    figure_path = output_path / filename

    if len(dbh_cm) > 1:
        width = dbh_cm[1] - dbh_cm[0]
    else:
        width = 1.0

    plt.figure(figsize=(6, 4))
    plt.bar(dbh_cm, counts, width=width)
    plt.xlabel("DBH (cm)")
    plt.ylabel("Number of trees")
    plt.title(f"DBH distribution at age {age:.3f}")
    plt.tight_layout()
    plt.savefig(figure_path, dpi=150)
    plt.close()

    return figure_path


def plot_all_observation_figures(
    observation: dict,
    output_dir: str | Path,
) -> dict[str, Path]:
    """
    Create all standard figures for one observation.

    Returns a dictionary of generated figure paths.
    """

    return {
        "density": plot_observation_density(
            observation,
            output_dir,
        ),
        "height_distribution": plot_height_distribution_from_observation(
            observation,
            output_dir,
        ),
        "dbh_distribution": plot_dbh_distribution_from_observation(
            observation,
            output_dir,
        ),
    }
def plot_time_series_metric(
    time_series: dict,
    metric_key: str,
    output_dir: str | Path,
    x_key: str = "age",
    y_label: str | None = None,
    title: str | None = None,
    filename: str | None = None,
) -> Path:
    """
    Plot one time series metric.

    Parameters
    ----------
    time_series:
        Dictionary containing time series arrays or lists.
    metric_key:
        Key of the metric to plot.
    output_dir:
        Directory where the figure will be saved.
    x_key:
        Key used for the x-axis, typically "age" or "time".
    """

    output_path = ensure_figure_dir(output_dir)

    x = np.asarray(time_series[x_key], dtype=float)
    y = np.asarray(time_series[metric_key], dtype=float)

    if y_label is None:
        y_label = metric_key

    if title is None:
        title = metric_key.replace("_", " ").title()

    if filename is None:
        filename = f"{metric_key}_vs_{x_key}.png"

    figure_path = output_path / filename

    plt.figure(figsize=(6, 4))
    plt.plot(x, y)
    plt.xlabel(x_key.replace("_", " ").title())
    plt.ylabel(y_label)
    plt.title(title)
    plt.grid()
    plt.tight_layout()
    plt.savefig(figure_path, dpi=150)
    plt.close()

    return figure_path

def plot_standard_time_series(
    time_series: dict,
    output_dir: str | Path,
    x_key: str = "age",
) -> dict[str, Path]:
    """
    Plot the standard PyDynamicForest time series diagnostics.

    Expected keys include:
        - total_mass
        - legacy_mass
        - minimum_density
        - top_height
        - basal_area
    """

    figures = {}

    if "total_mass" in time_series:
        figures["total_mass"] = plot_time_series_metric(
            time_series,
            metric_key="total_mass",
            output_dir=output_dir,
            x_key=x_key,
            y_label="Total mass",
            title="Total mass",
        )

    if "legacy_mass" in time_series:
        figures["legacy_mass"] = plot_time_series_metric(
            time_series,
            metric_key="legacy_mass",
            output_dir=output_dir,
            x_key=x_key,
            y_label="Legacy mass",
            title="Legacy mass",
        )

    if "minimum_density" in time_series:
        figures["minimum_density"] = plot_time_series_metric(
            time_series,
            metric_key="minimum_density",
            output_dir=output_dir,
            x_key=x_key,
            y_label="Minimum density",
            title="Minimum density",
        )

    if "top_height" in time_series:
        figures["top_height"] = plot_time_series_metric(
            time_series,
            metric_key="top_height",
            output_dir=output_dir,
            x_key=x_key,
            y_label="Top height (m)",
            title="Top height",
        )

    if "basal_area" in time_series:
        figures["basal_area"] = plot_time_series_metric(
            time_series,
            metric_key="basal_area",
            output_dir=output_dir,
            x_key=x_key,
            y_label="Basal area (m²/ha)",
            title="Basal area",
        )

    return figures
def _normalized_grid_steps(observation: dict) -> tuple[float, float]:
    """
    Return normalized grid steps dx and dy from an observation dictionary.
    """

    height_grid = observation["height_grid"]
    dbh_grid = observation["dbh_grid"]

    if len(height_grid) > 1:
        dx = float(height_grid[1] - height_grid[0])
    else:
        dx = 1.0

    if len(dbh_grid) > 1:
        dy = float(dbh_grid[1] - dbh_grid[0])
    else:
        dy = 1.0

    return dx, dy


def _observation_label(observation: dict) -> str:
    """
    Return a standard label for an observation.
    """

    age = observation["age"]
    step_index = observation["step_index"]

    return f"age={age:.3f}, step={step_index}"


def plot_height_distributions_comparison(
    observations: list[dict],
    output_dir: str | Path,
    filename: str = "height_distributions_comparison.png",
) -> Path:
    """
    Plot marginal height distributions for several observations.

    Each observation is expected to contain:
        - U
        - age
        - step_index
        - height_grid
        - dbh_grid
        - height_grid_physical

    The marginal distribution is computed using the same simple convention
    as previous observation plots:

        counts_h = dx * dy * sum_j U[h_i, d_j]
    """

    if not observations:
        raise ValueError("No observations provided for height comparison.")

    output_path = ensure_figure_dir(output_dir)
    figure_path = output_path / filename

    plt.figure(figsize=(7, 5))

    for observation in observations:
        U = observation["U"]
        height = observation["height_grid_physical"]

        dx, dy = _normalized_grid_steps(observation)
        counts = dx * dy * np.sum(U, axis=1)

        plt.plot(
            height,
            counts,
            marker="o",
            linewidth=1.5,
            label=_observation_label(observation),
        )

    plt.xlabel("Height (m)")
    plt.ylabel("Number of trees")
    plt.title("Height distributions across observations")
    plt.grid()
    plt.legend()
    plt.tight_layout()
    plt.savefig(figure_path, dpi=150)
    plt.close()

    return figure_path


def plot_dbh_distributions_comparison(
    observations: list[dict],
    output_dir: str | Path,
    filename: str = "dbh_distributions_comparison.png",
) -> Path:
    """
    Plot marginal DBH distributions for several observations.

    Each observation is expected to contain:
        - U
        - age
        - step_index
        - height_grid
        - dbh_grid
        - dbh_grid_physical

    The marginal distribution is computed using:

        counts_d = dx * dy * sum_i U[h_i, d_j]
    """

    if not observations:
        raise ValueError("No observations provided for DBH comparison.")

    output_path = ensure_figure_dir(output_dir)
    figure_path = output_path / filename

    plt.figure(figsize=(7, 5))

    for observation in observations:
        U = observation["U"]
        dbh_cm = observation["dbh_grid_physical"] * 100.0

        dx, dy = _normalized_grid_steps(observation)
        counts = dx * dy * np.sum(U, axis=0)

        plt.plot(
            dbh_cm,
            counts,
            marker="o",
            linewidth=1.5,
            label=_observation_label(observation),
        )

    plt.xlabel("DBH (cm)")
    plt.ylabel("Number of trees")
    plt.title("DBH distributions across observations")
    plt.grid()
    plt.legend()
    plt.tight_layout()
    plt.savefig(figure_path, dpi=150)
    plt.close()

    return figure_path

def plot_density_fields_comparison(
    observations: list[dict],
    output_dir: str | Path,
    filename: str = "density_fields_comparison.png",
    ncols: int = 3,
) -> Path:
    """
    Plot 2D density fields for several observations in a grid of subplots.

    A common color scale is used across all observations to make visual
    comparison easier.
    """

    if not observations:
        raise ValueError("No observations provided for density comparison.")

    output_path = ensure_figure_dir(output_dir)
    figure_path = output_path / filename

    n_obs = len(observations)
    ncols = max(1, min(ncols, n_obs))
    nrows = int(np.ceil(n_obs / ncols))

    vmax = max(float(np.max(observation["U"])) for observation in observations)
    vmin = min(float(np.min(observation["U"])) for observation in observations)

    fig, axes = plt.subplots(
        nrows=nrows,
        ncols=ncols,
        figsize=(5 * ncols, 4 * nrows),
        squeeze=False,
    )

    last_mesh = None

    for index, observation in enumerate(observations):
        row = index // ncols
        col = index % ncols

        ax = axes[row, col]

        U = observation["U"]
        height = observation["height_grid_physical"]
        dbh = observation["dbh_grid_physical"]
        age = observation["age"]
        step_index = observation["step_index"]

        mesh = ax.pcolormesh(
            dbh,
            height,
            U,
            shading="auto",
            vmin=vmin,
            vmax=vmax,
        )

        last_mesh = mesh

        ax.set_xlabel("DBH (m)")
        ax.set_ylabel("Height (m)")
        ax.set_title(f"Age {age:.3f}, step {step_index}")

    # Hide unused axes if the grid is larger than the number of observations.
    for index in range(n_obs, nrows * ncols):
        row = index // ncols
        col = index % ncols
        axes[row, col].axis("off")

    if last_mesh is not None:
        fig.colorbar(
            last_mesh,
            ax=axes.ravel().tolist(),
            label="Tree density",
            shrink=0.9,
        )


    fig.suptitle("Density fields across observations")

    fig.subplots_adjust(
        top=0.88,
        right=0.88,
        wspace=0.35,
        hspace=0.35,
    )

    fig.savefig(figure_path, dpi=150)
    plt.close(fig)


    return figure_path


def plot_all_observation_comparison_figures(
    observations: list[dict],
    output_dir: str | Path,
) -> dict[str, Path]:
    """
    Create all standard comparison figures for a list of observations.

    Returns a dictionary of generated figure paths.
    """

    return {
        "height_distributions": plot_height_distributions_comparison(
            observations,
            output_dir,
        ),
        "dbh_distributions": plot_dbh_distributions_comparison(
            observations,
            output_dir,
        ),
        "density_fields": plot_density_fields_comparison(
            observations,
            output_dir,
        ),
    }