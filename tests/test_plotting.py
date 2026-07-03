import numpy as np

from pydynamicforest.plotting import (
    plot_observation_density,
    plot_height_distribution_from_observation,
    plot_dbh_distribution_from_observation,
    plot_all_observation_figures,
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