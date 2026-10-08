import csv
import json

import numpy as np
import pytest

from pydynamicforest.diagnostics import proportional_top_height
from simulations.dominant_height_sensitivity.run import (
    build_parameters_for_grid,
    controlled_density,
    evaluate_case,
    run_study,
)


def test_controlled_density_has_target_trapezoidal_mass():
    p = build_parameters_for_grid(81, 40)
    U = controlled_density(p, "regular_height_dbh", mass_target=800.0)
    from pydynamicforest.numerics import integrate_2d_trapezoidal

    assert U.shape == (81, 40)
    assert np.all(U >= 0.0)
    assert integrate_2d_trapezoidal(U, p.numerics.grid.dx, p.numerics.grid.dy) == pytest.approx(800.0)


def test_proportional_operator_converges_on_regular_case():
    rows = evaluate_case(
        "regular_height_dbh",
        ny_values=(20, 40, 80, 160),
        reference_ny=640,
    )
    errors = [row["absolute_error_proportional"] for row in rows]

    assert errors[-1] < errors[0]
    assert errors[-1] < 0.02


def test_dispersed_case_separates_extreme_and_proportional_operators():
    rows = evaluate_case(
        "dispersed_threshold",
        ny_values=(40,),
        reference_ny=640,
    )
    row = rows[0]

    assert row["current"] < row["proportional"] < row["legacy"]
    assert row["legacy"] - row["current"] > 0.05


def test_study_writes_machine_readable_outputs(tmp_path):
    result = run_study(tmp_path)

    assert result["csv_path"].is_file()
    assert result["json_path"].is_file()

    with result["csv_path"].open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    summary = json.loads(result["json_path"].read_text(encoding="utf-8"))

    assert len(rows) == 8
    assert summary["ny_values"] == [20, 40, 80, 160]
    assert set(summary["cases"]) == {"regular_height_dbh", "dispersed_threshold"}
