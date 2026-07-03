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