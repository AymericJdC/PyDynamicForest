import pytest

from simulations.article.initial_state_sensitivity import (
    run_initial_state_sensitivity,
    sensitivity_records,
    solve_height_dispersion_for_rho,
)
from simulations.article.observations import observation_at_age
from simulations.article.parameters import build_parameters


def test_height_dispersion_solver_reproduces_age45_dominant_height():
    candidate = solve_height_dispersion_for_rho(
        observation=observation_at_age(45.0),
        p=build_parameters(),
        copula_rho=0.85,
    )
    assert candidate.root_status == "root_found"
    assert candidate.reconstructed_H0_m == pytest.approx(
        candidate.target_H0_m, abs=0.02
    )
    assert candidate.compatible


def test_sensitivity_preserves_requested_order_and_serialises_rows():
    rho_values = (0.70, 0.85)
    candidates = run_initial_state_sensitivity(
        observation=observation_at_age(45.0),
        p=build_parameters(),
        rho_values=rho_values,
    )
    assert tuple(item.requested_rho for item in candidates) == rho_values
    rows = sensitivity_records(candidates)
    assert len(rows) == 2
    assert [row["requested_rho"] for row in rows] == list(rho_values)
    assert all("reconstructed_H0" in row for row in rows)


def test_unbracketed_target_is_reported_without_extrapolation():
    observation = dict(observation_at_age(45.0))
    observation["H0"] = 49.0
    observation["H0_minus_Hm"] = observation["H0"] - observation["Hm"]
    candidate = solve_height_dispersion_for_rho(
        observation=observation,
        p=build_parameters(),
        copula_rho=0.5,
        height_sd_bounds_m=(0.5, 1.0),
    )
    assert candidate.root_status == "target_not_bracketed"
    assert not candidate.compatible
