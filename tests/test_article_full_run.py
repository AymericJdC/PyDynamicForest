import csv
import json

import numpy as np
import pytest

from simulations.article.full_run import (
    COMPARISON_FIELDS,
    DENSITY_FIELDS,
    TIME_SERIES_FIELDS,
    _comparison_rows,
    run_article_full,
)
from simulations.article.context import build_context
from simulations.article.initial_condition import build_initial_condition
from simulations.article.parameters import build_parameters
from pydynamicforest.initial_conditions import build_initial_state


def test_comparison_rows_preserve_missing_height_observations():
    p = build_parameters()
    state = build_initial_state(build_initial_condition(), p, build_context())
    rows = _comparison_rows(51.0, state, p)
    by_name = {row["observable"]: row for row in rows}
    assert by_name["Hm"]["observed_value"] == ""
    assert by_name["Hm"]["residual"] == ""
    assert by_name["Hm"]["observation_status"] == "missing_in_source"
    assert by_name["N"]["observed_value"] != ""


def test_zero_step_pipeline_writes_reproducible_outputs(tmp_path):
    result = run_article_full(tmp_path, max_steps=0, progress=False)
    paths = result["paths"]
    with paths["time_series"].open(newline="", encoding="utf-8") as stream:
        time_rows = list(csv.DictReader(stream))
    with paths["comparison"].open(newline="", encoding="utf-8") as stream:
        comparison = list(csv.DictReader(stream))
    with paths["densities"].open(newline="", encoding="utf-8") as stream:
        density = list(csv.DictReader(stream))
    metadata = json.loads(paths["metadata"].read_text(encoding="utf-8"))
    assert list(time_rows[0]) == TIME_SERIES_FIELDS
    assert list(comparison[0]) == COMPARISON_FIELDS
    assert list(density[0]) == DENSITY_FIELDS
    assert len(time_rows) == 1
    assert {float(row["requested_age"]) for row in comparison} == {18.0}
    assert len(density) == 1600
    assert metadata["steps_run"] == 0
    assert metadata["completed_full_horizon"] is False
    assert (tmp_path / "state_age_18.npz").is_file()


def test_short_pipeline_advances_and_keeps_nonnegative_density(tmp_path):
    result = run_article_full(tmp_path, max_steps=2, progress=False)
    assert result["metadata"]["steps_run"] == 2
    with np.load(tmp_path / "state_age_18.npz") as state:
        assert state["U"].min() >= 0.0
        assert float(state["actual_age"]) == pytest.approx(18.0)
