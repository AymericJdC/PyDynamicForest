import csv
import json

import numpy as np
import pytest

from pydynamicforest.initial_conditions import build_initial_state
from pydynamicforest.numerics import compute_derived_quantities
from pydynamicforest.solver import (
    compute_transport_components_legacy,
    evaluate_model_fields_for_solver,
)
from simulations.article_submission_legacy.compare_vertical_status_modulations import (
    CSV_FIELDS,
    FORMULATIONS,
    build_responses,
    compute_modified_height_transport,
    diagnose_state,
    patrimonial_regression,
    transform_status,
    write_outputs,
)
from simulations.article_submission_legacy.config import make_short_debug_config
from simulations.article_submission_legacy.context import build_context
from simulations.article_submission_legacy.initial_condition import build_initial_condition
from simulations.article_submission_legacy.parameters import build_parameters


def _state_parameters():
    config = make_short_debug_config()
    config["grid"].update({"nx": 7, "ny": 6})
    p = build_parameters(config)
    c = build_context(config)
    state = build_initial_state(build_initial_condition(config), p, c)
    return state, p


def test_status_formulations_are_bounded_monotone_and_linear_is_identity():
    status = np.linspace(0.0, 1.0, 101)
    np.testing.assert_array_equal(transform_status(status, "linear"), status)
    for formulation in FORMULATIONS:
        values = transform_status(status, formulation)
        assert np.all((values >= 0.0) & (values <= 1.0))
        assert np.all(np.diff(values) >= 0.0)
    with pytest.raises(ValueError, match="Unknown"):
        transform_status(status, "invalid")


def test_linear_height_transport_matches_patrimonial_component():
    state, p = _state_parameters()
    derived = compute_derived_quantities(state, p)
    fields = evaluate_model_fields_for_solver(state, p)
    modified = compute_modified_height_transport(state, p, derived, fields, "linear")
    patrimonial = compute_transport_components_legacy(state, p, derived, fields)["height"]
    np.testing.assert_allclose(modified, patrimonial, rtol=0.0, atol=1.0e-15)


def test_linear_full_step_matches_patrimonial_solver():
    state, p = _state_parameters()
    regression = patrimonial_regression(state, p)
    assert regression["max_abs_U_difference"] == pytest.approx(0.0)
    assert regression["l2_U_difference"] == pytest.approx(0.0)


def test_builds_eight_finite_responses_and_alternatives_raise_mean_height():
    state, p = _state_parameters()
    rows = diagnose_state(state, p, 18)
    assert len(rows) == 8
    assert {(row["formulation"], row["response_type"]) for row in rows} == {
        (formulation, response)
        for formulation in FORMULATIONS
        for response in ("transport_only", "full_step")
    }
    for row in rows:
        assert all(np.isfinite(value) for value in row.values() if isinstance(value, float))
    full = {row["formulation"]: row for row in rows if row["response_type"] == "full_step"}
    assert full["sqrt"]["d_mean_height_m_dt"] > full["linear"]["d_mean_height_m_dt"]
    assert full["floor_0p1_sqrt"]["d_mean_height_m_dt"] > full["linear"]["d_mean_height_m_dt"]


def test_outputs_have_24_rows_for_three_ages(tmp_path):
    state, p = _state_parameters()
    rows = []
    regressions = []
    for age in (18, 45, 69):
        rows.extend(diagnose_state(state, p, age))
        regressions.append({"target_age": age, **patrimonial_regression(state, p)})
    files = write_outputs(tmp_path, rows, regressions, "states")
    with files["csv"].open(newline="", encoding="utf-8") as stream:
        saved = list(csv.DictReader(stream))
    payload = json.loads(files["json"].read_text(encoding="utf-8"))
    markdown = files["markdown"].read_text(encoding="utf-8")
    assert len(saved) == 24
    assert list(saved[0]) == CSV_FIELDS
    assert payload["formulations"] == list(FORMULATIONS)
    assert "dVar(H)/dt" in markdown
