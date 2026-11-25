import csv, json
import numpy as np
import pytest
from pydynamicforest.initial_conditions import build_initial_state
from pydynamicforest.numerics import compute_derived_quantities
from pydynamicforest.solver import compute_transport_components_legacy, evaluate_model_fields_for_solver
from simulations.article_submission_legacy.config import make_short_debug_config
from simulations.article_submission_legacy.context import build_context
from simulations.article_submission_legacy.diagnose_vertical_fluxes import CLASS_FIELDS, CHECK_FIELDS, INTERFACE_FIELDS, compute_vertical_face_fluxes, diagnose_state, vertical_divergence_from_faces, write_outputs
from simulations.article_submission_legacy.initial_condition import build_initial_condition
from simulations.article_submission_legacy.parameters import build_parameters


def _state_parameters():
    config = make_short_debug_config(); config["grid"].update({"nx": 7, "ny": 6})
    p = build_parameters(config); c = build_context(config)
    return build_initial_state(build_initial_condition(config), p, c), p


def test_face_divergence_reconstructs_height_transport_exactly():
    state, p = _state_parameters(); derived = compute_derived_quantities(state, p); fields = evaluate_model_fields_for_solver(state, p)
    faces, status = compute_vertical_face_fluxes(state, p, derived, fields)
    expected = compute_transport_components_legacy(state, p, derived, fields)["height"]
    np.testing.assert_allclose(vertical_divergence_from_faces(faces, p), expected, rtol=0, atol=1e-15)
    assert faces.shape == (state.U.shape[0] - 1, state.U.shape[1]); assert status.shape == faces.shape


def test_diagnostic_reconstructs_moment_rates_and_class_sums():
    state, p = _state_parameters(); interfaces, classes, check = diagnose_state(state, p, 18)
    assert check["max_abs_divergence_residual"] < 1e-12
    assert check["flux_dHm_dt"] == pytest.approx(check["direct_dHm_dt"], abs=1e-12)
    assert check["flux_dVarH_dt"] == pytest.approx(check["direct_dVarH_dt"], abs=1e-12)
    assert len(interfaces) == p.numerics.grid.nx - 1
    for classification in ("dbh_cm", "upwind_status"):
        selected = [r for r in classes if r["classification"] == classification]
        assert sum(r["dHm_dt_contribution_m_year"] for r in selected) == pytest.approx(check["direct_dHm_dt"], abs=1e-12)
        assert sum(r["dVarH_dt_contribution_m2_year"] for r in selected) == pytest.approx(check["direct_dVarH_dt"], abs=1e-12)


def test_interface_moment_contributions_sum_to_total():
    state, p = _state_parameters(); interfaces, _, check = diagnose_state(state, p, 18)
    assert sum(r["dMh_mean_contribution_m_year"] for r in interfaces) == pytest.approx(check["direct_dHm_dt"], abs=1e-12)
    assert sum(r["dVarH_dt_contribution_m2_year"] for r in interfaces) == pytest.approx(check["direct_dVarH_dt"], abs=1e-12)


def test_outputs_have_expected_row_counts(tmp_path):
    state, p = _state_parameters(); interfaces, classes, check = diagnose_state(state, p, 18)
    files = write_outputs(tmp_path, interfaces * 3, classes * 3, [check] * 3, "states")
    with files["interfaces"].open(newline="", encoding="utf-8") as f: irows = list(csv.DictReader(f))
    with files["classes"].open(newline="", encoding="utf-8") as f: crows = list(csv.DictReader(f))
    with files["checks"].open(newline="", encoding="utf-8") as f: checks = list(csv.DictReader(f))
    payload = json.loads(files["json"].read_text(encoding="utf-8"))
    assert len(irows) == 3 * (p.numerics.grid.nx - 1) and list(irows[0]) == INTERFACE_FIELDS
    assert len(crows) == 30 and list(crows[0]) == CLASS_FIELDS
    assert len(checks) == 3 and list(checks[0]) == CHECK_FIELDS
    assert payload["scope"] == "legacy vertical upwind face fluxes"
