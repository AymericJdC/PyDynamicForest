# SPDX-License-Identifier: LGPL-3.0-or-later
"""Q-9D simulation scenarios for the article revision.

The scenarios preserve the model laws, coefficient values, spatial grid,
solver, and observation operators of ``ARTICLE_CONFIG``. Only the initial age,
initial density, simulation horizon, requested observation ages, and resulting
number of time steps differ.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from pydynamicforest.types import InitialCondition
from simulations.article.config import ARTICLE_CONFIG
from simulations.article.observations import (
    MAIN_COMPARISON_AGES,
    MAIN_INITIAL_AGE,
    TRANSITION_COMPARISON_AGES,
    TRANSITION_INITIAL_AGE,
    observation_at_age,
)

SELECTED_RHOS = (0.50, 0.85, 0.95)
FINAL_AGE = 69.0
HISTORICAL_DT = (
    ARTICLE_CONFIG["time"]["t_end"] - ARTICLE_CONFIG["time"]["t_start"]
) / ARTICLE_CONFIG["time"]["n_steps"]


@dataclass(frozen=True)
class Q9DScenario:
    """One Q-9D simulation scenario and its external initial-state source."""

    name: str
    domain: str
    initial_age: float
    final_age: float
    requested_rho: float
    initial_state_path: Path
    initial_state_key: str
    output_relative_path: Path
    comparison_ages: tuple[float, ...]
    config: dict

    @property
    def duration(self) -> float:
        return self.final_age - self.initial_age


def _rho_label(rho: float) -> str:
    return f"rho_{rho:.2f}"


def _steps_for_duration(duration: float) -> int:
    """Choose the closest integer step count to the historical time step."""
    if duration <= 0.0:
        raise ValueError("scenario duration must be strictly positive.")
    return max(1, int(round(duration / HISTORICAL_DT)))


def build_q9d_config(
    *,
    name: str,
    domain: str,
    initial_age: float,
    final_age: float,
    requested_rho: float,
    comparison_ages: tuple[float, ...],
) -> dict:
    """Return a scenario config with unchanged model and spatial settings."""
    if not np.isfinite(requested_rho) or requested_rho not in SELECTED_RHOS:
        raise ValueError(f"requested_rho must be one of {SELECTED_RHOS}.")
    duration = float(final_age - initial_age)
    n_steps = _steps_for_duration(duration)
    config = deepcopy(ARTICLE_CONFIG)
    config["name"] = name
    config["description"] = (
        f"Q-9D {domain} scenario from GIS Coop age {initial_age:g} to "
        f"age {final_age:g}, using a Gaussian-copula initial state with "
        f"requested rho={requested_rho:.2f}. Dynamic laws and coefficients "
        "are unchanged from ARTICLE_CONFIG."
    )
    config["ages"] = {
        "initial_age": float(initial_age),
        "final_age": float(final_age),
    }
    config["time"] = {
        "t_start": 0.0,
        "t_end": duration,
        "n_steps": n_steps,
    }
    target = observation_at_age(initial_age)
    config["initial_condition"] = {
        "name": f"{name}_copula_initial_state",
        "mass_target": float(target["N"]),
        "distribution_kind": "precomputed_gaussian_copula",
        "source": "Q-9C compatible_initial_states.npz",
        "requested_rho": float(requested_rho),
        "dependence_status": (
            "Representative member of a non-identifiable family of initial "
            "height-DBH distributions compatible with stand-level observables."
        ),
    }
    config["output"] = {
        **config["output"],
        "observation_ages": list(comparison_ages),
        "save_full_trajectory": False,
    }
    config["q9d"] = {
        "domain": domain,
        "historical_dt": HISTORICAL_DT,
        "effective_dt": duration / n_steps,
        "requested_rho": float(requested_rho),
        "dynamic_parameters_recalibrated": False,
    }
    return config


def make_q9d_scenario(
    *,
    domain: str,
    requested_rho: float,
    q9c_root: str | Path = "outputs/article_initial_copula",
) -> Q9DScenario:
    """Create one age-45 or age-38 scenario."""
    rho = float(requested_rho)
    if domain == "main_age45":
        initial_age = MAIN_INITIAL_AGE
        comparison_ages = MAIN_COMPARISON_AGES
        age_directory = "age45"
    elif domain == "transition_age38":
        initial_age = TRANSITION_INITIAL_AGE
        comparison_ages = TRANSITION_COMPARISON_AGES
        age_directory = "age38"
    else:
        raise ValueError("domain must be 'main_age45' or 'transition_age38'.")

    label = _rho_label(rho)
    name = f"q9d_{domain}_{label}"
    source = Path(q9c_root) / age_directory / "compatible_initial_states.npz"
    output_relative_path = Path(domain) / label
    config = build_q9d_config(
        name=name,
        domain=domain,
        initial_age=initial_age,
        final_age=FINAL_AGE,
        requested_rho=rho,
        comparison_ages=comparison_ages,
    )
    return Q9DScenario(
        name=name,
        domain=domain,
        initial_age=initial_age,
        final_age=FINAL_AGE,
        requested_rho=rho,
        initial_state_path=source,
        initial_state_key=label,
        output_relative_path=output_relative_path,
        comparison_ages=comparison_ages,
        config=config,
    )


def selected_q9d_scenarios(
    q9c_root: str | Path = "outputs/article_initial_copula",
) -> tuple[Q9DScenario, ...]:
    """Return the six selected dynamic scenarios in a stable order."""
    return tuple(
        make_q9d_scenario(domain=domain, requested_rho=rho, q9c_root=q9c_root)
        for domain in ("main_age45", "transition_age38")
        for rho in SELECTED_RHOS
    )


def load_scenario_initial_condition(scenario: Q9DScenario) -> InitialCondition:
    """Load one precomputed Q-9C matrix into the standard initial API."""
    if not scenario.initial_state_path.is_file():
        raise FileNotFoundError(
            f"Q-9C initial-state archive not found: {scenario.initial_state_path}"
        )
    with np.load(scenario.initial_state_path) as payload:
        if scenario.initial_state_key not in payload.files:
            raise KeyError(
                f"Missing key {scenario.initial_state_key!r} in "
                f"{scenario.initial_state_path}. Available keys: {payload.files}"
            )
        density = np.array(payload[scenario.initial_state_key], dtype=float, copy=True)
    if density.shape != (
        scenario.config["grid"]["nx"],
        scenario.config["grid"]["ny"],
    ):
        raise ValueError("precomputed initial density has an unexpected grid shape.")
    if not np.all(np.isfinite(density)) or np.any(density < 0.0):
        raise ValueError("precomputed initial density must be finite and non-negative.")
    initial = scenario.config["initial_condition"]
    return InitialCondition(
        name=initial["name"],
        initial_age=scenario.initial_age,
        mass_target=initial["mass_target"],
        distribution_kind=initial["distribution_kind"],
        distribution_parameters={
            "requested_rho": scenario.requested_rho,
            "initial_state_key": scenario.initial_state_key,
        },
        source=initial["source"],
        description=initial["dependence_status"],
        U0=density,
    )
