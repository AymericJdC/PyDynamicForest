import math

import pytest

from simulations.article.observations import (
    HISTORICAL_INITIAL_AGE,
    MAIN_COMPARISON_AGES,
    MAIN_INITIAL_AGE,
    OBSERVATIONS,
    SOURCE_PROVENANCE,
    TRANSITION_COMPARISON_AGES,
    TRANSITION_INITIAL_AGE,
    comparison_ages,
    dbh_standard_deviation_cm,
    observation_ages,
    observation_at_age,
    observation_records,
    quadratic_mean_dbh_cm,
)


def test_ecouves_a5_article_series_is_transcribed_exactly():
    assert observation_ages() == (
        18.0,
        22.0,
        28.0,
        33.0,
        38.0,
        43.0,
        45.0,
        51.0,
        53.0,
        54.0,
        57.0,
        60.0,
        63.0,
        66.0,
        69.0,
    )

    initial = observation_at_age(18.0, include_derived=False)
    assert initial == {
        "N": 1924.342105,
        "G": 21.60515264,
        "Dm": 11.69312727,
        "Hm": 9.610508086,
        "H0": 11.65988237,
    }

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
        assert row["H0_minus_Hm"] is None


def test_derived_diameter_identities_are_exactly_defined():
    for row in observation_records():
        reconstructed_G = (
            0.25 * math.pi * row["N"] * (row["Dg"] / 100.0) ** 2
        )
        assert reconstructed_G == pytest.approx(
            row["G"], rel=1.0e-14, abs=1.0e-12
        )
        assert row["Dg"] ** 2 == pytest.approx(
            row["Dm"] ** 2 + row["sigma_D"] ** 2,
            rel=1.0e-14,
            abs=1.0e-12,
        )


def test_public_derivation_functions_validate_inputs():
    with pytest.raises(ValueError, match="N must be positive"):
        quadratic_mean_dbh_cm(0.0, 1.0)
    with pytest.raises(ValueError, match="negative DBH variance"):
        dbh_standard_deviation_cm(10.0, 9.0)
    with pytest.raises(KeyError, match="No observation"):
        observation_at_age(19.0)
    with pytest.raises(KeyError, match="No observation"):
        comparison_ages(19.0)


def test_provenance_identifies_article_series_and_open_metadata():
    assert SOURCE_PROVENANCE["data_provider"] == "GIS Coop"
    assert SOURCE_PROVENANCE["series"] == "Ecouves A5"
    assert "GIS Coop" in SOURCE_PROVENANCE["aggregate_observation_source"]
    assert "Francois Ningre" in SOURCE_PROVENANCE["individual_inventory_source"]
    discrepancy_policy = SOURCE_PROVENANCE["source_discrepancy_policy"]
    assert "retained and documented by source" in discrepancy_policy
    assert "silently reconciled" in discrepancy_policy
    assert "one year" in SOURCE_PROVENANCE["individual_inventory_age_note"]

    assert SOURCE_PROVENANCE["main_initial_age"] == MAIN_INITIAL_AGE
    assert (
        SOURCE_PROVENANCE["transition_sensitivity_initial_age"]
        == TRANSITION_INITIAL_AGE
    )
    assert (
        SOURCE_PROVENANCE["historical_diagnostic_initial_age"]
        == HISTORICAL_INITIAL_AGE
    )

    assert (
        SOURCE_PROVENANCE["dominant_height_definition"]
        == "pending empirical documentation"
    )

    repository_policy = SOURCE_PROVENANCE["repository_policy"]
    assert "Ecouves A5" in repository_policy
    assert "other series are excluded" in repository_policy
    assert len(OBSERVATIONS) == 15


def test_comparison_ages_match_the_three_numerical_domains():
    assert MAIN_INITIAL_AGE == 45.0
    assert TRANSITION_INITIAL_AGE == 38.0
    assert HISTORICAL_INITIAL_AGE == 18.0

    assert MAIN_COMPARISON_AGES == comparison_ages(MAIN_INITIAL_AGE)
    assert TRANSITION_COMPARISON_AGES == comparison_ages(
        TRANSITION_INITIAL_AGE
    )

    assert MAIN_COMPARISON_AGES == (
        45.0,
        51.0,
        53.0,
        54.0,
        57.0,
        60.0,
        63.0,
        66.0,
        69.0,
    )
    assert TRANSITION_COMPARISON_AGES[0] == 38.0
    assert TRANSITION_COMPARISON_AGES[-1] == 69.0
