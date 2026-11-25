# SPDX-License-Identifier: LGPL-3.0-or-later
"""Tests of the Écouves A5 study pipeline on synthetic data (no restricted inputs)."""

import json
import math

import numpy as np
import pandas as pd
import pytest

from pydynamicforest.numerics import product_trapezoidal_weights
from pydynamicforest.observation_operators import mean_dbh, mean_height, stand_density
from studies.ecouves_a5 import completion, heights
from studies.ecouves_a5.calibration import log_objective
from studies.ecouves_a5.dynamics import inventory_steps, simulate_inventories, summarize
from studies.ecouves_a5.regularise import regularise_records
from studies.ecouves_a5.run_all import Pipeline
from studies.ecouves_a5.settings import build_parameters, load_config

YEARS = (1985, 1992, 1998, 2016, 2020)
AGES = dict(zip(YEARS, (37.0, 44.0, 50.0, 68.0, 72.0)))


def synthetic_inputs(seed=0):
    """Population of plot A5 and measured heights following h = 2 + 9 log(D) + noise."""

    rng = np.random.default_rng(seed)
    pop, measured = [], []
    for k, year in enumerate(YEARS):
        n = 60 - 8 * k
        d = rng.uniform(15 + 3 * k, 45 + 4 * k, n)
        for i, di in enumerate(d):
            pop.append({"year": year, "age": AGES[year], "tree_id": str(i), "diameter_cm": di,
                        "expansion_factor_ha": 1 / 0.1216})
    for year in (1985, 1992, 2001, 2016, 2020):
        for plot in ("A1", "A2", "A5"):
            d = rng.uniform(15, 55, 8)
            for i, di in enumerate(d):
                measured.append({"plot": plot, "tree_id": str(i), "year": year, "dbh_cm": di,
                                 "height_m": 2 + 9 * math.log(di) + rng.normal(0, 1)})
    return pd.DataFrame(pop), pd.DataFrame(measured)


SOURCE = {1985: 1985, 1992: 1992, 1998: 2001, 2016: 2016, 2020: 2020}


def test_allometry_fit_recovers_coefficients():
    d = np.linspace(10, 60, 200)
    fit = heights.fit_allometry(d, 2 + 9 * np.log(d))
    assert fit["beta0"] == pytest.approx(2) and fit["beta1"] == pytest.approx(9)
    assert abs(fit["residuals"].mean()) < 1e-12


def test_completion_keeps_measured_heights_and_conserves_density():
    pop, measured = synthetic_inputs()
    assigned, summary = heights.complete_heights(pop, measured, SOURCE)
    for year in YEARS:
        rows = assigned[assigned.year == year]
        assert rows.weight_ha.sum() == pytest.approx(pop[pop.year == year].expansion_factor_ha.sum())
    a5 = measured[(measured["plot"] == "A5") & (measured.year == 1985)].set_index("tree_id").height_m
    kept = assigned[(assigned.year == 1985) & assigned.measured_height_available].set_index("tree_id").height_m
    assert len(kept) > 0 and np.allclose(kept, a5.loc[kept.index])
    imputed = assigned[(assigned.year == 1998) & ~assigned.measured_height_available]
    assert (imputed.component_count == 24).all()      # 24 measured pairs in 2001
    assert (summary.set_index("year").loc[1998, "measured_heights"]) == 0


def test_completion_rejects_small_samples():
    pop, measured = synthetic_inputs()
    with pytest.raises(ValueError):
        heights.complete_heights(pop, measured, SOURCE, minimum_sample=100)


def test_regularisation_conserves_density_and_first_moments():
    p = build_parameters(81, 0.04, 0.016, 1.66)
    rng = np.random.default_rng(1)
    d = rng.uniform(20, 50, 50)
    h = 2 + 9 * np.log(d)
    w = np.full(50, 8.2)
    U = regularise_records(h, d, w, p, 1.28, 2.56)
    assert stand_density(U, p) == pytest.approx(w.sum(), rel=1e-12)
    # the discrete triangular kernel preserves first moments up to the discretisation
    assert mean_height(U, p) == pytest.approx(np.average(h, weights=w), rel=1e-4)
    assert mean_dbh(U, p, unit="cm") == pytest.approx(np.average(d, weights=w), rel=1e-4)


def test_regularisation_is_grid_independent():
    rng = np.random.default_rng(2)
    d = rng.uniform(20, 50, 80)
    h = 2 + 9 * np.log(d) + rng.normal(0, 1, 80)
    w = np.full(80, 8.2)
    out = []
    for n in (157, 313):
        p = build_parameters(n, 0.04, 0.016, 1.66)
        out.append(summarize(regularise_records(h, d, w, p, 1.28, 2.56), p))
    for m in ("N", "Dm", "Hm", "sigma_D"):
        assert out[0][m] == pytest.approx(out[1][m], rel=2e-3)


def test_inventory_steps():
    assert inventory_steps(AGES, 0.0051) == {1985: 0, 1992: 1373, 1998: 2549, 2016: 6078, 2020: 6863}


