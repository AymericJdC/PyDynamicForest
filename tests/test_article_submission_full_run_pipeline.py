import csv
import json

import numpy as np
import pytest

from simulations.article_submission_legacy.full_run import (
    CSV_FIELDS,
    legacy_threshold_details,
    run_article_submission_legacy,
)
from simulations.article_submission_legacy.parameters import build_parameters


def test_legacy_threshold_details_identifies_cut_dbh_class():
    p = build_parameters()
    grid = p.numerics.grid
    U = np.zeros((grid.nx, grid.ny), dtype=float)

    # Put 60 stems/ha in each of two tallest cells of the maximum DBH class.
    density_for_60_stems = 60.0 / (grid.dx * grid.dy)
    U[-1, -1] = density_for_60_stems
    U[-2, -1] = density_for_60_stems

    details = legacy_threshold_details(U, p)

    assert details["threshold_dbh_index"] == grid.ny - 1
    assert details["stems_strictly_above_threshold"] == pytest.approx(0.0)
    assert details["stems_in_threshold_class"] == pytest.approx(120.0)
    assert details["fraction_used_from_threshold_class"] == pytest.approx(100.0 / 120.0)


def test_short_full_run_pipeline_writes_reproducible_outputs(tmp_path):
    result = run_article_submission_legacy(
        output_dir=tmp_path,
        max_steps=2,
        progress=False,
    )

    csv_path = tmp_path / "time_series_legacy.csv"
    metadata_path = tmp_path / "metadata.json"
    config_path = tmp_path / "configuration.json"

    assert csv_path.is_file()
    assert metadata_path.is_file()
    assert config_path.is_file()
    assert (tmp_path / "state_age_18.npz").is_file()

    with csv_path.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))

    assert len(rows) == 3
    assert list(rows[0]) == CSV_FIELDS
    assert [int(row["step_index"]) for row in rows] == [0, 1, 2]
    assert all(row["legacy_top_height"] for row in rows)
    assert all(row["top_height_current"] for row in rows)

    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert metadata["n_steps_run"] == 2
    assert metadata["solver"] == "sparse legacy-equivalent"
    assert metadata["observation_files"]["18"] == "state_age_18.npz"

    saved = np.load(tmp_path / "state_age_18.npz")
    assert saved["U"].shape == (40, 40)
    assert float(saved["age"]) == pytest.approx(18.0)

    assert result["final_state"].step_index == 2
