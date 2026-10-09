import csv
import json

import pytest

from simulations.article_submission_legacy.diagnose_initial_condition import (
    SUMMARY_FIELDS,
    diagnose_initial_condition,
    run_diagnostic,
)


def test_initial_diagnostic_distinguishes_Dm_Dg_and_spread():
    result = diagnose_initial_condition()

    assert result["stand_density"] == pytest.approx(result["observed_N"], abs=0.01)
    assert result["basal_area"] == pytest.approx(result["observed_G"], abs=0.02)
    assert result["mean_dbh_cm"] == pytest.approx(result["observed_mean_dbh_cm"], abs=0.01)
    assert result["quadratic_mean_dbh_cm"] == pytest.approx(
        result["observed_quadratic_mean_dbh_cm"], abs=0.01
    )
    assert result["dbh_standard_deviation_cm"] == pytest.approx(
        result["observed_implied_dbh_standard_deviation_cm"], abs=0.02
    )
    assert result["quadratic_mean_dbh_cm"] > result["mean_dbh_cm"]


def test_initial_joint_structure_and_algebraic_identities_are_consistent():
    result = diagnose_initial_condition()

    assert result["mean_height"] == pytest.approx(result["observed_Hm"], abs=0.001)
    assert result["continuous_top_height"] == pytest.approx(
        result["mean_height"], abs=1.0e-8
    )
    assert result["observed_H0_minus_Hm"] == pytest.approx(2.04938237)
    assert result["continuous_H0_minus_Hm"] == pytest.approx(0.0, abs=1.0e-8)
    assert abs(result["height_dbh_covariance_m2"]) < 1.0e-12
    assert abs(result["height_dbh_correlation"]) < 1.0e-12
    assert abs(result["quadratic_identity_residual_cm2"]) < 1.0e-10
    assert abs(result["basal_area_identity_residual"]) < 1.0e-12
    assert result["continuous_selected_stems"] == pytest.approx(100.0, abs=1.0e-9)


def test_initial_diagnostic_writes_revised_outputs(tmp_path):
    result = run_diagnostic(tmp_path)

    with result["csv_path"].open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    payload = json.loads(result["json_path"].read_text(encoding="utf-8"))
    markdown = result["markdown_path"].read_text(encoding="utf-8")

    assert len(rows) == 1
    assert list(rows[0]) == SUMMARY_FIELDS
    assert payload["interpretation"]["scenario_status"] == (
        "patrimonial initial condition unchanged"
    )
    assert payload["interpretation"]["observables_present"] == [
        "N", "G", "Dm", "Dg", "sigma_D", "Hm", "H0"
    ]
    assert "| Dm (cm) |" in markdown
    assert "| Dg (cm) |" in markdown
    assert "closely reproduces N, G, Dm, derived Dg" in markdown
    assert "do not identify a unique joint distribution" in markdown
