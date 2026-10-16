import numpy as np
import pytest

from pydynamicforest.initial_conditions import build_initial_state
from pydynamicforest.observation_operators import (
    continuous_dominant_height_details,
    height_dbh_correlation,
    joint_moment_summary,
    stand_density,
)
from simulations.article.context import build_context
from simulations.article.initial_condition import build_initial_condition
from simulations.article.parameters import build_parameters


def test_article_initial_condition_matches_audited_reconstruction():
    p = build_parameters()
    state = build_initial_state(build_initial_condition(), p, build_context())
    summary = joint_moment_summary(state.U, p)
    dominant = continuous_dominant_height_details(state.U, p)
    assert state.U.shape == (40, 40)
    assert np.min(state.U) >= 0.0
    assert stand_density(state.U, p) == pytest.approx(1924.34, abs=1.0e-9)
    assert summary["mean_height"] == pytest.approx(9.613157296138, abs=1.0e-9)
    assert height_dbh_correlation(state.U, p) == pytest.approx(0.857094656455, abs=1.0e-9)
    assert dominant["dominant_height"] == pytest.approx(11.659849276837, abs=1.0e-9)
    assert dominant["threshold_dbh"] * 100.0 == pytest.approx(16.133915303908, abs=1.0e-9)


def test_article_initial_condition_records_reconstruction_status():
    initial = build_initial_condition()
    assert initial.distribution_parameters["height_dbh_correlation"] == pytest.approx(
        0.8490113967
    )
    assert "not estimated from individual-tree records" in initial.description
