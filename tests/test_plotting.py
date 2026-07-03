# SPDX-License-Identifier: LGPL-3.0-or-later
import numpy as np

from pydynamicforest.plotting import (
    plot_observation_density,
    plot_height_distribution_from_observation,
    plot_dbh_distribution_from_observation,
    plot_all_observation_figures,
    plot_time_series_metric,
    plot_standard_time_series,
)


def make_fake_observation():
    height_grid = np.linspace(0.0, 1.0, 5)
    dbh_grid = np.linspace(0.0, 1.0, 4)

    U = np.ones((len(height_grid), len(dbh_grid)))

    return {
        "U": U,
        "time": 0.0,
        "age": 18.0,
        "step_index": 0,
        "height_grid": height_grid,
        "dbh_grid": dbh_grid,
        "height_grid_physical": height_grid * 50.0,
        "dbh_grid_physical": dbh_grid * 0.9,
    }


def test_plot_observation_density_creates_file(tmp_path):
    observation = make_fake_observation()

    figure_path = plot_observation_density(
        observation,
        output_dir=tmp_path,
    )

    assert figure_path.exists()
    assert figure_path.is_file()
    assert figure_path.suffix == ".png"


def test_plot_height_distribution_creates_file(tmp_path):
    observation = make_fake_observation()

    figure_path = plot_height_distribution_from_observation(
        observation,
        output_dir=tmp_path,
    )

    assert figure_path.exists()
    assert figure_path.is_file()
    assert figure_path.suffix == ".png"


def test_plot_dbh_distribution_creates_file(tmp_path):
    observation = make_fake_observation()

    figure_path = plot_dbh_distribution_from_observation(
        observation,
        output_dir=tmp_path,
    )

    assert figure_path.exists()
    assert figure_path.is_file()
    assert figure_path.suffix == ".png"


def test_plot_all_observation_figures_creates_expected_files(tmp_path):
    observation = make_fake_observation()

    figures = plot_all_observation_figures(
        observation,
        output_dir=tmp_path,
    )

    assert set(figures.keys()) == {
        "density",
        "height_distribution",
        "dbh_distribution",
    }

    for figure_path in figures.values():
        assert figure_path.exists()
        assert figure_path.is_file()
        assert figure_path.suffix == ".png"

def make_fake_time_series():
    return {
        "time": [0.0, 1.0, 2.0],
        "age": [18.0, 19.0, 20.0],
        "total_mass": [2000.0, 1800.0, 1600.0],
        "legacy_mass": [1990.0, 1790.0, 1590.0],
        "minimum_density": [0.0, 1e-10, 1e-9],
        "top_height": [10.0, 12.0, 14.0],
        "basal_area": [20.0, 25.0, 30.0],
    }

def test_plot_time_series_metric_creates_file(tmp_path):
    time_series = make_fake_time_series()

    figure_path = plot_time_series_metric(
        time_series,
        metric_key="total_mass",
        output_dir=tmp_path,
        x_key="age",
    )

    assert figure_path.exists()
    assert figure_path.is_file()
    assert figure_path.suffix == ".png"


def test_plot_standard_time_series_creates_expected_files(tmp_path):
    time_series = make_fake_time_series()

    figures = plot_standard_time_series(
        time_series,
        output_dir=tmp_path,
        x_key="age",
    )

    assert set(figures.keys()) == {
        "total_mass",
        "legacy_mass",
        "minimum_density",
        "top_height",
        "basal_area",
    }

    for figure_path in figures.values():
        assert figure_path.exists()
        assert figure_path.is_file()
        assert figure_path.suffix == ".png"