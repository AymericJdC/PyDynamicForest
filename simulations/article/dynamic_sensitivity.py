# SPDX-License-Identifier: LGPL-3.0-or-later
"""Local one-at-a-time screening of Q-9D dynamic parameters.

The screening keeps the age-45, rho=0.85 reconstructed initial state fixed and
changes exactly one dynamic coefficient at a time. It is a sensitivity
analysis, not a calibration.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, replace
from pathlib import Path

from simulations.article.scenarios import Q9DScenario, make_q9d_scenario

BASELINE_VALUES = {
    "height_growth": 1.66,
    "dbh_growth": 0.0155,
    "diffusion": 1.0e-5,
    "mortality": 0.033,
}
FACTOR_LEVELS = (0.80, 1.20)
PARAMETER_PATHS = {
    "height_growth": ("height_growth", "physical_rate"),
    "dbh_growth": ("dbh_growth", "physical_rate"),
    "diffusion": ("diffusion", "value"),
    "mortality": ("mortality", "value"),
}


@dataclass(frozen=True)
class DynamicSensitivityCase:
    """One OAT perturbation around the unchanged-parameter Q-9D baseline."""

    name: str
    parameter: str
    multiplier: float
    baseline_value: float
    perturbed_value: float
    scenario: Q9DScenario


def case_name(parameter: str, multiplier: float) -> str:
    return f"{parameter}_x{multiplier:.2f}"


def make_dynamic_sensitivity_case(
    *,
    parameter: str,
    multiplier: float,
    q9c_root: str | Path = "outputs/article_initial_copula",
) -> DynamicSensitivityCase:
    """Create one age-45 rho=0.85 OAT scenario."""
    if parameter not in PARAMETER_PATHS:
        raise ValueError(f"Unknown parameter {parameter!r}.")
    if multiplier not in FACTOR_LEVELS:
        raise ValueError(f"multiplier must be one of {FACTOR_LEVELS}.")

    baseline = make_q9d_scenario(
        domain="main_age45",
        requested_rho=0.85,
        q9c_root=q9c_root,
    )
    config = deepcopy(baseline.config)
    section, field = PARAMETER_PATHS[parameter]
    baseline_value = float(config["model"][section][field])
    expected = BASELINE_VALUES[parameter]
    if baseline_value != expected:
        raise ValueError(
            f"Unexpected baseline for {parameter}: {baseline_value}, expected {expected}."
        )
    perturbed_value = multiplier * baseline_value
    config["model"][section][field] = perturbed_value

    label = case_name(parameter, multiplier)
    config["name"] = f"q9e_oat_age45_rho_0.85_{label}"
    config["description"] = (
        "Q-9E local one-at-a-time dynamic-parameter screening at age 45 "
        f"with requested rho=0.85: {parameter} multiplied by {multiplier:.2f}. "
        "All other dynamic and numerical settings are unchanged."
    )
    config["q9d"] = {
        **config["q9d"],
        "sensitivity_design": "one_at_a_time",
        "sensitivity_parameter": parameter,
        "sensitivity_multiplier": multiplier,
        "sensitivity_baseline_value": baseline_value,
        "sensitivity_perturbed_value": perturbed_value,
        "dynamic_parameters_recalibrated": False,
    }
    scenario = replace(
        baseline,
        name=config["name"],
        output_relative_path=Path("sensitivity") / "oat_age45_rho_0.85" / label,
        config=config,
    )
    return DynamicSensitivityCase(
        name=label,
        parameter=parameter,
        multiplier=multiplier,
        baseline_value=baseline_value,
        perturbed_value=perturbed_value,
        scenario=scenario,
    )


def selected_dynamic_sensitivity_cases(
    q9c_root: str | Path = "outputs/article_initial_copula",
) -> tuple[DynamicSensitivityCase, ...]:
    """Return the eight OAT perturbations in stable order."""
    return tuple(
        make_dynamic_sensitivity_case(
            parameter=parameter,
            multiplier=multiplier,
            q9c_root=q9c_root,
        )
        for parameter in (
            "height_growth",
            "dbh_growth",
            "diffusion",
            "mortality",
        )
        for multiplier in FACTOR_LEVELS
    )
