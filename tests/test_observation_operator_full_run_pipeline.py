import csv
import json

import pytest

from simulations.article_submission_legacy.full_run import (
    CSV_FIELDS,
    run_article_submission_legacy,
)


EXPECTED_FIELDS = {
    "stand_density",
    "mean_height",
    "quadratic_mean_dbh_cm",
    "continuous_top_height",
    "continuous_threshold_dbh_cm",
    "continuous_selected_stems",
    "continuous_minus_proportional",
}


def test_full_run_declares_quadrature_consistent_observation_fields():
    assert EXPECTED_FIELDS.issubset(CSV_FIELDS)


def test_short_full_run_writes_consistent_continuous_diagnostics(tmp_path):
    run_article_submission_legacy(
        output_dir=tmp_path,
        max_steps=2,
        progress=False,
    )

    with (tmp_path / "time_series_legacy.csv").open(
        newline="", encoding="utf-8"
    ) as stream:
        rows = list(csv.DictReader(stream))

    assert len(rows) == 3
    for row in rows:
        assert float(row["stand_density"]) == pytest.approx(
            float(row["trapezoidal_mass"]), rel=1.0e-14, abs=1.0e-12
        )
        assert float(row["continuous_selected_stems"]) == pytest.approx(
            100.0, abs=1.0e-9
        )
        assert float(row["continuous_minus_proportional"]) == pytest.approx(
            float(row["continuous_top_height"])
            - float(row["proportional_top_height"])
        )
        assert float(row["mean_height"]) > 0.0
        assert float(row["quadratic_mean_dbh_cm"]) > 0.0
        assert float(row["continuous_threshold_dbh_cm"]) > 0.0


def test_full_run_metadata_documents_new_observation_conventions(tmp_path):
    run_article_submission_legacy(
        output_dir=tmp_path,
        max_steps=0,
        progress=False,
    )

    metadata = json.loads(
        (tmp_path / "metadata.json").read_text(encoding="utf-8")
    )
    conventions = metadata["diagnostic_conventions"]

    assert "continuous_top_height" in conventions
    assert "piecewise-linear" in conventions["continuous_top_height"]
    assert "stand_density_mean_height_quadratic_mean_dbh" in conventions
    assert "tensor-product trapezoidal" in conventions[
        "stand_density_mean_height_quadratic_mean_dbh"
    ]
