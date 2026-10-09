from copy import deepcopy

import numpy as np
import pytest

from pydynamicforest.numerics import trapezoidal_weights_1d
from pydynamicforest.observation_operators import (
    basal_area_consistent,
    dbh_marginal_density,
    mean_height,
    physical_dbh_nodes,
    physical_height_nodes,
    quadratic_mean_dbh,
    stand_density,
    height_marginal_density,
)
from simulations.article_submission_legacy.config import ARTICLE_SUBMISSION_CONFIG
from simulations.article_submission_legacy.parameters import build_parameters


def make_parameters(nx=7, ny=6, height_scale=50.0, dbh_scale=1.0):
    config = deepcopy(ARTICLE_SUBMISSION_CONFIG)
    config["grid"].update(
        {"nx": nx, "ny": ny, "x_min": 0.0, "x_max": 1.0, "y_min": 0.0, "y_max": 1.0}
    )
    config["physical_scales"].update(
        {"height_scale": height_scale, "dbh_scale": dbh_scale}
    )
    return build_parameters(config)


def test_constant_density_has_consistent_mass_and_moments():
    p = make_parameters()
    U = np.full((7, 6), 800.0)

    assert stand_density(U, p) == pytest.approx(800.0)
    assert mean_height(U, p) == pytest.approx(25.0)

    dbh_nodes_m = physical_dbh_nodes(p, unit="m")
    dbh_weights = trapezoidal_weights_1d(
        len(dbh_nodes_m),
        dbh_nodes_m[1] - dbh_nodes_m[0],
    )
    expected_dbh_m = np.sqrt(
        np.sum(dbh_weights * dbh_nodes_m**2)
        / np.sum(dbh_weights)
    )

    assert expected_dbh_m == pytest.approx(np.sqrt(0.34))
    assert quadratic_mean_dbh(U, p, unit="m") == pytest.approx(
        expected_dbh_m
    )
    assert quadratic_mean_dbh(U, p, unit="cm") == pytest.approx(
        100.0 * expected_dbh_m
    )


def test_basal_area_identity_is_satisfied():
    p = make_parameters(nx=9, ny=8)
    X, Y = np.meshgrid(p.numerics.grid.x, p.numerics.grid.y, indexing="ij")
    U = 1000.0 * (1.0 + X + 2.0 * Y)

    N = stand_density(U, p)
    Dg = quadratic_mean_dbh(U, p, unit="m")
    G = basal_area_consistent(U, p)

    assert G == pytest.approx(0.25 * np.pi * N * Dg**2, rel=1.0e-14)


def test_marginals_integrate_back_to_total_density():
    p = make_parameters(nx=11, ny=10)
    X, Y = np.meshgrid(p.numerics.grid.x, p.numerics.grid.y, indexing="ij")
    U = 600.0 * np.exp(-((X - 0.4) / 0.2) ** 2 - ((Y - 0.3) / 0.15) ** 2)

    heights_m, height_density = height_marginal_density(U, p)
    dbh_m, dbh_density_m = dbh_marginal_density(U, p, unit="m")
    total = stand_density(U, p)

    height_weights_m = trapezoidal_weights_1d(
        len(heights_m), heights_m[1] - heights_m[0]
    )
    dbh_weights_m = trapezoidal_weights_1d(len(dbh_m), dbh_m[1] - dbh_m[0])

    assert np.sum(height_weights_m * height_density) == pytest.approx(total, rel=1.0e-14)
    assert np.sum(dbh_weights_m * dbh_density_m) == pytest.approx(total, rel=1.0e-14)


def test_dbh_marginal_centimetre_conversion_preserves_mass():
    p = make_parameters(nx=11, ny=10)
    U = np.full((11, 10), 750.0)

    dbh_m, density_m = dbh_marginal_density(U, p, unit="m")
    dbh_cm, density_cm = dbh_marginal_density(U, p, unit="cm")

    np.testing.assert_allclose(dbh_cm, 100.0 * dbh_m)
    np.testing.assert_allclose(density_cm, density_m / 100.0)

    weights_cm = trapezoidal_weights_1d(len(dbh_cm), dbh_cm[1] - dbh_cm[0])
    assert np.sum(weights_cm * density_cm) == pytest.approx(stand_density(U, p))


def test_physical_nodes_follow_configured_scales():
    p = make_parameters(nx=3, ny=3, height_scale=60.0, dbh_scale=1.2)

    np.testing.assert_allclose(physical_height_nodes(p), [0.0, 30.0, 60.0])
    np.testing.assert_allclose(physical_dbh_nodes(p, unit="m"), [0.0, 0.6, 1.2])
    np.testing.assert_allclose(physical_dbh_nodes(p, unit="cm"), [0.0, 60.0, 120.0])


def test_empty_density_returns_nan_for_ratio_observables():
    p = make_parameters()
    U = np.zeros((7, 6))

    assert stand_density(U, p) == pytest.approx(0.0)
    assert np.isnan(mean_height(U, p))
    assert np.isnan(quadratic_mean_dbh(U, p))
    assert basal_area_consistent(U, p) == pytest.approx(0.0)


def test_small_negative_roundoff_is_clipped_but_material_negative_is_rejected():
    p = make_parameters()
    U = np.ones((7, 6))
    U[0, 0] = -0.5 * p.numerics.positivity_tolerance
    assert stand_density(U, p) > 0.0

    U[0, 0] = -2.0 * p.numerics.positivity_tolerance
    with pytest.raises(ValueError, match="non-negative density"):
        stand_density(U, p)


def test_invalid_shape_non_finite_values_and_dbh_units_are_rejected():
    p = make_parameters()

    with pytest.raises(ValueError, match="does not match grid shape"):
        stand_density(np.ones((6, 6)), p)

    non_finite = np.ones((7, 6))
    non_finite[0, 0] = np.nan
    with pytest.raises(ValueError, match="finite values"):
        stand_density(non_finite, p)

    with pytest.raises(ValueError, match="must be 'm' or 'cm'"):
        physical_dbh_nodes(p, unit="mm")
    with pytest.raises(ValueError, match="must be 'm' or 'cm'"):
        quadratic_mean_dbh(np.ones((7, 6)), p, unit="mm")
    with pytest.raises(ValueError, match="must be 'm' or 'cm'"):
        dbh_marginal_density(np.ones((7, 6)), p, unit="mm")


def test_quadratic_mean_dbh_converges_to_continuous_uniform_value():
    analytical_value = np.sqrt(1.0 / 3.0)

    coarse_p = make_parameters(nx=7, ny=6)
    fine_p = make_parameters(nx=7, ny=101)

    coarse_U = np.full(
        (coarse_p.numerics.grid.nx, coarse_p.numerics.grid.ny),
        800.0,
    )
    fine_U = np.full(
        (fine_p.numerics.grid.nx, fine_p.numerics.grid.ny),
        800.0,
    )

    coarse_error = abs(
        quadratic_mean_dbh(coarse_U, coarse_p)
        - analytical_value
    )
    fine_error = abs(
        quadratic_mean_dbh(fine_U, fine_p)
        - analytical_value
    )

    assert fine_error < coarse_error
    assert fine_error < 1.0e-4
