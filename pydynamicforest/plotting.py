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
from matplotlib.colors import LogNorm


def ensure_figure_dir(output_dir: str | Path) -> Path:
    """
    Ensure that a figure output directory exists.
    """

    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path

def _density_color_limits(
    arrays: list[np.ndarray],
    scale: str = "linear",
    lower_percentile: float = 1.0,
    upper_percentile: float = 99.0,
) -> tuple[float, float]:
    """
    Compute robust color limits for density heatmaps.

    Parameters
    ----------
    arrays:
        List of density arrays.
    scale:
        Either "linear" or "log".
    lower_percentile:
        Lower percentile used for robust scaling.
    upper_percentile:
        Upper percentile used for robust scaling.

    Returns
    -------
    tuple[float, float]
        vmin and vmax.
    """

    values = np.concatenate([array.ravel() for array in arrays])
    values = values[np.isfinite(values)]

    if values.size == 0:
        return 0.0, 1.0

    if scale == "log":
        positive_values = values[values > 0.0]

        if positive_values.size == 0:
            return 1e-15, 1.0

        vmin = float(np.percentile(positive_values, lower_percentile))
        vmax = float(np.percentile(positive_values, upper_percentile))

        vmin = max(vmin, 1e-15)

    else:
        vmin = float(np.percentile(values, lower_percentile))
        vmax = float(np.percentile(values, upper_percentile))

    if vmax <= vmin:
        vmax = vmin + 1.0

    return vmin, vmax


def plot_observation_density(
    observation: dict,
    output_dir: str | Path,
    filename: str | None = None,
    scale: str = "linear",
    use_percentile_limits: bool = True,
) -> Path:
    """
    Plot the 2D density field U for one exported observation.

    Parameters
    ----------
    observation:
        Observation dictionary produced by load_observation_npz(...).
    output_dir:
        Directory where the figure will be saved.
    filename:
        Optional output filename.
    scale:
        Either "linear" or "log".
    use_percentile_limits:
        If True, use robust percentile-based color limits.

    Notes
    -----
    DBH is displayed in centimeters for readability.
    """

    if scale not in {"linear", "log"}:
        raise ValueError("scale must be either 'linear' or 'log'.")

    output_path = ensure_figure_dir(output_dir)

    U = observation["U"]
    age = observation["age"]
    height = observation["height_grid_physical"]
    dbh_cm = observation["dbh_grid_physical"] * 100.0

    if filename is None:
        filename = f"density_age_{age:.3f}_{scale}.png"

    figure_path = output_path / filename

    if use_percentile_limits:
        vmin, vmax = _density_color_limits(
            [U],
            scale=scale,
            lower_percentile=1.0,
            upper_percentile=99.0,
        )
    else:
        if scale == "log":
            positive_values = U[U > 0.0]
            vmin = max(float(np.min(positive_values)), 1e-15)
            vmax = float(np.max(U))
        else:
            vmin = float(np.min(U))
            vmax = float(np.max(U))

    plt.figure(figsize=(6, 5))

    if scale == "log":
        mesh = plt.pcolormesh(
            dbh_cm,
            height,
            U,
            shading="auto",
            norm=LogNorm(vmin=vmin, vmax=vmax),
        )
        colorbar_label = "Tree density, log scale"
    else:
        mesh = plt.pcolormesh(
            dbh_cm,
            height,
            U,
            shading="auto",
            vmin=vmin,
            vmax=vmax,
        )
        colorbar_label = "Tree density"

    plt.colorbar(mesh, label=colorbar_label)
    plt.xlabel("DBH (cm)")
    plt.ylabel("Height (m)")
    plt.title(f"Density field at age {age:.1f}")
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
        "density_linear": plot_observation_density(
            observation,
            output_dir,
            scale="linear",
        ),
        "density_log": plot_observation_density(
            observation,
            output_dir,
            scale="log",
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
    filename: str | None = None,
    ncols: int = 3,
    scale: str = "linear",
    use_shared_color_scale: bool = True,
    use_percentile_limits: bool = True,
) -> Path:
    """
    Plot 2D density fields for several observations in a grid of subplots.

    Parameters
    ----------
    observations:
        List of observation dictionaries.
    output_dir:
        Directory where the figure will be saved.
    filename:
        Optional output filename.
    ncols:
        Number of subplot columns.
    scale:
        Either "linear" or "log".
    use_shared_color_scale:
        If True, all subplots use the same color scale.
    use_percentile_limits:
        If True, use robust percentile-based color limits.

    Notes
    -----
    DBH is displayed in centimeters for readability.
    """

    if not observations:
        raise ValueError("No observations provided for density comparison.")

    if scale not in {"linear", "log"}:
        raise ValueError("scale must be either 'linear' or 'log'.")

    output_path = ensure_figure_dir(output_dir)

    if filename is None:
        filename = f"density_fields_comparison_{scale}.png"

    figure_path = output_path / filename

    n_obs = len(observations)
    ncols = max(1, min(ncols, n_obs))
    nrows = int(np.ceil(n_obs / ncols))

    density_arrays = [observation["U"] for observation in observations]

    if use_shared_color_scale:
        vmin, vmax = _density_color_limits(
            density_arrays,
            scale=scale,
            lower_percentile=1.0,
            upper_percentile=99.0,
        )
    else:
        vmin, vmax = None, None

    fig, axes = plt.subplots(
        nrows=nrows,
        ncols=ncols,
        figsize=(5.2 * ncols, 4.4 * nrows),
        squeeze=False,
    )

    last_mesh = None

    for index, observation in enumerate(observations):
        row = index // ncols
        col = index % ncols

        ax = axes[row, col]

        U = observation["U"]
        height = observation["height_grid_physical"]
        dbh_cm = observation["dbh_grid_physical"] * 100.0
        age = observation["age"]

        if use_shared_color_scale:
            local_vmin, local_vmax = vmin, vmax
        else:
            local_vmin, local_vmax = _density_color_limits(
                [U],
                scale=scale,
                lower_percentile=1.0,
                upper_percentile=99.0,
            )

        if scale == "log":
            mesh = ax.pcolormesh(
                dbh_cm,
                height,
                U,
                shading="auto",
                norm=LogNorm(vmin=local_vmin, vmax=local_vmax),
            )
        else:
            mesh = ax.pcolormesh(
                dbh_cm,
                height,
                U,
                shading="auto",
                vmin=local_vmin,
                vmax=local_vmax,
            )

        last_mesh = mesh

        ax.set_xlabel("DBH (cm)")
        ax.set_ylabel("Height (m)")
        ax.set_title(f"Age {age:.1f}")

    for index in range(n_obs, nrows * ncols):
        row = index // ncols
        col = index % ncols
        axes[row, col].axis("off")

    colorbar_label = "Tree density"
    if scale == "log":
        colorbar_label = "Tree density, log scale"

    if last_mesh is not None:
        fig.colorbar(
            last_mesh,
            ax=axes.ravel().tolist(),
            label=colorbar_label,
            shrink=0.85,
        )

    fig.suptitle(f"Density fields across observations ({scale} scale)")

    fig.subplots_adjust(
        top=0.86,
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
        "density_fields_linear": plot_density_fields_comparison(
            observations,
            output_dir,
            scale="linear",
        ),
        "density_fields_log": plot_density_fields_comparison(
            observations,
            output_dir,
            scale="log",
        ),
    }