from copy import deepcopy

import numpy as np
import pytest

from pydynamicforest.diagnostics import legacy_top_height, top_height
from simulations.article_submission_legacy.config import ARTICLE_SUBMISSION_CONFIG
from simulations.article_submission_legacy.parameters import build_parameters


def make_tie_break_test_parameters():
    config = deepcopy(ARTICLE_SUBMISSION_CONFIG)
    config["grid"].update(
        {
            "nx": 3,
            "ny": 2,
            "x_min": 0.0,
            "x_max": 1.0,
            "y_min": 0.0,
            "y_max": 1.0,
        }
    )
    return build_parameters(config)


def test_legacy_top_height_breaks_dbh_ties_by_decreasing_height():
    p = make_tie_break_test_parameters()
    U = np.zeros((3, 2), dtype=float)

    # dx = 0.5 and dy = 1.0, so a density of 120 represents 60 stems/ha.
    # Both occupied cells have the same, largest DBH. The legacy convention
    # selects the 60 stems at 50 m first, then 40 of the 60 stems at 0 m.
    U[0, 1] = 120.0
    U[2, 1] = 120.0

    value = legacy_top_height(U, p, target_stems_per_ha=100.0)

    assert value == pytest.approx((60.0 * 50.0 + 40.0 * 0.0) / 100.0)
    assert value == pytest.approx(30.0)


def test_legacy_top_height_is_distinct_from_current_stable_dbh_only_sort():
    p = make_tie_break_test_parameters()
    U = np.zeros((3, 2), dtype=float)
    U[0, 1] = 120.0
    U[2, 1] = 120.0

    legacy_value = legacy_top_height(U, p, target_stems_per_ha=100.0)
    current_value = top_height(U, p, target_stems_per_ha=100.0)

    assert legacy_value == pytest.approx(30.0)
    assert current_value == pytest.approx(20.0)
    assert legacy_value != current_value


def test_legacy_top_height_uses_all_available_stems_below_target():
    p = make_tie_break_test_parameters()
    U = np.zeros((3, 2), dtype=float)

    # Two cells of 20 stems/ha each at heights 25 m and 50 m.
    U[1, 1] = 40.0
    U[2, 1] = 40.0

    value = legacy_top_height(U, p, target_stems_per_ha=100.0)

    assert value == pytest.approx((20.0 * 25.0 + 20.0 * 50.0) / 40.0)
    assert value == pytest.approx(37.5)


def test_legacy_top_height_rejects_non_positive_target():
    p = make_tie_break_test_parameters()
    U = np.ones((3, 2), dtype=float)

    with pytest.raises(ValueError, match="strictly positive"):
        legacy_top_height(U, p, target_stems_per_ha=0.0)
