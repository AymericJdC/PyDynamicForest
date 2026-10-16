import csv
import math
from pathlib import Path

import pytest

from simulations.article.mortality_intervals import (
    INTERVAL_FIELDS,
    apparent_mortality_rate,
    build_interval_rows,
    generate_mortality_interval_diagnostic,
)


def test_apparent_mortality_rate_definition_and_validation():
    rate = apparent_mortality_rate(1000.0, 900.0, 5.0)
    assert rate == pytest.approx(-math.log(0.9) / 5.0)
    with pytest.raises(ValueError, match="strictly positive"):
        apparent_mortality_rate(0.0, 900.0, 5.0)
    with pytest.raises(ValueError, match="Interval length"):
        apparent_mortality_rate(1000.0, 900.0, 0.0)


def test_interval_rows_capture_strong_initial_simulated_loss():
    source = Path("outputs/article_simulation/observations_simulation.csv")
    if not source.is_file():
        pytest.skip("Canonical comparison is unavailable.")
    with source.open(newline="", encoding="utf-8") as stream:
        rows = build_interval_rows(list(csv.DictReader(stream)))
    assert len(rows) == 14
    first = rows[0]
    assert (first["initial_age"], first["final_age"]) == (18.0, 22.0)
    assert first["observed_stem_loss"] == pytest.approx(16.447368, abs=1.0e-6)
    assert first["simulated_stem_loss"] > 150.0
    assert first["mortality_rate_ratio"] > 8.0
    assert first["empirical_interpretation_status"] == "pending_data_review"


def test_diagnostic_outputs_are_complete(tmp_path):
    source = Path("outputs/article_simulation")
    if not (source / "observations_simulation.csv").is_file():
        pytest.skip("Canonical comparison is unavailable.")
    result = generate_mortality_interval_diagnostic(source, tmp_path)
    with result["paths"]["csv"].open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    assert list(rows[0]) == INTERVAL_FIELDS
    assert len(rows) == 14
    assert result["paths"]["figure_pdf"].stat().st_size > 0
    assert result["paths"]["figure_png"].stat().st_size > 0
    markdown = result["paths"]["markdown"].read_text(encoding="utf-8")
    assert "must not be interpreted as natural competition mortality" in markdown
    assert result["metadata"]["n_intervals"] == 14
