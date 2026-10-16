# SPDX-License-Identifier: LGPL-3.0-or-later
"""Observed stand trajectory used by the manuscript simulation.

The values are transcribed exactly from the third chronological DOUGLAS ECOUVES
block in data_final_simu.csv. The block identity, plot correspondence, treatment
history, and empirical definition of dominant height remain to be confirmed.
"""

from __future__ import annotations

from math import pi, sqrt

SOURCE_PROVENANCE = {
    "source_file": "data_final_simu.csv",
    "dataset_label": "DOUGLAS ECOUVES",
    "series_selection": "third chronological block among three blocks sharing the label",
    "series_index": 3,
    "plot_identification": "pending confirmation from Ecouves data documentation",
    "treatment_history": "pending confirmation",
    "dominant_height_definition": "pending empirical confirmation",
    "inventory_level": "stand-level summary table; complete individual inventories expected separately",
    "repository_policy": "source file is not committed; exact extracted values are transcribed below",
}

# N: trees/ha; G: m2/ha; Dm: cm; Hm and H0: m.
# None represents the literal NA entries found in the source file.
OBSERVATIONS = {
    18.0: {"N": 1924.342105, "G": 21.60515264, "Dm": 11.69312727, "Hm": 9.610508086, "H0": 11.65988237},
    22.0: {"N": 1907.894737, "G": 31.87450755, "Dm": 14.18537032, "Hm": 12.60638531, "H0": 14.78614144},
    28.0: {"N": 1825.657895, "G": 44.39676873, "Dm": 16.98226258, "Hm": 17.10779016, "H0": 19.25032478},
    33.0: {"N": 1669.407895, "G": 50.92022358, "Dm": 18.93395013, "Hm": 19.81812702, "H0": 23.88106038},
    38.0: {"N": 1381.578947, "G": 57.07497821, "Dm": 22.02401260, "Hm": 24.14307989, "H0": 26.77016131},
    43.0: {"N": 1175.986842, "G": 62.74670543, "Dm": 25.03740979, "Hm": 26.81473993, "H0": 29.82857931},
    45.0: {"N": 1143.092105, "G": 66.31669739, "Dm": 26.10141067, "Hm": 28.23042106, "H0": 31.61278016},
    51.0: {"N": 978.6184211, "G": 74.74117689, "Dm": 30.06022270, "Hm": None, "H0": None},
    53.0: {"N": 937.5000000, "G": 75.14017676, "Dm": 30.76157909, "Hm": None, "H0": None},
    54.0: {"N": 921.0526316, "G": 76.26276882, "Dm": 31.26542016, "Hm": 32.15922885, "H0": 36.83922322},
    57.0: {"N": 921.0526316, "G": 81.18132407, "Dm": 32.14361440, "Hm": None, "H0": None},
    60.0: {"N": 888.1578947, "G": 85.33191746, "Dm": 33.50506283, "Hm": 33.96915770, "H0": 38.85315315},
    63.0: {"N": 855.2631579, "G": 88.65997035, "Dm": 34.76617305, "Hm": 35.17780594, "H0": 39.57932507},
    66.0: {"N": 731.9078947, "G": 87.93179722, "Dm": 37.73939235, "Hm": 37.51656632, "H0": 42.23550242},
    69.0: {"N": 682.5657895, "G": 89.55632942, "Dm": 39.44741553, "Hm": 38.96861330, "H0": 43.14040062},
}

UNITS = {"N": "trees/ha", "G": "m2/ha", "Dm": "cm", "Dg": "cm", "sigma_D": "cm", "Hm": "m", "H0": "m", "H0_minus_Hm": "m"}
STATUS = {"N": "observed", "G": "observed", "Dm": "observed", "Dg": "derived_from_N_and_G", "sigma_D": "derived_from_Dm_and_Dg", "Hm": "observed_or_missing", "H0": "observed_or_missing_definition_pending", "H0_minus_Hm": "derived_from_observed_H0_and_Hm"}


def observation_ages() -> tuple[float, ...]:
    return tuple(OBSERVATIONS)


def quadratic_mean_dbh_cm(N: float, G: float) -> float:
    if N <= 0.0 or G < 0.0:
        raise ValueError("N must be positive and G must be non-negative.")
    return 100.0 * sqrt(4.0 * G / (pi * N))


def dbh_standard_deviation_cm(Dm: float, Dg: float) -> float:
    variance = Dg**2 - Dm**2
    if variance < -1.0e-12:
        raise ValueError("Dm and Dg imply a negative DBH variance.")
    return sqrt(max(0.0, variance))


def observation_at_age(age: float, include_derived: bool = True) -> dict:
    key = float(age)
    if key not in OBSERVATIONS:
        raise KeyError(f"No observation is available at age {age}.")
    row = dict(OBSERVATIONS[key])
    if include_derived:
        row["Dg"] = quadratic_mean_dbh_cm(row["N"], row["G"])
        row["sigma_D"] = dbh_standard_deviation_cm(row["Dm"], row["Dg"])
        row["H0_minus_Hm"] = (
            None if row["H0"] is None or row["Hm"] is None
            else row["H0"] - row["Hm"]
        )
    return row


def observation_records(include_derived: bool = True) -> list[dict]:
    return [{"age": age, **observation_at_age(age, include_derived)} for age in observation_ages()]
