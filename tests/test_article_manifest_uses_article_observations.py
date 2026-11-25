import pytest

from simulations.article.initial_condition_manifest import build_manifest
from simulations.article.observations import observation_at_age


def test_manifest_uses_exact_source_observations():
    _, rows, _ = build_manifest()
    by_name = {row["observable"]: row for row in rows}
    observed = observation_at_age(18.0)
    assert by_name["G"]["observed_or_derived_value"] == pytest.approx(observed["G"])
    assert by_name["Hm"]["observed_or_derived_value"] == pytest.approx(observed["Hm"])
    assert by_name["Dg"]["observed_or_derived_value"] == pytest.approx(observed["Dg"])
