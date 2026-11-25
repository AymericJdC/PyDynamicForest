import csv
import json

import numpy as np
import pytest

from simulations.article.q9d_full_run import run_q9d_scenario
from simulations.article.scenarios import make_q9d_scenario


def _write_initial_archive(root, age, rho, density):
    directory = root / f"age{age}"
    directory.mkdir(parents=True)
    np.savez_compressed(
        directory / "compatible_initial_states.npz",
        **{f"rho_{rho:.2f}": density},
    )


def test_zero_step_q9d_run_uses_precomputed_state_and_isolated_outputs(tmp_path):
    q9c_root = tmp_path / "q9c"
    output_root = tmp_path / "scenarios"
    density = np.ones((40, 40), dtype=float)
    _write_initial_archive(q9c_root, 45, 0.85, density)
    scenario = make_q9d_scenario(
        domain="main_age45",
        requested_rho=0.85,
        q9c_root=q9c_root,
    )
    result = run_q9d_scenario(
        scenario,
        output_root=output_root,
        max_steps=0,
        progress=False,
    )
    scenario_dir = output_root / "main_age45" / "rho_0.85"
    assert result["final_state"].age == pytest.approx(45.0)
    assert np.array_equal(result["final_state"].U, density)
    assert (scenario_dir / "state_age_45.npz").is_file()
    metadata = json.loads((scenario_dir / "metadata.json").read_text())
    assert metadata["steps_run"] == 0
    assert metadata["dynamic_parameters_recalibrated"] is False
    assert metadata["saved_observation_ages"] == [45.0]
    with (scenario_dir / "observations_simulation.csv").open(
        newline="", encoding="utf-8"
    ) as stream:
        rows = list(csv.DictReader(stream))
    assert {float(row["requested_age"]) for row in rows} == {45.0}


def test_nonempty_output_directory_is_not_overwritten(tmp_path):
    q9c_root = tmp_path / "q9c"
    output_root = tmp_path / "scenarios"
    _write_initial_archive(q9c_root, 38, 0.50, np.ones((40, 40)))
    scenario = make_q9d_scenario(
        domain="transition_age38",
        requested_rho=0.50,
        q9c_root=q9c_root,
    )
    target = output_root / scenario.output_relative_path
    target.mkdir(parents=True)
    (target / "sentinel.txt").write_text("keep", encoding="utf-8")
    with pytest.raises(FileExistsError, match="Refusing to overwrite"):
        run_q9d_scenario(
            scenario,
            output_root=output_root,
            max_steps=0,
            progress=False,
        )
