import numpy as np
import pytest

from pydynamicforest.observation_operators import (
    basal_area_consistent,
    dbh_moment,
    dbh_variance,
    height_dbh_correlation,
    height_dbh_covariance,
    height_dbh_cross_moment,
    height_moment,
    height_variance,
    joint_moment_summary,
    mean_dbh,
    mean_height,
    quadratic_mean_dbh,
    stand_density,
    stand_moment,
)
from simulations.article_submission_legacy.config import make_short_debug_config
from simulations.article_submission_legacy.parameters import build_parameters


def make_parameters(nx=5, ny=5, height_scale=40.0, dbh_scale=1.0):
    config = make_short_debug_config()
    config["grid"].update({"nx": nx, "ny": ny})
    config["physical_scales"].update(
        {"height_scale": height_scale, "dbh_scale": dbh_scale}
    )
    return build_parameters(config)


def test_uniform_density_has_analytical_raw_and_normalised_moments():
    p = make_parameters()
    U = np.full((5, 5), 100.0)

    assert stand_moment(U, p) == pytest.approx(stand_density(U, p))
    assert height_moment(U, p) == pytest.approx(2000.0)
    assert dbh_moment(U, p) == pytest.approx(50.0)
    assert height_dbh_cross_moment(U, p) == pytest.approx(1000.0)
    assert mean_height(U, p) == pytest.approx(20.0)
    assert mean_dbh(U, p) == pytest.approx(0.5)
    assert height_variance(U, p) == pytest.approx(150.0)
    assert dbh_variance(U, p) == pytest.approx(0.09375)
    assert height_dbh_covariance(U, p) == pytest.approx(0.0, abs=1.0e-12)
    assert height_dbh_correlation(U, p) == pytest.approx(0.0, abs=1.0e-12)


def test_separable_density_has_zero_height_dbh_covariance():
    p = make_parameters(nx=7, ny=6)
    height_factor = np.linspace(1.0, 3.0, 7)[:, None]
    dbh_factor = np.linspace(2.0, 5.0, 6)[None, :]
    U = height_factor * dbh_factor

    assert height_dbh_covariance(U, p) == pytest.approx(0.0, abs=1.0e-12)
    assert height_dbh_correlation(U, p) == pytest.approx(0.0, abs=1.0e-12)


def test_diagonal_density_has_positive_correlation_and_unit_invariance():
    p = make_parameters(nx=5, ny=5)
    U = np.eye(5) * 100.0

    covariance_m = height_dbh_covariance(U, p, dbh_unit="m")
    covariance_cm = height_dbh_covariance(U, p, dbh_unit="cm")

    assert height_dbh_correlation(U, p) == pytest.approx(1.0)
    assert covariance_cm == pytest.approx(100.0 * covariance_m)
    assert mean_dbh(U, p, unit="cm") == pytest.approx(100.0 * mean_dbh(U, p))
    assert dbh_variance(U, p, unit="cm") == pytest.approx(
        10000.0 * dbh_variance(U, p)
    )


def test_summary_matches_public_operators_and_algebraic_identities():
    p = make_parameters(nx=7, ny=6, height_scale=50.0, dbh_scale=1.2)
    rng = np.random.default_rng(1234)
    U = rng.uniform(0.1, 3.0, size=(7, 6))
    summary = joint_moment_summary(U, p)

    assert summary["stand_density"] == pytest.approx(stand_density(U, p))
    assert summary["mean_height"] == pytest.approx(mean_height(U, p))
    assert summary["mean_dbh_m"] == pytest.approx(mean_dbh(U, p))
    assert summary["height_variance_m2"] == pytest.approx(height_variance(U, p))
    assert summary["dbh_variance_m2"] == pytest.approx(dbh_variance(U, p))
    assert summary["height_dbh_covariance_m2"] == pytest.approx(
        height_dbh_covariance(U, p)
    )
    assert summary["height_dbh_correlation"] == pytest.approx(
        height_dbh_correlation(U, p)
    )
    assert quadratic_mean_dbh(U, p) ** 2 == pytest.approx(
        mean_dbh(U, p) ** 2 + dbh_variance(U, p)
    )
    assert basal_area_consistent(U, p) == pytest.approx(
        0.25 * np.pi * summary["dbh_second_moment_m2"]
    )


def test_zero_density_returns_zero_raw_moments_and_nan_statistics():
    p = make_parameters(nx=3, ny=4)
    U = np.zeros((3, 4))
    summary = joint_moment_summary(U, p)

    assert summary["stand_density"] == 0.0
    assert summary["height_moment"] == 0.0
    assert summary["dbh_moment_m"] == 0.0
    assert np.isnan(summary["mean_height"])
    assert np.isnan(summary["mean_dbh_m"])
    assert np.isnan(summary["height_dbh_correlation"])


def test_moment_orders_and_dbh_units_are_validated():
    p = make_parameters(nx=3, ny=3)
    U = np.ones((3, 3))

    with pytest.raises(ValueError, match="height_order"):
        stand_moment(U, p, height_order=-1)
    with pytest.raises(ValueError, match="dbh_order"):
        stand_moment(U, p, dbh_order=1.5)
    with pytest.raises(ValueError, match="DBH unit"):
        stand_moment(U, p, dbh_order=1, dbh_unit="mm")
