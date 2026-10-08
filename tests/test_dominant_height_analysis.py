import csv
import json

import pytest

from simulations.article_submission_legacy.analyze_dominant_height import (
    analyze_csv,
    analyze_rows,
)


def synthetic_rows():
    return [
        {
            "step_index": 0,
            "age": 18.0,
            "threshold_dbh_index": 1,
            "fraction_used_from_threshold_class": 0.1,
            "legacy_top_height": 10.0,
            "top_height_current": 8.0,
            "proportional_top_height": 9.0,
        },
        {
            "step_index": 1,
            "age": 19.0,
            "threshold_dbh_index": 1,
            "fraction_used_from_threshold_class": 0.01,
            "legacy_top_height": 9.5,
            "top_height_current": 8.8,
            "proportional_top_height": 9.2,
        },
        {
            "step_index": 2,
            "age": 20.0,
            "threshold_dbh_index": 2,
            "fraction_used_from_threshold_class": 0.99,
            "legacy_top_height": 10.5,
            "top_height_current": 9.0,
            "proportional_top_height": 9.4,
        },
    ]


def test_analysis_computes_regularity_and_threshold_change():
    result = analyze_rows(synthetic_rows(), target_ages=(18.0, 20.0))

    assert result["n_rows"] == 3
    assert result["regularity"]["legacy"]["max_abs_delta"] == pytest.approx(1.0)
    assert result["regularity"]["proportional"]["max_abs_delta"] == pytest.approx(0.2)
    assert result["regularity"]["proportional"]["total_variation"] == pytest.approx(0.4)
    assert len(result["threshold_changes"]) == 1
    change = result["threshold_changes"][0]
    assert change["step_index"] == 2
    assert change["delta_proportional"] == pytest.approx(0.2)


def test_analysis_computes_pairwise_bounds_and_target_values():
    result = analyze_rows(synthetic_rows(), target_ages=(18.0, 20.0))

    legacy_prop = result["pairwise_differences"]["legacy_minus_proportional"]
    assert legacy_prop["minimum"] == pytest.approx(0.3)
    assert legacy_prop["maximum"] == pytest.approx(1.1)
    assert result["target_values"]["18"]["proportional"] == pytest.approx(9.0)
    assert result["target_values"]["20"]["legacy"] == pytest.approx(10.5)


def test_csv_loader_and_json_serialization(tmp_path):
    path = tmp_path / "comparison.csv"
    fieldnames = list(synthetic_rows()[0])
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(synthetic_rows())

    result = analyze_csv(path)
    rendered = json.dumps(result)

    assert result["n_rows"] == 3
    assert "proportional" in rendered
