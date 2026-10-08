import csv
import json

import pytest

from simulations.article_submission_legacy.full_run import (
    CSV_FIELDS,
    run_article_submission_legacy,
)


EXPECTED_HEIGHT_FIELDS = {
    "top_height_current",
    "legacy_top_height",
    "proportional_top_height",
    "legacy_minus_proportional",
    "current_minus_proportional",
    "top_height_difference",
}


def test_comparison_pipeline_declares_all_height_fields():
    assert EXPECTED_HEIGHT_FIELDS.issubset(CSV_FIELDS)


def test_comparison_pipeline_writes_consistent_height_differences(tmp_path):
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
        current = float(row["top_height_current"])
        legacy = float(row["legacy_top_height"])
        proportional = float(row["proportional_top_height"])

        assert float(row["legacy_minus_proportional"]) == pytest.approx(
            legacy - proportional
        )
        assert float(row["current_minus_proportional"]) == pytest.approx(
            current - proportional
        )
        assert float(row["top_height_difference"]) == pytest.approx(
            legacy - current
        )


def test_comparison_pipeline_documents_proportional_convention(tmp_path):
    run_article_submission_legacy(
        output_dir=tmp_path,
        max_steps=0,
        progress=False,
    )

    metadata = json.loads(
        (tmp_path / "metadata.json").read_text(encoding="utf-8")
    )
    conventions = metadata["diagnostic_conventions"]

    assert "proportional_top_height" in conventions
    assert "uniform fraction" in conventions["proportional_top_height"]
