import csv

import pytest

from simulations.article.full_run import run_article_full
from simulations.article.rebuild_comparison import rebuild_comparison


def test_rebuild_comparison_uses_saved_states_and_adds_observed_gap(tmp_path):
    run_article_full(tmp_path, max_steps=0, progress=False)
    paths = rebuild_comparison(
        tmp_path,
        ages=(18.0,),
    )
    with paths["comparison"].open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    gap = next(row for row in rows if row["observable"] == "H0_minus_Hm")
    assert float(gap["observed_value"]) == pytest.approx(11.65988237 - 9.610508086)
    assert gap["observation_status"] == "derived_from_observed_H0_and_Hm"


def test_rebuild_fails_if_a_saved_inventory_state_is_missing(tmp_path):
    with pytest.raises(FileNotFoundError, match="Saved state not found"):
        rebuild_comparison(tmp_path)
