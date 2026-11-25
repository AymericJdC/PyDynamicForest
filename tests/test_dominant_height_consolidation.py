import csv
import json

import pytest

from simulations.dominant_height_sensitivity.consolidate import (
    convergence_summary,
    fine_grid_sequence,
    run_consolidation,
)


def test_fine_grid_sequence_records_successive_changes():
    rows = fine_grid_sequence(
        "regular_height_dbh",
        ny_values=(80, 160, 320),
    )

    assert [row["ny"] for row in rows] == [80, 160, 320]
    assert rows[0]["change_from_previous"] is None
    assert rows[1]["absolute_change_from_previous"] >= 0.0
    assert rows[2]["absolute_change_from_previous"] >= 0.0


def test_convergence_summary_uses_finest_successive_change():
    rows = [
        {"ny": 10, "proportional_top_height": 1.0, "absolute_change_from_previous": None},
        {"ny": 20, "proportional_top_height": 1.2, "absolute_change_from_previous": 0.2},
        {"ny": 40, "proportional_top_height": 1.25, "absolute_change_from_previous": 0.05},
    ]
    summary = convergence_summary(rows)

    assert summary["finest_value"] == pytest.approx(1.25)
    assert summary["finest_successive_change"] == pytest.approx(0.05)
    assert summary["successive_change_ratios"] == pytest.approx([4.0])


def test_consolidation_writes_documented_outputs(tmp_path):
    result = run_consolidation(tmp_path)

    assert result["csv_path"].is_file()
    assert result["json_path"].is_file()
    assert result["markdown_path"].is_file()

    with result["csv_path"].open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    payload = json.loads(result["json_path"].read_text(encoding="utf-8"))
    markdown = result["markdown_path"].read_text(encoding="utf-8")

    assert len(rows) == 6
    assert payload["reference_ny_values"] == [640, 1280, 2560]
    assert "not an analytical value" in " ".join(payload["interpretation_limits"])
    assert "preferred numerical candidate" in markdown
    assert "top_height" in markdown
