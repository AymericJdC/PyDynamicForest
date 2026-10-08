import numpy as np
import pytest

from pydynamicforest.initial_conditions import build_initial_state
from pydynamicforest.numerics import integrate_2d_trapezoidal
from simulations.article_submission_legacy.config import ARTICLE_SUBMISSION_CONFIG
from simulations.article_submission_legacy.context import build_context
from simulations.article_submission_legacy.initial_condition import build_initial_condition
from simulations.article_submission_legacy.parameters import build_parameters


def test_article_submission_configuration_matches_transmitted_script():
    config = ARTICLE_SUBMISSION_CONFIG

    assert config["ages"] == {"initial_age": 18.0, "final_age": 69.0}
    assert config["physical_scales"] == {"height_scale": 50.0, "dbh_scale": 1.0}
    assert config["grid"]["nx"] == 40
    assert config["grid"]["ny"] == 40
    assert config["time"]["t_end"] == 51.0
    assert config["time"]["n_steps"] == 10000

    initial = config["initial_condition"]
    assert initial["mass_target"] == pytest.approx(1924.34)
    assert initial["h0_physical"] == pytest.approx(9.61)
    assert initial["d0_physical"] == pytest.approx(0.1169)
    assert initial["sigma_h_physical"] == pytest.approx(1.3)
    assert initial["sigma_d_physical"] == pytest.approx(0.025)

    model = config["model"]
    assert model["diffusion"]["value"] == pytest.approx(1.0e-5)
    assert model["mortality"]["value"] == pytest.approx(0.033)
    assert model["height_growth"]["physical_rate"] == pytest.approx(1.66)
    assert model["dbh_growth"]["physical_rate"] == pytest.approx(0.0155)


def test_article_submission_builders_are_mutually_consistent():
    x0 = build_initial_condition()
    p = build_parameters()
    c = build_context()

    assert x0.initial_age == pytest.approx(c.initial_age)
    assert c.final_age - c.initial_age == pytest.approx(p.numerics.time.t_end)
    assert (p.numerics.grid.nx, p.numerics.grid.ny) == (40, 40)
    assert p.numerics.time.dt == pytest.approx(51.0 / 10000.0)
    assert c.output.observation_ages == [18.0, 45.0, 69.0]


def test_article_submission_initial_state_has_target_trapezoidal_mass():
    x0 = build_initial_condition()
    p = build_parameters()
    c = build_context()

    state = build_initial_state(x0, p, c)
    grid = p.numerics.grid
    mass = integrate_2d_trapezoidal(state.U, grid.dx, grid.dy)

    assert state.U.shape == (40, 40)
    assert np.all(state.U >= 0.0)
    assert mass == pytest.approx(1924.34, rel=1.0e-12, abs=1.0e-10)
    assert state.time == pytest.approx(0.0)
    assert state.age == pytest.approx(18.0)
