import csv
import json

import numpy as np
import pytest

from pydynamicforest.initial_conditions import build_initial_state
from pydynamicforest.solver import advance_one_step_sparse_legacy, evaluate_model_fields_for_solver
from simulations.article_submission_legacy.compare_height_growth_profiles import (
    BETAS,
    COMPARISON_FIELDS,
    TRAJECTORY_FIELDS,
    advance_one_step_height_profile,
    build_comparison,
    height_profile_multiplier,
    modify_height_growth,
    nearest_age_rows,
    patrimonial_regression,
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
    return build_initial_state(build_initial_condition(config), p, c), p


def test_profile_multipliers_preserve_beta_one_and_upper_boundary():
    _, p = _state_parameters()
    np.testing.assert_array_equal(height_profile_multiplier(p, 1.0), np.ones(p.numerics.grid.nx))
    for beta in BETAS[1:]:
        multiplier = height_profile_multiplier(p, beta)
        assert np.all((multiplier >= 0.0) & (multiplier <= 1.0))
        assert multiplier[0] == pytest.approx(1.0)
        assert multiplier[-1] == pytest.approx(0.0)
    with pytest.raises(ValueError, match="strictly positive"):
        height_profile_multiplier(p, 0.0)


def test_only_height_growth_field_is_modified():
    state, p = _state_parameters()
    fields = evaluate_model_fields_for_solver(state, p)
    modified = modify_height_growth(fields, p, 1.5)
    assert set(modified) == set(fields)
    for name in fields:
        if name == "height_growth":
            assert not np.array_equal(modified[name], fields[name])
        else:
            np.testing.assert_array_equal(modified[name], fields[name])


def test_beta_one_step_matches_patrimonial_solver():
    state, p = _state_parameters()
    custom = advance_one_step_height_profile(state, p, 1.0)
    patrimonial = advance_one_step_sparse_legacy(state, p)
    np.testing.assert_array_equal(custom.U, patrimonial.U)
    assert custom.age == patrimonial.age
    assert patrimonial_regression(p, build_context(make_short_debug_config()))["max_abs_U_difference"] == pytest.approx(0.0)


def test_nearest_ages_and_comparison_deltas():
    base = [{"age": 18.0, "stand_density": 1.0, "basal_area_m2_ha": 2.0, "mean_height_m": 3.0, "continuous_top_height_m": 4.0, "H0_minus_Hm_m": 1.0, "height_sd_m": 0.5, "mean_dbh_cm": 10.0, "quadratic_mean_dbh_cm": 11.0, "dbh_sd_cm": 2.0, "height_dbh_correlation": 0.2}, {"age": 45.0, "stand_density": 1.0, "basal_area_m2_ha": 2.0, "mean_height_m": 3.0, "continuous_top_height_m": 4.0, "H0_minus_Hm_m": 1.0, "height_sd_m": 0.5, "mean_dbh_cm": 10.0, "quadratic_mean_dbh_cm": 11.0, "dbh_sd_cm": 2.0, "height_dbh_correlation": 0.2}, {"age": 69.0, "stand_density": 1.0, "basal_area_m2_ha": 2.0, "mean_height_m": 3.0, "continuous_top_height_m": 4.0, "H0_minus_Hm_m": 1.0, "height_sd_m": 0.5, "mean_dbh_cm": 10.0, "quadratic_mean_dbh_cm": 11.0, "dbh_sd_cm": 2.0, "height_dbh_correlation": 0.2}]
    alt = [{**row, "mean_height_m": 4.0} for row in base]
    selected = nearest_age_rows(base)
    assert [row["age"] for row in selected] == [18.0, 45.0, 69.0]
    comparison = build_comparison({1.0: base, 1.25: alt})
    alternative = [row for row in comparison if row["beta"] == 1.25]
    assert all(row["delta_mean_height_m"] == pytest.approx(1.0) for row in alternative)


def test_outputs_have_expected_structure(tmp_path):
    row = {field: 0.0 for field in TRAJECTORY_FIELDS}
    trajectories = {beta: [{**row, "beta": beta}] for beta in BETAS}
    comparison_row = {field: 0.0 for field in COMPARISON_FIELDS}
    comparison = [{**comparison_row, "beta": beta} for beta in BETAS]
    regression = {"max_abs_U_difference": 0.0, "l2_U_difference": 0.0}
    files = write_outputs(tmp_path, trajectories, comparison, regression)
    with files["trajectory_csv"].open(newline="", encoding="utf-8") as stream:
        trajectory_rows = list(csv.DictReader(stream))
    with files["comparison_csv"].open(newline="", encoding="utf-8") as stream:
        comparison_rows = list(csv.DictReader(stream))
    payload = json.loads(files["json"].read_text(encoding="utf-8"))
    assert len(trajectory_rows) == 3 and list(trajectory_rows[0]) == TRAJECTORY_FIELDS
    assert len(comparison_rows) == 3 and list(comparison_rows[0]) == COMPARISON_FIELDS
    assert payload["betas"] == list(BETAS)


def test_short_complete_trajectory_reaches_context_final_age():
    from simulations.article_submission_legacy.compare_height_growth_profiles import (
        run_trajectory,
    )

    config = make_short_debug_config()
    p = build_parameters(config)
    context = build_context(config)

    rows, states = run_trajectory(
        beta=1.0,
        p=p,
        context=context,
    )

    expected_final_time = (
        context.final_age - context.initial_age
    )

    assert len(rows) == len(states)
    assert rows[0]["time"] == pytest.approx(0.0)
    assert rows[0]["age"] == pytest.approx(
        context.initial_age
    )

    assert rows[-1]["time"] == pytest.approx(
        expected_final_time
    )
    assert states[-1].time == pytest.approx(
        expected_final_time
    )

    assert rows[-1]["age"] == pytest.approx(
        context.final_age
    )
    assert states[-1].age == pytest.approx(
        context.final_age
    )

    assert all(
        later["time"] > earlier["time"]
        for earlier, later in zip(rows, rows[1:])
    )
