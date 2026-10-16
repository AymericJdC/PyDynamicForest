import numpy as np
import pytest

from simulations.article.context import build_context
from simulations.article.run import run_article_simulation


def test_article_zero_step_run_preserves_correlated_initial_state():
    results = run_article_simulation(max_steps=0)
    state = results.final_state
    context = build_context()
    assert state.time == pytest.approx(0.0)
    assert state.age == pytest.approx(context.initial_age)
    assert state.step_index == 0
    assert np.min(state.U) >= 0.0


def test_article_one_step_run_advances_time_and_remains_nonnegative():
    results = run_article_simulation(max_steps=1)
    state = results.final_state
    context = build_context()
    assert state.time > 0.0
    assert state.age > context.initial_age
    assert state.step_index == 1
    assert np.min(state.U) >= -1.0e-12
