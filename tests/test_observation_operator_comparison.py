import csv
import json

import numpy as np
import pytest

from simulations.article_submission_legacy.compare_observation_operators import (
    CSV_FIELDS,
    compare_saved_states,
    compare_state,
)
from pydynamicforest.initial_conditions import build_initial_state
from simulations.article_submission_legacy.context import build_context
from simulations.article_submission_legacy.initial_condition import build_initial_condition
from simulations.article_submission_legacy.parameters import build_parameters


def test_initial_state_comparison_is_algebraically_consistent():
    x0 = build_initial_condition()
    p = build_parameters()
    c = build_context()
    state0 = build_initial_state(x0, p, c)

    row = compare_state(
        state0.U,
        p,
        target_age=18,
        actual_age=state0.age,
        step_index=state0.step_index,
    )

    assert row["target_age"] == 18
    assert row["stand_density"] == pytest.approx(1924.34, rel=1.0e-10)
    assert row["mean_height"] == pytest.approx(9.61, abs=1.0e-6)
    assert abs(row["basal_area_identity_residual"]) < 1.0e-12
    assert row["continuous_selected_stems"] == pytest.approx(100.0, abs=1.0e-9)
    assert 0.0 < row["continuous_threshold_dbh_cm"] < 100.0
    assert row["current_top_height"] < row["continuous_top_height"] < row["legacy_top_height"]


def test_saved_state_workflow_writes_complete_outputs(tmp_path):
    x0 = build_initial_condition()
    p = build_parameters()
    c = build_context()
    state0 = build_initial_state(x0, p, c)
    U = state0.U
    input_dir = tmp_path / "states"
    output_dir = tmp_path / "comparison"
    input_dir.mkdir()

    for target_age, filename, actual_age, step in (
        (18, "state_age_18.npz", 18.0, 0),
        (45, "state_age_44p9994.npz", 44.9994, 5294),
        (69, "state_age_69.npz", 69.0, 10000),
    ):
        np.savez_compressed(
            input_dir / filename,
            U=U,
            age=np.array(actual_age),
            step_index=np.array(step),
        )

    result = compare_saved_states(input_dir, output_dir)

    assert result["csv_path"].is_file()
    assert result["json_path"].is_file()
    with result["csv_path"].open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    payload = json.loads(result["json_path"].read_text(encoding="utf-8"))

    assert len(rows) == 3
    assert list(rows[0]) == CSV_FIELDS
    assert [int(row["target_age"]) for row in rows] == [18, 45, 69]
    assert len(payload["rows"]) == 3
    assert "piecewise-linear" in payload["continuous_top_height"]


def test_missing_saved_state_is_reported(tmp_path):
    with pytest.raises(FileNotFoundError, match="Required saved state"):
        compare_saved_states(tmp_path, tmp_path / "output")
