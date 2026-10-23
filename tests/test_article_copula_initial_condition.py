import numpy as np
import pytest

from pydynamicforest.observation_operators import stand_density
from simulations.article.copula_initial_condition import (
    build_gaussian_copula_initial_state,
    gaussian_copula_density,
)
from simulations.article.observations import observation_at_age
from simulations.article.parameters import build_parameters


def test_zero_rho_copula_density_is_independence():
    u = np.linspace(0.05, 0.95, 7)
    v = np.linspace(0.05, 0.95, 9)
    density = gaussian_copula_density(u, v, 0.0)
    assert density.shape == (7, 9)
    assert np.all(density == 1.0)


def test_invalid_copula_parameters_are_rejected():
    u = np.linspace(0.1, 0.9, 4)
    with pytest.raises(ValueError, match="strictly between -1 and 1"):
        gaussian_copula_density(u, u, 1.0)

    p = build_parameters()
    with pytest.raises(ValueError, match="positive"):
        build_gaussian_copula_initial_state(
            observation=observation_at_age(45.0),
            p=p,
            height_kernel_sd_m=0.0,
            copula_rho=0.8,
        )


def test_age45_candidate_matches_mass_and_calibrated_marginals():
    p = build_parameters()
    observation = observation_at_age(45.0)
    result = build_gaussian_copula_initial_state(
        observation=observation,
        p=p,
        height_kernel_sd_m=2.2,
        copula_rho=0.85,
    )

    assert result.density.shape == (p.numerics.grid.nx, p.numerics.grid.ny)
    assert np.all(np.isfinite(result.density))
    assert np.min(result.density) >= 0.0
    assert stand_density(result.density, p) == pytest.approx(
        observation["N"], rel=1.0e-10, abs=1.0e-8
    )
    assert result.reconstructed_observables["Hm"] == pytest.approx(
        observation["Hm"], abs=0.01
    )
    assert result.reconstructed_observables["Dm"] == pytest.approx(
        observation["Dm"], abs=0.01
    )
    assert result.reconstructed_observables["sigma_D"] == pytest.approx(
        observation["sigma_D"], abs=0.02
    )
    assert result.selected_stems_per_ha == pytest.approx(100.0, abs=1.0e-6)


def test_effective_dependence_increases_with_requested_rho():
    p = build_parameters()
    observation = observation_at_age(45.0)
    low = build_gaussian_copula_initial_state(
        observation=observation,
        p=p,
        height_kernel_sd_m=2.2,
        copula_rho=0.5,
    )
    high = build_gaussian_copula_initial_state(
        observation=observation,
        p=p,
        height_kernel_sd_m=2.2,
        copula_rho=0.9,
    )
    assert high.effective_rho > low.effective_rho
    assert high.reconstructed_observables["H0"] > low.reconstructed_observables["H0"]
