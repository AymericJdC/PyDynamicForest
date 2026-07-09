# SPDX-License-Identifier: LGPL-3.0-or-later

from argparse import Namespace

from scripts.run_baseline import apply_cli_overrides

from simulations.baseline.config import BASELINE_CONFIG, copy_baseline_config
from simulations.baseline.initial_condition import build_initial_condition
from simulations.baseline.parameters import build_parameters
from simulations.baseline.context import build_context

from pydynamicforest.initial_conditions import build_initial_state
from pydynamicforest.solver import simulate


def test_baseline_config_contains_expected_sections():
    assert "name" in BASELINE_CONFIG
    assert "description" in BASELINE_CONFIG
    assert "ages" in BASELINE_CONFIG
    assert "initial_condition" in BASELINE_CONFIG
    assert "physical_scales" in BASELINE_CONFIG
    assert "grid" in BASELINE_CONFIG
    assert "time" in BASELINE_CONFIG
    assert "model" in BASELINE_CONFIG
    assert "solver" in BASELINE_CONFIG
    assert "output" in BASELINE_CONFIG


def test_baseline_initial_condition_uses_config_values():
    x0 = build_initial_condition()
    cfg = BASELINE_CONFIG

    assert x0.name == cfg["initial_condition"]["name"]
    assert x0.initial_age == cfg["ages"]["initial_age"]
    assert x0.mass_target == cfg["initial_condition"]["mass_target"]
    assert x0.distribution_kind == cfg["initial_condition"]["distribution_kind"]
    assert x0.source == cfg["initial_condition"]["source"]

    assert x0.distribution_parameters["h0_physical"] == (
        cfg["initial_condition"]["h0_physical"]
    )
    assert x0.distribution_parameters["d0_physical"] == (
        cfg["initial_condition"]["d0_physical"]
    )
    assert x0.distribution_parameters["sigma_h_physical"] == (
        cfg["initial_condition"]["sigma_h_physical"]
    )
    assert x0.distribution_parameters["sigma_d_physical"] == (
        cfg["initial_condition"]["sigma_d_physical"]
    )


def test_baseline_parameters_use_config_values():
    p = build_parameters()
    cfg = BASELINE_CONFIG

    assert p.name == cfg["name"]
    assert p.description == cfg["description"]

    assert p.model.physical_scales.height_scale == (
        cfg["physical_scales"]["height_scale"]
    )
    assert p.model.physical_scales.dbh_scale == (
        cfg["physical_scales"]["dbh_scale"]
    )

    assert p.numerics.grid.nx == cfg["grid"]["nx"]
    assert p.numerics.grid.ny == cfg["grid"]["ny"]
    assert p.numerics.grid.x_min == cfg["grid"]["x_min"]
    assert p.numerics.grid.x_max == cfg["grid"]["x_max"]
    assert p.numerics.grid.y_min == cfg["grid"]["y_min"]
    assert p.numerics.grid.y_max == cfg["grid"]["y_max"]

    assert p.numerics.time.t_start == cfg["time"]["t_start"]
    assert p.numerics.time.t_end == cfg["time"]["t_end"]
    assert p.numerics.time.n_steps == cfg["time"]["n_steps"]

    assert p.numerics.scheme_name == cfg["solver"]["scheme_name"]
    assert p.numerics.matrix_storage == cfg["solver"]["matrix_storage"]
    assert p.numerics.linear_solver == cfg["solver"]["linear_solver"]
    assert p.numerics.epsilon_zero_mass == cfg["solver"]["epsilon_zero_mass"]
    assert p.numerics.positivity_tolerance == (
        cfg["solver"]["positivity_tolerance"]
    )


def test_baseline_context_uses_config_values():
    c = build_context()
    cfg = BASELINE_CONFIG

    assert c.name == f"{cfg['name']}_context"
    assert c.initial_age == cfg["ages"]["initial_age"]
    assert c.final_age == cfg["ages"]["final_age"]

    assert c.output.observation_ages == cfg["output"]["observation_ages"]
    assert c.output.save_full_trajectory == (
        cfg["output"]["save_full_trajectory"]
    )
    assert c.output.compute_time_series == cfg["output"]["compute_time_series"]
    assert c.output.save_figures == cfg["output"]["save_figures"]
    assert c.output.save_tables == cfg["output"]["save_tables"]


