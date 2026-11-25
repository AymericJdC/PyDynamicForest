import numpy as np
import pytest

from simulations.article.parameters import build_parameters
from simulations.article.ecouves_a5.hierarchical_height_diagnostics import (
    RELATIVE_DBH_LABELS,
    compare_profiles,
    hierarchy_profile,
)


def state_with_mass():
    p = build_parameters()
    U = np.zeros((p.numerics.grid.nx, p.numerics.grid.ny))
    U[5, 3] = 10.0
    U[10, 8] = 20.0
    U[15, 13] = 30.0
    return p, U


def test_hierarchy_profile_partitions_total_density():
    p, U = state_with_mass()
    rows = hierarchy_profile(U, p, year=1998, source='test')
    assert tuple(row.hierarchy_class for row in rows) == RELATIVE_DBH_LABELS
    assert sum(row.density_share for row in rows) == pytest.approx(1.0)
    assert sum(row.contribution_to_mean_height for row in rows) > 0.0


def test_identical_profiles_have_zero_comparison():
    p, U = state_with_mass()
    rows = hierarchy_profile(U, p, year=1998, source='test')
    comparison = compare_profiles(rows, rows)
    assert all(row.density_share_difference == pytest.approx(0.0) for row in comparison)
    assert all(row.mean_height_difference_m == pytest.approx(0.0) for row in comparison)
    assert all(row.height_contribution_difference == pytest.approx(0.0) for row in comparison)


def test_vertical_shift_changes_height_not_density_share():
    p, target = state_with_mass()
    simulated = np.roll(target, 1, axis=0)
    target_rows = hierarchy_profile(target, p, year=1998, source='target')
    simulated_rows = hierarchy_profile(simulated, p, year=1998, source='simulated')
    comparison = compare_profiles(simulated_rows, target_rows)
    assert all(row.density_share_difference == pytest.approx(0.0) for row in comparison)
    occupied = [
        row
        for row in comparison
        if row.simulated_density_share > 0.0
        and row.target_density_share > 0.0
    ]
    assert occupied
    assert all(
        np.isfinite(row.mean_height_difference_m)
        and row.mean_height_difference_m > 0.0
        for row in occupied
    )


def test_hierarchy_uses_state_specific_quadratic_dbh():
    p, U = state_with_mass()
    shifted = np.roll(U, 2, axis=1)
    first = hierarchy_profile(U, p, year=1998, source='first')
    second = hierarchy_profile(shifted, p, year=2016, source='second')
    assert sum(row.density_share for row in first) == pytest.approx(1.0)
    assert sum(row.density_share for row in second) == pytest.approx(1.0)
