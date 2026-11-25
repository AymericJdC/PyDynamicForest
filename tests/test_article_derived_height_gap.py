import pytest

from simulations.article.observations import STATUS, UNITS, observation_at_age


def test_observed_height_gap_is_derived_when_both_heights_exist():
    row = observation_at_age(45.0)
    assert row["H0_minus_Hm"] == pytest.approx(31.61278016 - 28.23042106)
    assert UNITS["H0_minus_Hm"] == "m"
    assert STATUS["H0_minus_Hm"] == "derived_from_observed_H0_and_Hm"


def test_observed_height_gap_remains_missing_with_missing_heights():
    for age in (51.0, 53.0, 57.0):
        assert observation_at_age(age)["H0_minus_Hm"] is None
