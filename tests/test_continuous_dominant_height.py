from copy import deepcopy

import numpy as np
import pytest

from pydynamicforest.observation_operators import (
    continuous_dominant_height,
    continuous_dominant_height_details,
    mean_height,
)
from simulations.article_submission_legacy.config import ARTICLE_SUBMISSION_CONFIG
from simulations.article_submission_legacy.parameters import build_parameters


def make_parameters(nx=41, ny=21):
    config = deepcopy(ARTICLE_SUBMISSION_CONFIG)
    config["grid"].update(
        {"nx": nx, "ny": ny, "x_min": 0.0, "x_max": 1.0, "y_min": 0.0, "y_max": 1.0}
    )
    config["physical_scales"].update(
        {"height_scale": 50.0, "dbh_scale": 1.0}
    )
    return build_parameters(config)


def test_uniform_density_has_analytical_threshold_and_mean_height():
    p = make_parameters()
    U = np.full((p.numerics.grid.nx, p.numerics.grid.ny), 800.0)

    details = continuous_dominant_height_details(U, p)

    assert details["total_stems"] == pytest.approx(800.0)
    assert details["selected_stems"] == pytest.approx(100.0, abs=1.0e-10)
    assert details["threshold_dbh"] == pytest.approx(0.875, abs=1.0e-12)
    assert details["dominant_height"] == pytest.approx(25.0, abs=1.0e-12)
    assert continuous_dominant_height(U, p) == pytest.approx(25.0)


def test_affine_dbh_marginal_has_grid_independent_analytical_threshold():
    expected_threshold = -1.0 + np.sqrt(3.625)

    for ny in (11, 21, 81):
        p = make_parameters(ny=ny)
        Y = np.broadcast_to(
            p.numerics.grid.y[None, :],
            (p.numerics.grid.nx, p.numerics.grid.ny),
        )
        # Integral of 1 + y on [0, 1] is 1.5; scale to 800 stems/ha.
        U = (800.0 / 1.5) * (1.0 + Y)

        details = continuous_dominant_height_details(U, p)

        assert details["threshold_dbh"] == pytest.approx(
            expected_threshold,
            abs=2.0e-12,
        )
        assert details["selected_stems"] == pytest.approx(100.0, abs=1.0e-10)
        assert details["dominant_height"] == pytest.approx(25.0, abs=1.0e-12)


def test_separable_density_returns_same_height_mean_in_every_dbh_tail():
    p = make_parameters(nx=61, ny=31)
    X, Y = np.meshgrid(p.numerics.grid.x, p.numerics.grid.y, indexing="ij")
    U = 900.0 * np.exp(-((X - 0.6) / 0.12) ** 2) * (1.0 + 2.0 * Y)

    assert continuous_dominant_height(U, p) == pytest.approx(
        mean_height(U, p),
        rel=1.0e-13,
        abs=1.0e-13,
    )


def test_population_below_target_uses_all_stems_and_lowest_threshold():
    p = make_parameters()
    U = np.full((p.numerics.grid.nx, p.numerics.grid.ny), 40.0)

    details = continuous_dominant_height_details(U, p, target_stems_per_ha=100.0)

    assert details["total_stems"] == pytest.approx(40.0)
    assert details["selected_stems"] == pytest.approx(40.0)
    assert details["threshold_dbh"] == pytest.approx(0.0)
    assert details["dominant_height"] == pytest.approx(mean_height(U, p))


def test_exact_target_uses_full_domain():
    p = make_parameters()
    U = np.full((p.numerics.grid.nx, p.numerics.grid.ny), 100.0)

    details = continuous_dominant_height_details(U, p)

    assert details["threshold_dbh"] == pytest.approx(0.0)
    assert details["selected_stems"] == pytest.approx(100.0)
    assert details["dominant_height"] == pytest.approx(25.0)


def test_empty_population_returns_nan_details():
    p = make_parameters()
    U = np.zeros((p.numerics.grid.nx, p.numerics.grid.ny))

    details = continuous_dominant_height_details(U, p)

    assert np.isnan(details["dominant_height"])
    assert np.isnan(details["threshold_dbh"])
    assert details["selected_stems"] == 0.0
    assert details["total_stems"] == 0.0
    assert details["threshold_interval_index"] == -1


def test_zero_density_plateau_does_not_change_selected_tail_moment():
    p = make_parameters(nx=41, ny=5)
    U = np.zeros((p.numerics.grid.nx, p.numerics.grid.ny))
    U[:, 0] = 400.0
    U[:, -1] = 400.0

    details = continuous_dominant_height_details(
        U,
        p,
        target_stems_per_ha=25.0,
    )

    assert details["selected_stems"] == pytest.approx(25.0, abs=1.0e-10)
    assert details["dominant_height"] == pytest.approx(25.0)
    assert 0.75 < details["threshold_dbh"] < 1.0


def test_roundoff_negative_is_tolerated_and_material_negative_is_rejected():
    p = make_parameters()
    U = np.full((p.numerics.grid.nx, p.numerics.grid.ny), 800.0)
    U[0, 0] = -0.5 * p.numerics.positivity_tolerance
    assert np.isfinite(continuous_dominant_height(U, p))

    U[0, 0] = -2.0 * p.numerics.positivity_tolerance
    with pytest.raises(ValueError, match="non-negative density"):
        continuous_dominant_height(U, p)


def test_non_positive_target_is_rejected():
    p = make_parameters()
    U = np.ones((p.numerics.grid.nx, p.numerics.grid.ny))

    with pytest.raises(ValueError, match="strictly positive"):
        continuous_dominant_height(U, p, target_stems_per_ha=0.0)
