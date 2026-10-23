from copy import deepcopy

import pytest

from simulations.article.config import ARTICLE_CONFIG
from simulations.article.scenarios import (
    HISTORICAL_DT,
    SELECTED_RHOS,
    make_q9d_scenario,
    selected_q9d_scenarios,
)


def test_selected_scenarios_cover_two_domains_and_three_rhos():
    scenarios = selected_q9d_scenarios()
    assert len(scenarios) == 6
    assert {item.domain for item in scenarios} == {
        "main_age45",
        "transition_age38",
    }
    assert {item.requested_rho for item in scenarios} == set(SELECTED_RHOS)
    assert len({item.output_relative_path for item in scenarios}) == 6


def test_main_and_transition_horizons_preserve_model_and_grid():
    for domain, initial_age, expected_count in (
        ("main_age45", 45.0, 9),
        ("transition_age38", 38.0, 11),
    ):
        scenario = make_q9d_scenario(domain=domain, requested_rho=0.85)
        config = scenario.config
        assert scenario.initial_age == initial_age
        assert scenario.final_age == 69.0
        assert len(scenario.comparison_ages) == expected_count
        assert config["model"] == ARTICLE_CONFIG["model"]
        assert config["grid"] == ARTICLE_CONFIG["grid"]
        assert config["solver"] == ARTICLE_CONFIG["solver"]
        assert config["physical_scales"] == ARTICLE_CONFIG["physical_scales"]
        assert config["q9d"]["dynamic_parameters_recalibrated"] is False
        assert config["time"]["t_end"] == pytest.approx(69.0 - initial_age)
        assert config["time"]["t_end"] / config["time"]["n_steps"] == pytest.approx(
            HISTORICAL_DT, abs=5.0e-7
        )


def test_scenario_config_does_not_mutate_article_config():
    before = deepcopy(ARTICLE_CONFIG)
    make_q9d_scenario(domain="main_age45", requested_rho=0.50)
    assert ARTICLE_CONFIG == before
