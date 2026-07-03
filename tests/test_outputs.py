import numpy as np

from simulations.baseline.initial_condition import build_initial_condition
from simulations.baseline.parameters import build_parameters
from simulations.baseline.context import build_context

from pydynamicforest.solver import simulate
from pydynamicforest.outputs import save_simulation_results


def test_save_simulation_results_creates_expected_files(tmp_path):
    x0 = build_initial_condition()
    p = build_parameters()
    c = build_context()

    results = simulate(
        x0,
        p,
        c,
        max_steps=2,
        solver_name="sparse",
    )

    files = save_simulation_results(results, tmp_path)

    assert "time_series" in files
    assert "metadata" in files
    assert "summary" in files
    assert "observations" in files

    assert files["time_series"].exists()
    assert files["time_series"].is_file()

    assert files["metadata"].exists()
    assert files["metadata"].is_file()

    assert files["summary"].exists()
    assert files["summary"].is_file()

    assert isinstance(files["observations"], list)

    time_series_content = files["time_series"].read_text(encoding="utf-8")
    metadata_content = files["metadata"].read_text(encoding="utf-8")
    summary_content = files["summary"].read_text(encoding="utf-8")

    assert "time,age,total_mass,legacy_mass" in time_series_content
    assert "baseline_gaussian_initial_condition" in metadata_content
    assert "PyDynamicForest simulation summary" in summary_content

    assert "observations" in metadata_content.lower()
    assert "Observations" in summary_content


def test_save_simulation_results_exports_observations_npz(tmp_path):
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

    assert isinstance(observation_files, list)
    assert len(observation_files) == len(results.observations)

    observations_dir = tmp_path / "observations"

    assert observations_dir.exists()
    assert observations_dir.is_dir()

    for file_path, observation in zip(observation_files, results.observations):
        assert file_path.exists()
        assert file_path.is_file()
        assert file_path.suffix == ".npz"

        data = np.load(file_path)

        assert "U" in data
        assert "time" in data
        assert "age" in data
        assert "step_index" in data
        assert "height_grid" in data
        assert "dbh_grid" in data

        assert data["U"].shape == observation.U.shape
        assert np.isclose(float(data["time"]), observation.time)
        assert np.isclose(float(data["age"]), observation.age)
        assert int(data["step_index"]) == observation.step_index