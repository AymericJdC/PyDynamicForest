import csv
import json
import numpy as np
import pytest

from pydynamicforest.initial_conditions import build_initial_state
from simulations.article_submission_legacy.config import make_short_debug_config
from simulations.article_submission_legacy.context import build_context
from simulations.article_submission_legacy.diagnose_status_weighted_velocities import (
    CLASS_FIELDS, GLOBAL_FIELDS, QUANTILE_FIELDS, STATUS_EDGES,
    diagnose_state, weighted_gini, weighted_quantile, write_outputs,
)
from simulations.article_submission_legacy.initial_condition import build_initial_condition
from simulations.article_submission_legacy.parameters import build_parameters


def _state_and_parameters():
    config = make_short_debug_config(); config["grid"].update({"nx": 7, "ny": 6})
    p = build_parameters(config); c = build_context(config)
    return build_initial_state(build_initial_condition(config), p, c), p


def test_weighted_quantiles_are_monotone_and_validate_inputs():
    q = weighted_quantile([3, 1, 2], [1, 2, 1], [0, .25, .5, .75, 1])
    assert np.all(np.diff(q) >= 0)
    assert q[0] == 1 and q[-1] == 3
    with pytest.raises(ValueError, match="identical"):
        weighted_quantile([1, 2], [1], [.5])
    with pytest.raises(ValueError, match="non-negative"):
        weighted_quantile([1, 2], [1, -1], [.5])


def test_weighted_gini_limits():
    assert weighted_gini([1, 1, 1], [1, 1, 1]) == pytest.approx(0.0)
    assert 0.0 < weighted_gini([0, 0, 1], [1, 1, 1]) < 1.0


def test_status_classes_reconstruct_population_and_weighted_shares():
    state, p = _state_and_parameters()
    classes, quantiles, global_row = diagnose_state(state, p, 18)
    assert len(classes) == len(STATUS_EDGES) - 1
    assert sum(row["stem_number"] for row in classes) == pytest.approx(global_row["stand_density"])
    assert sum(row["stem_fraction"] for row in classes) == pytest.approx(1.0)
    assert sum(row["height_velocity_share"] for row in classes) == pytest.approx(1.0)
    assert sum(row["mortality_share"] for row in classes) == pytest.approx(1.0)
    assert len(quantiles) == 5 * 7


def test_effective_fields_obey_status_modulation_bounds():
    state, p = _state_and_parameters()
    classes, _, global_row = diagnose_state(state, p, 18)
    assert 0.0 <= global_row["mean_status"] <= 1.0
    assert 0.0 <= global_row["near_zero_height_velocity_fraction"] <= 1.0
    assert 0.0 <= global_row["top_10_status_height_velocity_share"] <= 1.0
    assert 0.0 <= global_row["top_20_status_height_velocity_share"] <= 1.0
    assert global_row["top_20_status_height_velocity_share"] >= global_row["top_10_status_height_velocity_share"]
    assert 0.1 < global_row["mean_effective_height_velocity_m_year"] < 1.0
    for row in classes:
        if row["stem_number"] > 0:
            assert row["mean_effective_height_velocity_m_year"] <= row["mean_height_reference_velocity_m_year"] + 1e-15
            assert 0.0 <= row["status_modulation_ratio"] <= 1.0


def test_outputs_have_expected_shapes(tmp_path):
    state, p = _state_and_parameters()
    classes, quantiles, global_row = diagnose_state(state, p, 18)
    class_rows = classes * 3
    quantile_rows = quantiles * 3
    global_rows = [global_row] * 3
    files = write_outputs(tmp_path, class_rows, quantile_rows, global_rows, "states")
    with files["class_csv"].open(newline="", encoding="utf-8") as stream:
        saved_classes = list(csv.DictReader(stream))
    with files["quantile_csv"].open(newline="", encoding="utf-8") as stream:
        saved_quantiles = list(csv.DictReader(stream))
    with files["global_csv"].open(newline="", encoding="utf-8") as stream:
        saved_global = list(csv.DictReader(stream))
    payload = json.loads(files["json"].read_text(encoding="utf-8"))
    assert len(saved_classes) == 15 and list(saved_classes[0]) == CLASS_FIELDS
    assert len(saved_quantiles) == 105 and list(saved_quantiles[0]) == QUANTILE_FIELDS
    assert len(saved_global) == 3 and list(saved_global[0]) == GLOBAL_FIELDS
    assert payload["status_edges"] == STATUS_EDGES.tolist()
