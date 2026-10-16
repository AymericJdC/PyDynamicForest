import math

import pytest

from simulations.article.observations import (
    OBSERVATIONS,
    SOURCE_PROVENANCE,
    dbh_standard_deviation_cm,
    observation_ages,
    observation_at_age,
    observation_records,
    quadratic_mean_dbh_cm,
)


def test_third_ecouves_series_is_transcribed_exactly():
    assert observation_ages() == (18.0, 22.0, 28.0, 33.0, 38.0, 43.0, 45.0, 51.0, 53.0, 54.0, 57.0, 60.0, 63.0, 66.0, 69.0)
    initial = observation_at_age(18.0, include_derived=False)
    assert initial == {"N": 1924.342105, "G": 21.60515264, "Dm": 11.69312727, "Hm": 9.610508086, "H0": 11.65988237}
    final = observation_at_age(69.0, include_derived=False)
    assert final["N"] == pytest.approx(682.5657895)
    assert final["G"] == pytest.approx(89.55632942)
    assert final["H0"] == pytest.approx(43.14040062)


def test_missing_height_observations_remain_missing():
    for age in (51.0, 53.0, 57.0):
        row = observation_at_age(age)
        assert row["Hm"] is None
        assert row["H0"] is None
        assert row["Dg"] is not None
        assert row["sigma_D"] is not None


def test_derived_diameter_identities_are_exactly_defined():
    for row in observation_records():
        reconstructed_G = 0.25 * math.pi * row["N"] * (row["Dg"] / 100.0) ** 2
        assert reconstructed_G == pytest.approx(row["G"], rel=1.0e-14, abs=1.0e-12)
        assert row["Dg"] ** 2 == pytest.approx(row["Dm"] ** 2 + row["sigma_D"] ** 2, rel=1.0e-14, abs=1.0e-12)


def test_public_derivation_functions_validate_inputs():
    with pytest.raises(ValueError, match="N must be positive"):
        quadratic_mean_dbh_cm(0.0, 1.0)
    with pytest.raises(ValueError, match="negative DBH variance"):
        dbh_standard_deviation_cm(10.0, 9.0)
    with pytest.raises(KeyError, match="No observation"):
        observation_at_age(19.0)


def test_provenance_keeps_empirical_unknowns_explicit():
    assert SOURCE_PROVENANCE["series_index"] == 3
    assert "pending" in SOURCE_PROVENANCE["plot_identification"]
    assert "pending" in SOURCE_PROVENANCE["dominant_height_definition"]
    assert len(OBSERVATIONS) == 15
