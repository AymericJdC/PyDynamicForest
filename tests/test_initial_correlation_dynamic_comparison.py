import csv
import json
from pathlib import Path

import pytest

from simulations.article_submission_legacy.compare_initial_correlation_dynamics import (
    DEFAULT_RHO,
    compare_trajectories,
    run_correlated_trajectory,
)


def test_short_correlated_run_records_experiment_metadata(tmp_path):
    output_dir = tmp_path / "correlated"
    run_correlated_trajectory(
        output_dir=output_dir,
        rho=DEFAULT_RHO,
        max_steps=2,
        progress=False,
    )

    metadata = json.loads((output_dir / "metadata.json").read_text(encoding="utf-8"))
    rows = list(
        csv.DictReader(
            (output_dir / "time_series_legacy.csv").open(
                newline="", encoding="utf-8"
            )
        )
    )

    assert len(rows) == 3
    assert metadata["experiment"]["rho_requested"] == pytest.approx(DEFAULT_RHO)
    assert metadata["experiment"]["scenario_status"].startswith("experimental")
    assert float(rows[0]["continuous_top_height"]) > float(rows[0]["mean_height"]) + 2.0


def test_initial_state_patch_is_restored_after_run(tmp_path):
    from simulations.article_submission_legacy import full_run

    original = full_run.build_initial_state
    run_correlated_trajectory(tmp_path / "correlated", max_steps=0, progress=False)
    assert full_run.build_initial_state is original


def test_trajectory_comparison_aligns_and_computes_deltas(tmp_path):
    patrimonial = tmp_path / "patrimonial.csv"
    correlated = tmp_path / "correlated.csv"
    output = tmp_path / "comparison.csv"
    fields = [
        "step_index", "time", "age", "stand_density", "basal_area",
        "quadratic_mean_dbh_cm", "mean_height", "continuous_top_height",
        "continuous_threshold_dbh_cm",
    ]
    base_row = {
        "step_index": 0, "time": 0.0, "age": 18.0, "stand_density": 1000.0,
        "basal_area": 20.0, "quadratic_mean_dbh_cm": 12.0,
        "mean_height": 9.0, "continuous_top_height": 10.0,
        "continuous_threshold_dbh_cm": 16.0,
    }
    corr_row = dict(base_row)
    corr_row["mean_height"] = 9.1
    corr_row["continuous_top_height"] = 11.5

    for path, row in ((patrimonial, base_row), (correlated, corr_row)):
        with path.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            writer.writerow(row)

    compare_trajectories(patrimonial, correlated, output)
    result = next(csv.DictReader(output.open(newline="", encoding="utf-8")))

    assert float(result["delta_mean_height"]) == pytest.approx(0.1)
    assert float(result["delta_continuous_top_height"]) == pytest.approx(1.5)
    assert float(result["delta_H0_minus_Hm"]) == pytest.approx(1.4)


def test_trajectory_comparison_rejects_unaligned_lengths(tmp_path):
    fields = ["step_index", "time", "age", *(
        "stand_density", "basal_area", "quadratic_mean_dbh_cm", "mean_height",
        "continuous_top_height", "continuous_threshold_dbh_cm"
    )]
    paths = [tmp_path / "a.csv", tmp_path / "b.csv"]
    for index, path in enumerate(paths):
        with path.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            writer.writerow({field: 0 for field in fields})
            if index == 1:
                writer.writerow({field: 1 for field in fields})

    with pytest.raises(ValueError, match="different lengths"):
        compare_trajectories(paths[0], paths[1], tmp_path / "out.csv")
