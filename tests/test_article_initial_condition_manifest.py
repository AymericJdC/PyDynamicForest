import csv
import json

import pytest

from simulations.article.initial_condition_manifest import (
    DENSITY_FIELDS,
    SUMMARY_FIELDS,
    build_manifest,
    write_manifest,
)


def test_manifest_records_audited_construction_and_observables():
    manifest, rows, density_rows = build_manifest()
    initial = manifest["initial_condition"]
    assert initial["requested_height_dbh_correlation"] == pytest.approx(0.8490113967)
    assert initial["effective_height_dbh_correlation"] == pytest.approx(0.857094656455, abs=1.0e-9)
    by_name = {row["observable"]: row for row in rows}
    assert by_name["N"]["simulated_value"] == pytest.approx(1924.34, abs=1.0e-9)
    assert by_name["H0_continuous"]["simulated_value"] == pytest.approx(11.659849276837, abs=1.0e-9)
    assert len(density_rows) == 40 * 40
    assert sum(row["weighted_stems_ha"] for row in density_rows) == pytest.approx(1924.34, abs=1.0e-9)


def test_manifest_outputs_are_machine_readable(tmp_path):
    paths = write_manifest(tmp_path)
    payload = json.loads(paths["json"].read_text(encoding="utf-8"))
    with paths["summary_csv"].open(newline="", encoding="utf-8") as stream:
        summary = list(csv.DictReader(stream))
    with paths["density_csv"].open(newline="", encoding="utf-8") as stream:
        density = list(csv.DictReader(stream))
    assert list(summary[0]) == SUMMARY_FIELDS
    assert list(density[0]) == DENSITY_FIELDS
    assert len(density) == 1600
    assert "not a statistical estimate" in payload["methodological_warning"]
    assert "Initial observables" in paths["markdown"].read_text(encoding="utf-8")
