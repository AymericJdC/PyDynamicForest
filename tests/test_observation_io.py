# SPDX-License-Identifier: LGPL-3.0-or-later
import numpy as np

from simulations.baseline.initial_condition import build_initial_condition
from simulations.baseline.parameters import build_parameters
from simulations.baseline.context import build_context

from pydynamicforest.solver import simulate
from pydynamicforest.io import (
    save_simulation_results,
    load_observation_npz,
    load_observations_npz_dir,
)


def test_load_observation_npz(tmp_path):
    x0 = build_initial_condition()
    p = build_parameters()
    c = build_context()

    results = simulate(
        x0,
        p,
        c,
        max_steps=10,
        solver_name="sparse",
    )

    files = save_simulation_results(results, tmp_path)
    observation_files = files["observations"]

    assert len(observation_files) > 0

    loaded = load_observation_npz(observation_files[0])
    original = results.observations[0]

    assert np.allclose(loaded["U"], original.U)
    assert np.isclose(loaded["time"], original.time)
    assert np.isclose(loaded["age"], original.age)
    assert loaded["step_index"] == original.step_index

    assert "height_grid" in loaded
    assert "dbh_grid" in loaded
    assert "height_grid_physical" in loaded
    assert "dbh_grid_physical" in loaded

    assert loaded["height_grid"].shape == loaded["height_grid_physical"].shape
    assert loaded["dbh_grid"].shape == loaded["dbh_grid_physical"].shape


def test_load_observations_npz_dir(tmp_path):
    x0 = build_initial_condition()
    p = build_parameters()
    c = build_context()

    results = simulate(
        x0,
        p,
        c,
        max_steps=10,
        solver_name="sparse",
    )

    save_simulation_results(results, tmp_path)

    loaded_observations = load_observations_npz_dir(tmp_path)

    assert len(loaded_observations) == len(results.observations)

    loaded_steps = [
        observation["step_index"]
        for observation in loaded_observations
    ]

    expected_steps = [
        observation.step_index
        for observation in results.observations
    ]

    assert loaded_steps == expected_steps

    loaded_ages = [
        observation["age"]
        for observation in loaded_observations
    ]

    expected_ages = [
        observation.age
        for observation in results.observations
    ]

    assert np.allclose(loaded_ages, expected_ages)