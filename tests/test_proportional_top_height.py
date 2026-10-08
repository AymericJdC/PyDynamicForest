from copy import deepcopy
import numpy as np
import pytest
from pydynamicforest.diagnostics import legacy_top_height, proportional_top_height
from simulations.article_submission_legacy.config import ARTICLE_SUBMISSION_CONFIG
from simulations.article_submission_legacy.parameters import build_parameters


def make_parameters():
    config = deepcopy(ARTICLE_SUBMISSION_CONFIG)
    config['grid'].update({'nx': 3, 'ny': 3, 'x_min': 0.0, 'x_max': 1.0, 'y_min': 0.0, 'y_max': 1.0})
    return build_parameters(config)


def density_for_stems(stems, p):
    return stems / (p.numerics.grid.dx * p.numerics.grid.dy)


def threshold_example():
    p = make_parameters()
    U = np.zeros((3, 3), dtype=float)
    U[2, 2] = density_for_stems(40.0, p)
    U[0, 1] = density_for_stems(60.0, p)
    U[2, 1] = density_for_stems(60.0, p)
    return p, U


def test_uniform_fraction_of_threshold_class():
    p, U = threshold_example()
    assert proportional_top_height(U, p) == pytest.approx(35.0)


def test_differs_from_legacy_height_tie_break():
    p, U = threshold_example()
    assert proportional_top_height(U, p) == pytest.approx(35.0)
    assert legacy_top_height(U, p) == pytest.approx(50.0)


def test_uses_all_stems_below_target():
    p = make_parameters()
    U = np.zeros((3, 3), dtype=float)
    U[1, 2] = density_for_stems(20.0, p)
    U[2, 1] = density_for_stems(20.0, p)
    assert proportional_top_height(U, p) == pytest.approx(37.5)


def test_handles_exact_target():
    p = make_parameters()
    U = np.zeros((3, 3), dtype=float)
    U[1, 2] = density_for_stems(40.0, p)
    U[2, 1] = density_for_stems(60.0, p)
    assert proportional_top_height(U, p) == pytest.approx(40.0)


def test_is_independent_of_assignment_order():
    p = make_parameters()
    U_a = np.zeros((3, 3), dtype=float)
    U_b = np.zeros((3, 3), dtype=float)
    U_a[2, 2] = U_b[2, 2] = density_for_stems(40.0, p)
    for U in (U_a, U_b):
        U[0, 1] = density_for_stems(30.0, p)
        U[1, 1] = density_for_stems(90.0, p)
    assert proportional_top_height(U_a, p) == pytest.approx(proportional_top_height(U_b, p))


def test_returns_nan_for_empty_population():
    p = make_parameters()
    assert np.isnan(proportional_top_height(np.zeros((3, 3)), p))


def test_rejects_non_positive_target():
    p = make_parameters()
    with pytest.raises(ValueError, match='strictly positive'):
        proportional_top_height(np.ones((3, 3)), p, target_stems_per_ha=0.0)