def test_baseline_config_builds_initial_state():
    x0 = build_initial_condition()
    p = build_parameters()
    c = build_context()

    state0 = build_initial_state(x0, p, c)

    assert state0.time == 0.0
    assert state0.age == BASELINE_CONFIG["ages"]["initial_age"]
    assert state0.step_index == 0
    assert state0.U.shape == (
        BASELINE_CONFIG["grid"]["nx"],
        BASELINE_CONFIG["grid"]["ny"],
    )


def test_baseline_configured_simulation_runs_short():
    x0 = build_initial_condition()
    p = build_parameters()
    c = build_context()

    results = simulate(
        x0,
        p,
        c,
        max_steps=2,
    )

    assert results.final_state.step_index == 2
    assert results.metadata["solver"] == "sparse_legacy"
    assert results.metadata["matrix_storage"] == "sparse"
    assert results.metadata["solver_requested"] is None

def test_copy_baseline_config_returns_independent_copy():
    config = copy_baseline_config()

    config["grid"]["nx"] = 10
    config["output"]["observation_ages"].append(999.0)

    assert BASELINE_CONFIG["grid"]["nx"] == 20
    assert BASELINE_CONFIG["output"]["observation_ages"] == [18.0, 45.0, 69.0]

    assert config["grid"]["nx"] == 10
    assert config["output"]["observation_ages"] == [18.0, 45.0, 69.0, 999.0]


def test_baseline_builders_accept_custom_config():
    config = copy_baseline_config()

    config["name"] = "baseline_custom_test"
    config["grid"]["nx"] = 10
    config["grid"]["ny"] = 12
    config["time"]["n_steps"] = 5
    config["output"]["observation_ages"] = [18.0, 20.0]

    x0 = build_initial_condition(config)
    p = build_parameters(config)
    c = build_context(config)

    assert x0.name == config["initial_condition"]["name"]
    assert p.name == "baseline_custom_test"
    assert p.numerics.grid.nx == 10
    assert p.numerics.grid.ny == 12
    assert p.numerics.time.n_steps == 5
    assert c.name == "baseline_custom_test_context"
    assert c.output.observation_ages == [18.0, 20.0]

def test_custom_config_simulation_runs_short():
    config = copy_baseline_config()

    config["name"] = "baseline_custom_short_test"
    config["grid"]["nx"] = 10
    config["grid"]["ny"] = 10
    config["time"]["n_steps"] = 5
    config["time"]["t_end"] = 1.0
    config["ages"]["final_age"] = 19.0
    config["output"]["observation_ages"] = [18.0, 19.0]

    x0 = build_initial_condition(config)
    p = build_parameters(config)
    c = build_context(config)

    results = simulate(
        x0,
        p,
        c,
        max_steps=2,
    )

    assert results.final_state.step_index == 2
    assert results.metadata["solver"] == "sparse_legacy"
    assert results.metadata["matrix_storage"] == "sparse"

def test_run_baseline_apply_cli_overrides():
    config = copy_baseline_config()

    args = Namespace(
        nx=11,
        ny=13,
        n_steps=17,
        t_end=8.0,
        initial_age=None,
        final_age=None,
        observation_ages=[18.0, 22.0, 26.0],
    )

    updated = apply_cli_overrides(config, args)

    assert updated["grid"]["nx"] == 11
    assert updated["grid"]["ny"] == 13
    assert updated["time"]["n_steps"] == 17
    assert updated["time"]["t_end"] == 8.0
    assert updated["ages"]["initial_age"] == 18.0
    assert updated["ages"]["final_age"] == 26.0
    assert updated["output"]["observation_ages"] == [18.0, 22.0, 26.0]