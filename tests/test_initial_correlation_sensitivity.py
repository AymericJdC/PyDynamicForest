import csv
import json

import numpy as np
import pytest

from simulations.article_submission_legacy.initial_correlation_sensitivity import (
    CSV_FIELDS,
    build_correlated_initial_density,
    evaluate_rho,
    evaluate_rhos,
    interpolate_target_rho,
    run_sensitivity,
)
from simulations.article_submission_legacy.parameters import build_parameters


def test_zero_correlation_reproduces_patrimonial_initial_moments():
    row = evaluate_rho(0.0)

    assert row["stand_density"] == pytest.approx(1924.34, rel=1.0e-10)
    assert row["mean_dbh_cm"] == pytest.approx(11.690043, abs=1.0e-5)
    assert row["quadratic_mean_dbh_cm"] == pytest.approx(11.954356, abs=1.0e-5)
    assert row["mean_height"] == pytest.approx(9.61, abs=1.0e-6)
    assert row["continuous_top_height"] == pytest.approx(9.61, abs=1.0e-6)
    assert abs(row["height_dbh_correlation_effective"]) < 1.0e-12


def test_positive_correlation_increases_dominant_height_and_effective_correlation():
    rows = evaluate_rhos((0.0, 0.25, 0.50, 0.75))

    effective = [row["height_dbh_correlation_effective"] for row in rows]
    top_heights = [row["continuous_top_height"] for row in rows]

    assert effective == sorted(effective)
    assert top_heights == sorted(top_heights)
    assert top_heights[-1] > top_heights[0] + 1.0
    for row in rows:
        assert row["continuous_selected_stems"] == pytest.approx(100.0, abs=1.0e-9)
        assert row["stand_density"] == pytest.approx(1924.34, rel=1.0e-10)


def test_density_validation_and_target_interpolation():
    p = build_parameters()
    with pytest.raises(ValueError, match="strictly between -1 and 1"):
        build_correlated_initial_density(1.0, p)

    rows = evaluate_rhos((0.0, 0.25, 0.50, 0.75, 0.90))
    target = interpolate_target_rho(rows)
    assert target is not None
    assert 0.0 < target["rho_requested_interpolated"] < 0.90
    assert len(target["bracket"]) == 2


def test_sensitivity_writes_complete_outputs(tmp_path):
    result = run_sensitivity(tmp_path, rhos=(0.0, 0.5, 0.9))

    with result["csv_path"].open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    payload = json.loads(result["json_path"].read_text(encoding="utf-8"))
    markdown = result["markdown_path"].read_text(encoding="utf-8")

    assert len(rows) == 3
    assert list(rows[0]) == CSV_FIELDS
    assert payload["scenario_status"].startswith("separate sensitivity experiment")
    assert "not a statistical estimate" in payload["identifiability_warning"]
    assert "rho effective" in markdown
    assert "Dm" in markdown and "Dg" in markdown and "sigma_D" in markdown