def test_simulation_conserves_positivity_and_loses_mass():
    p = build_parameters(21, 0.04, 0.016, 1.66)
    rng = np.random.default_rng(3)
    d = rng.uniform(20, 40, 40)
    U0 = regularise_records(2 + 9 * np.log(d), d, np.full(40, 10.0), p, 2.5, 5.0)
    ages = {1985: 37.0, 1992: 37.5}
    states, series = simulate_inventories(U0, p, ages, record_every=20)
    n0, n1 = stand_density(states[1985], p), stand_density(states[1992], p)
    assert 0 < n1 < n0 and n1 >= n0 * math.exp(-0.04 * 0.5) * (1 - 1e-9)
    assert states[1992].min() > -1e-10 and len(series) >= 2


def test_log_objective_is_zero_on_targets():
    p = build_parameters(21, 0.04, 0.016, 1.66)
    rng = np.random.default_rng(4)
    d = rng.uniform(20, 40, 30)
    U = regularise_records(2 + 9 * np.log(d), d, np.full(30, 10.0), p, 2.5, 5.0)
    target = {1992: summarize(U, p)}
    assert log_objective("N", {1992: U}, target, p, [1992]) == pytest.approx(0, abs=1e-24)


def test_tree_level_diagnostics_and_deterministic_completion():
    rows = pd.DataFrame({"tree_id": ["a", "a", "b"], "height_m": [20.0, 22.0, 30.0],
                         "diameter_cm": [20.0, 20.0, 40.0], "weight_ha": [5.0, 5.0, 10.0]})
    det = completion.deterministic_completion(rows)
    assert det.loc["a", "height_m"] == pytest.approx(21) and det.loc["a", "weight_ha"] == pytest.approx(10)
    diag = completion.tree_level_diagnostics(det.height_m, det.diameter_cm, det.weight_ha, dominant_stems_ha=10)
    assert diag["Hm"] == pytest.approx(25.5) and diag["H0"] == pytest.approx(30)


def test_pipeline_end_to_end_on_a_small_grid(tmp_path):
    pop, measured = synthetic_inputs()
    assigned, _ = heights.complete_heights(pop, measured, SOURCE)
    table = tmp_path / "assigned.csv"
    assigned.to_csv(table, index=False)
    config = load_config(overrides={"data": {"assigned_heights": str(table)}, "inventories": {"ages": [37.0, 37.2, 37.4, 37.6, 37.8]}})
    pipe = Pipeline(config, tmp_path / "out", grid_nodes=21, log=lambda *_: None)
    config.raw["bootstrap"]["replicates"] = 3
    pipe.run(["heights", "regularise", "calibrate", "simulate", "completion", "bootstrap"])
    out = tmp_path / "out"
    manifest = json.loads((out / "manifest.json").read_text())
    assert set(manifest["steps"]) == {"heights", "regularise", "calibrate", "simulate", "completion", "bootstrap"}
    assert manifest["steps"]["calibrate"]["source"] == "config [model]"
    comparison = pd.read_csv(out / "simulation" / "comparison.csv")
    assert set(comparison.year) == set(YEARS)
    s5 = pd.read_csv(out / "completion" / "completion_sensitivity.csv")
    assert (s5.Hm_residual - s5.Hm_deterministic).abs().max() < 1e-9


def test_partial_user_configuration_is_merged_with_defaults(tmp_path):
    user = tmp_path / "local.toml"
    user.write_text('[data]\nassigned_heights = "x.csv"\n[model]\ngrid_nodes = 41\n', encoding="utf-8")
    config = load_config(user)
    assert config.raw["data"]["assigned_heights"] == "x.csv"
    assert config.model["grid_nodes"] == 41 and config.model["mortality"] == 0.0394
    assert config.raw["bootstrap"]["replicates"] == 1000


def test_bootstrap_resampling_conserves_tree_count_and_components():
    from studies.ecouves_a5.bootstrap import resample_trees

    rows = pd.DataFrame({"tree_id": ["a", "a", "b", "c"], "height_m": [20.0, 22.0, 30.0, 25.0],
                         "diameter_cm": [20.0, 20.0, 40.0, 30.0], "weight_ha": [5.0, 5.0, 10.0, 10.0]})
    rng = np.random.default_rng(0)
    for _ in range(20):
        s = resample_trees(rows, rng)
        assert s.weight_ha.sum() == pytest.approx(30.0, rel=0.7)          # 3 trees of weight 10
        assert s.groupby("tree_id").weight_ha.sum().mod(10).abs().max() < 1e-12
        if "a" in set(s.tree_id):
            assert (s.tree_id == "a").sum() == 2


def test_bootstrap_intervals_flag_simulated_values_outside():
    from studies.ecouves_a5.bootstrap import percentile_intervals

    samples = pd.DataFrame({"replicate": range(100), "year": 2020, "metric": "Hm",
                            "value": np.linspace(36, 40, 100)})
    comparison = pd.DataFrame({"year": [2020], "metric": ["Hm"], "simulated": [34.3], "observed": [37.9]})
    t = percentile_intervals(samples, comparison)
    assert bool(t.outside.iloc[0]) and t.lower.iloc[0] < 37.9 < t.upper.iloc[0]
