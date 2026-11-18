"""Lightweight tests for the frozen Ecouves A5 article runner."""
from __future__ import annotations
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "scripts" / "article" / "run_ecouves_a5_main_1985_2020.py"

def load_runner():
    spec=importlib.util.spec_from_file_location("frozen_ecouves_runner",RUNNER)
    assert spec is not None and spec.loader is not None
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

def test_frozen_calibration_constants():
    r=load_runner();assert r.MORTALITY_K==0.0377;assert r.DBH_GROWTH_RATE==0.0165

def test_calibrated_config_changes_only_two_model_values():
    r=load_runner();before=r.copy.deepcopy(r.ARTICLE_CONFIG);after=r.calibrated_article_config()
    assert after["model"]["mortality"]["value"]==0.0377
    assert after["model"]["dbh_growth"]["physical_rate"]==0.0165
    after["model"]["mortality"]["value"]=before["model"]["mortality"]["value"]
    after["model"]["dbh_growth"]["physical_rate"]=before["model"]["dbh_growth"]["physical_rate"]
    assert after==before

def test_target_steps_and_horizon():
    r=load_runner();steps=r.nearest_target_steps(0.0051)
    assert steps=={1985:0,1992:1373,1998:2549,2016:6078,2020:6863}
    assert r.completed_full_horizon(72.001299999992,72.0,0.0051)
    assert not r.completed_full_horizon(71.99,72.0,0.0051)

def test_year_age_convention_is_frozen():
    r=load_runner();assert r.YEAR_TO_AGE=={1985:37.0,1992:44.0,1998:50.0,2016:68.0,2020:72.0}
