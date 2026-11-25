from copy import deepcopy

import numpy as np
import pytest

from pydynamicforest.initial_conditions import build_initial_state
from pydynamicforest.observation_operators import (
    continuous_dominant_height_details,
    height_dbh_correlation,
    mean_height,
    stand_density,
)
from simulations.article_submission_legacy.config import ARTICLE_SUBMISSION_CONFIG
from simulations.article_submission_legacy.context import build_context
from simulations.article_submission_legacy.correlated_initial_condition import (
    DEFAULT_HEIGHT_DBH_CORRELATION,
    build_correlated_initial_condition,
)
from simulations.article_submission_legacy.initial_condition import build_initial_condition
from simulations.article_submission_legacy.parameters import build_parameters


def _state(initial_condition):
    p = build_parameters()
    c = build_context()
    return build_initial_state(initial_condition, p, c), p


def test_zero_correlation_exactly_reproduces_separable_initial_density():
    legacy, _ = _state(build_initial_condition())
    zero, _ = _state(build_correlated_initial_condition(correlation=0.0))
    np.testing.assert_allclose(zero.U, legacy.U, rtol=2.0e-15, atol=0.0)


def test_proposed_condition_reproduces_audited_initial_joint_state():
    state, p = _state(build_correlated_initial_condition())
    assert stand_density(state.U, p) == pytest.approx(1924.34, abs=1.0e-9)
    assert mean_height(state.U, p) == pytest.approx(9.613157296138, abs=1.0e-9)
    assert height_dbh_correlation(state.U, p) == pytest.approx(
        0.857094656455, abs=1.0e-9
    )
    details = continuous_dominant_height_details(state.U, p)
    assert details["dominant_height"] == pytest.approx(11.659849276837, abs=1.0e-9)


def test_invalid_correlations_are_rejected_by_generic_builder():
    for correlation in (-1.0, 1.0, float("nan"), float("inf")):
        initial = build_correlated_initial_condition(correlation=correlation)
        with pytest.raises(ValueError, match="height_dbh_correlation"):
            _state(initial)


def test_correlated_builder_does_not_mutate_article_configuration():
    before = deepcopy(ARTICLE_SUBMISSION_CONFIG)
    initial = build_correlated_initial_condition()
    assert ARTICLE_SUBMISSION_CONFIG == before
    assert initial.distribution_parameters["height_dbh_correlation"] == pytest.approx(
        DEFAULT_HEIGHT_DBH_CORRELATION
    )
    assert "height_dbh_correlation" not in ARTICLE_SUBMISSION_CONFIG["initial_condition"]
