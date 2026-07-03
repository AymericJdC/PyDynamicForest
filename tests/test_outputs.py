from simulations.baseline.initial_condition import build_initial_condition
from simulations.baseline.parameters import build_parameters
from simulations.baseline.context import build_context

from pydynamicforest.solver import simulate
from pydynamicforest.outputs import save_simulation_results


def test_save_simulation_results_creates_expected_files(tmp_path):
    x0 = build_initial_condition()
    p = build_parameters()
    c = build_context()

    results = simulate(x0, p, c, max_steps=2)

    files = save_simulation_results(results, tmp_path)

    assert "time_series" in files
    assert "metadata" in files
    assert "summary" in files

    for path in files.values():
        assert path.exists()
        assert path.is_file()

    time_series_content = files["time_series"].read_text(encoding="utf-8")
    metadata_content = files["metadata"].read_text(encoding="utf-8")
    summary_content = files["summary"].read_text(encoding="utf-8")

    assert "time,age,total_mass" in time_series_content
    assert "baseline_gaussian_initial_condition" in metadata_content
    assert "PyDynamicForest simulation summary" in summary_content

    assert "snapshots" in metadata_content.lower()
    assert "Snapshots" in summary_content