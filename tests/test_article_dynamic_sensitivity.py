from simulations.article.config import ARTICLE_CONFIG
from simulations.article.dynamic_sensitivity import (
    BASELINE_VALUES,
    FACTOR_LEVELS,
    PARAMETER_PATHS,
    selected_dynamic_sensitivity_cases,
)


def test_oat_design_has_eight_unique_cases():
    cases = selected_dynamic_sensitivity_cases()
    assert len(cases) == 8
    assert len({case.name for case in cases}) == 8
    assert {case.parameter for case in cases} == set(PARAMETER_PATHS)
    assert {case.multiplier for case in cases} == set(FACTOR_LEVELS)


def test_each_case_changes_exactly_one_dynamic_value():
    for case in selected_dynamic_sensitivity_cases():
        config = case.scenario.config
        for parameter, (section, field) in PARAMETER_PATHS.items():
            value = config["model"][section][field]
            expected = (
                BASELINE_VALUES[parameter] * case.multiplier
                if parameter == case.parameter
                else BASELINE_VALUES[parameter]
            )
            assert value == expected
        assert config["grid"] == ARTICLE_CONFIG["grid"]
        assert config["solver"] == ARTICLE_CONFIG["solver"]
        assert case.scenario.initial_age == 45.0
        assert case.scenario.requested_rho == 0.85
        assert config["q9d"]["dynamic_parameters_recalibrated"] is False
