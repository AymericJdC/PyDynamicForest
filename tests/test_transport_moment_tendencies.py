import csv
import json

import numpy as np
import pytest

from pydynamicforest.initial_conditions import build_initial_state
from simulations.article_submission_legacy.config import make_short_debug_config
from simulations.article_submission_legacy.context import build_context
from simulations.article_submission_legacy.diagnose_transport_moment_tendencies import (
    CSV_FIELDS,
    component_additivity_residuals,
    diagnose_state_transport,
    mean_tendency_rates,
    signed_raw_moment_rates,
    write_outputs,
)
from simulations.article_submission_legacy.initial_condition import (
    build_initial_condition,
)
from simulations.article_submission_legacy.parameters import build_parameters


def _state_and_parameters(nx=7, ny=6):
    config = make_short_debug_config()
    config["grid"].update({"nx": nx, "ny": ny})
    x0 = build_initial_condition(config)
    p = build_parameters(config)
    c = build_context(config)
    return build_initial_state(x0, p, c), p


def test_signed_raw_moment_rates_accept_positive_and_negative_tendencies():
    _, p = _state_and_parameters(nx=3, ny=3)
    dot_U = np.array(
        [
            [-1.0, 0.0, 1.0],
            [-2.0, 0.0, 2.0],
            [-1.0, 0.0, 1.0],
        ]
    )

    rates = signed_raw_moment_rates(dot_U, p)

    assert rates["dN_dt_trees_ha_year"] == pytest.approx(0.0)
    assert rates["dMh_dt_m_trees_ha_year"] == pytest.approx(0.0)
    assert rates["dMd_dt_m_trees_ha_year"] > 0.0


def test_mean_tendency_uses_quotient_rule():
    state_summary = {
        "stand_density": 100.0,
        "mean_height": 10.0,
        "mean_dbh_m": 0.2,
    }
    raw = {
        "dN_dt_trees_ha_year": -5.0,
        "dMh_dt_m_trees_ha_year": -20.0,
        "dMd_dt_m_trees_ha_year": 1.0,
    }

    rates = mean_tendency_rates(state_summary, raw)

    assert rates["dHm_dt_m_year"] == pytest.approx(0.3)
    assert rates["dDm_dt_m_year"] == pytest.approx(0.02)
    assert rates["dDm_dt_cm_year"] == pytest.approx(2.0)


def test_directional_transport_rates_are_additive():
    state, p = _state_and_parameters()
    rows = diagnose_state_transport(state, p=p, target_age=18)
    residuals = component_additivity_residuals(rows)

    assert [row["component"] for row in rows] == [
        "height_transport",
        "dbh_transport",
        "total_transport",
    ]
    for residual in residuals.values():
        assert residual == pytest.approx(0.0, abs=1.0e-12)


def test_zero_density_rate_validation_rejects_wrong_shape_and_nonfinite_values():
    _, p = _state_and_parameters(nx=3, ny=4)

    with pytest.raises(ValueError, match="shape"):
        signed_raw_moment_rates(np.zeros((4, 3)), p)
    invalid = np.zeros((3, 4))
    invalid[0, 0] = np.nan
    with pytest.raises(ValueError, match="finite"):
        signed_raw_moment_rates(invalid, p)


def test_outputs_include_units_scope_rows_and_additivity(tmp_path):
    state, p = _state_and_parameters()
    rows = diagnose_state_transport(state, p=p, target_age=18)
    checks = [
        {
            "target_age": 18,
            "residuals": component_additivity_residuals(rows),
        }
    ]

    result = write_outputs(tmp_path, rows, checks, "saved_states")

    with result["csv_path"].open(newline="", encoding="utf-8") as stream:
        csv_rows = list(csv.DictReader(stream))
    payload = json.loads(result["json_path"].read_text(encoding="utf-8"))
    markdown = result["markdown_path"].read_text(encoding="utf-8")

    assert len(csv_rows) == 3
    assert list(csv_rows[0]) == CSV_FIELDS
    assert payload["scope"] == "explicit height and DBH transport only"
    assert payload["sign_convention"].startswith("dot_U = -transport")
    assert payload["units"]["dHm_dt_m_year"] == "m year-1"
    assert "height_transport" in markdown
    assert "Diffusion and mortality are excluded" in markdown
