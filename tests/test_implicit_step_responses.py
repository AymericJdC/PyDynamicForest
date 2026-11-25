import csv
import json

import numpy as np
import pytest

from pydynamicforest.initial_conditions import build_initial_state
from simulations.article_submission_legacy.config import make_short_debug_config
from simulations.article_submission_legacy.context import build_context
from simulations.article_submission_legacy.diagnose_implicit_step_responses import (
    CSV_FIELDS,
    EXPERIMENTS,
    RESIDUAL_FIELDS,
    build_one_step_experiments,
    diagnose_state_responses,
    response_residuals,
    summarize_state,
    write_outputs,
)
from simulations.article_submission_legacy.initial_condition import build_initial_condition
from simulations.article_submission_legacy.parameters import build_parameters


def _state_and_parameters():
    config = make_short_debug_config()
    config["grid"].update({"nx": 7, "ny": 6})
    x0 = build_initial_condition(config)
    p = build_parameters(config)
    c = build_context(config)
    return build_initial_state(x0, p, c), p


def test_builds_complete_ordered_experiment_set_and_identity():
    state, p = _state_and_parameters()
    experiments = build_one_step_experiments(state, p)

    assert tuple(experiments) == EXPERIMENTS
    np.testing.assert_array_equal(experiments["identity"], state.U)
    for U_next in experiments.values():
        assert U_next.shape == state.U.shape
        assert np.all(np.isfinite(U_next))


def test_full_diagnostic_step_matches_patrimonial_solver():
    state, p = _state_and_parameters()
    _, regression = diagnose_state_responses(state, p=p, target_age=18)

    assert regression["max_abs_U_difference"] == pytest.approx(0.0)
    assert regression["l2_U_difference"] == pytest.approx(0.0)


def test_identity_rates_are_zero_and_mortality_reduces_density():
    state, p = _state_and_parameters()
    rows, _ = diagnose_state_responses(state, p=p, target_age=18)
    by_name = {row["experiment"]: row for row in rows}

    for field, value in by_name["identity"].items():
        if field.startswith("d_") and field.endswith("_dt"):
            assert value == pytest.approx(0.0)
    assert by_name["mortality_only"]["d_stand_density_dt"] < 0.0


def test_diffusion_and_mortality_matrix_responses_are_reported_as_nonadditive():
    state, p = _state_and_parameters()
    rows, _ = diagnose_state_responses(state, p=p, target_age=18)
    residuals = response_residuals(rows)

    assert [row["residual_type"] for row in residuals] == [
        "implicit_nonadditivity",
        "full_minus_transport_minus_implicit",
    ]
    for row in residuals:
        for field in RESIDUAL_FIELDS[2:]:
            assert np.isfinite(row[field])


def test_summary_reports_second_moments_and_dominant_height():
    state, p = _state_and_parameters()
    summary = summarize_state(state.U, p)

    assert summary["stand_density"] > 0.0
    assert summary["height_variance_m2"] >= 0.0
    assert summary["dbh_variance_cm2"] >= 0.0
    assert summary["continuous_top_height_m"] >= summary["mean_height_m"]
    assert summary["continuous_H0_minus_Hm_m"] == pytest.approx(
        summary["continuous_top_height_m"] - summary["mean_height_m"]
    )


def test_writes_24_response_rows_and_six_residual_rows(tmp_path):
    state, p = _state_and_parameters()
    all_rows = []
    all_residuals = []
    regressions = []
    for age in (18, 45, 69):
        rows, regression = diagnose_state_responses(state, p=p, target_age=age)
        all_rows.extend(rows)
        all_residuals.extend(response_residuals(rows))
        regressions.append({"target_age": age, **regression})

    result = write_outputs(
        tmp_path, all_rows, all_residuals, regressions, "states"
    )

    with result["responses_csv"].open(newline="", encoding="utf-8") as stream:
        response_rows = list(csv.DictReader(stream))
    with result["residuals_csv"].open(newline="", encoding="utf-8") as stream:
        residual_rows = list(csv.DictReader(stream))
    payload = json.loads(result["json_path"].read_text(encoding="utf-8"))
    markdown = result["markdown_path"].read_text(encoding="utf-8")

    assert len(response_rows) == 24
    assert len(residual_rows) == 6
    assert list(response_rows[0]) == CSV_FIELDS
    assert list(residual_rows[0]) == RESIDUAL_FIELDS
    assert payload["experiments"] == list(EXPERIMENTS)
    assert "counterfactual" in payload["interpretation_warning"]
    assert "dVar(H)/dt" in markdown
