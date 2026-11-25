"""Q-9F.5 diagnostics of vertical structure along the relative-DBH hierarchy.

This lot compares simulated and reconstructed snapshots on the common native
PyDynamicForest grid. It does not infer individual longitudinal height growth:
the dynamic state is Eulerian and the reconstructed targets are snapshots.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np

from pydynamicforest.numerics import product_trapezoidal_weights
from pydynamicforest.observation_operators import (
    physical_dbh_nodes,
    physical_height_nodes,
)
from simulations.article.parameters import build_parameters

YEARS = (1992, 1998, 2016, 2020)
RELATIVE_DBH_EDGES = (0.0, 0.60, 0.80, 1.00, 1.20, 1.50, np.inf)
RELATIVE_DBH_LABELS = (
    'very_suppressed',
    'suppressed',
    'subordinate',
    'co_dominant',
    'dominant',
    'very_dominant',
)


@dataclass(frozen=True)
class HierarchyBin:
    year: int
    source: str
    bin_index: int
    hierarchy_class: str
    relative_dbh_lower: float
    relative_dbh_upper: float | None
    density_ha: float
    density_share: float
    mean_dbh_cm: float
    mean_height_m: float
    quadratic_mean_height_m: float
    mean_slenderness: float
    contribution_to_mean_height: float
    contribution_to_second_height_moment: float

    def record(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class HierarchyComparison:
    year: int
    bin_index: int
    hierarchy_class: str
    simulated_density_share: float
    target_density_share: float
    density_share_difference: float
    simulated_mean_height_m: float
    target_mean_height_m: float
    mean_height_difference_m: float
    simulated_height_contribution: float
    target_height_contribution: float
    height_contribution_difference: float

    def record(self) -> dict:
        return asdict(self)


def load_native_state(path: Path, key: str) -> np.ndarray:
    if not path.is_file():
        raise FileNotFoundError(path)
    with np.load(path) as data:
        if key not in data.files:
            raise KeyError(f'{path} does not contain {key}')
        state = np.array(data[key], dtype=float, copy=True)
    return state


def nodal_mass(state: np.ndarray, parameters) -> np.ndarray:
    mass = np.asarray(state, dtype=float) * product_trapezoidal_weights(parameters)
    if not np.all(np.isfinite(mass)):
        raise ValueError('state contains non-finite mass')
    if np.min(mass) < -parameters.numerics.positivity_tolerance:
        raise ValueError('state contains negative mass beyond tolerance')
    return np.maximum(mass, 0.0)


def quadratic_mean_dbh_cm(mass: np.ndarray, dbh_cm: np.ndarray) -> float:
    total = float(mass.sum())
    if total <= 0.0:
        raise ValueError('positive total mass is required')
    return float(np.sqrt(np.sum(mass * dbh_cm[None, :] ** 2) / total))


def hierarchy_profile(
    state: np.ndarray,
    parameters,
    *,
    year: int,
    source: str,
) -> tuple[HierarchyBin, ...]:
    mass = nodal_mass(state, parameters)
    height_m = physical_height_nodes(parameters)
    dbh_cm = physical_dbh_nodes(parameters, unit='cm')
    total = float(mass.sum())
    dg_cm = quadratic_mean_dbh_cm(mass, dbh_cm)
    relative_dbh = dbh_cm / dg_cm

    rows: list[HierarchyBin] = []
    for index, (lower, upper, label) in enumerate(
        zip(RELATIVE_DBH_EDGES[:-1], RELATIVE_DBH_EDGES[1:], RELATIVE_DBH_LABELS)
    ):
        if np.isinf(upper):
            selected = relative_dbh >= lower
        else:
            selected = (relative_dbh >= lower) & (relative_dbh < upper)
        class_mass = mass[:, selected]
        density = float(class_mass.sum())
        if density > 0.0:
            selected_dbh = dbh_cm[selected]
            mean_dbh = float(np.sum(class_mass * selected_dbh[None, :]) / density)
            mean_height = float(np.sum(class_mass * height_m[:, None]) / density)
            quadratic_height = float(
                np.sqrt(np.sum(class_mass * height_m[:, None] ** 2) / density)
            )
            slenderness = np.divide(
                100.0 * height_m[:, None],
                selected_dbh[None, :],
                out=np.zeros_like(class_mass),
                where=selected_dbh[None, :] > 0.0,
            )
            mean_slenderness = float(np.sum(class_mass * slenderness) / density)
        else:
            mean_dbh = mean_height = quadratic_height = mean_slenderness = float('nan')

        density_share = density / total
        contribution_h = (
            float(np.sum(class_mass * height_m[:, None]) / total) if density > 0.0 else 0.0
        )
        contribution_h2 = (
            float(np.sum(class_mass * height_m[:, None] ** 2) / total)
            if density > 0.0
            else 0.0
        )
        rows.append(
            HierarchyBin(
                year=year,
                source=source,
                bin_index=index,
                hierarchy_class=label,
                relative_dbh_lower=float(lower),
                relative_dbh_upper=None if np.isinf(upper) else float(upper),
                density_ha=density,
                density_share=density_share,
                mean_dbh_cm=mean_dbh,
                mean_height_m=mean_height,
                quadratic_mean_height_m=quadratic_height,
                mean_slenderness=mean_slenderness,
                contribution_to_mean_height=contribution_h,
                contribution_to_second_height_moment=contribution_h2,
            )
        )
    return tuple(rows)


def _difference(simulated: float, target: float) -> float:
    """Return zero for two jointly missing class statistics."""
    if np.isnan(simulated) and np.isnan(target):
        return 0.0
    if np.isnan(simulated) or np.isnan(target):
        return float("nan")
    return simulated - target


def compare_profiles(
    simulated: tuple[HierarchyBin, ...],
    target: tuple[HierarchyBin, ...],
) -> tuple[HierarchyComparison, ...]:
    by_sim = {row.bin_index: row for row in simulated}
    by_target = {row.bin_index: row for row in target}
    if set(by_sim) != set(by_target):
        raise ValueError('simulated and target profiles use different hierarchy bins')
    rows = []
    for index in sorted(by_sim):
        sim = by_sim[index]
        obs = by_target[index]
        rows.append(
            HierarchyComparison(
                year=sim.year,
                bin_index=index,
                hierarchy_class=sim.hierarchy_class,
                simulated_density_share=sim.density_share,
                target_density_share=obs.density_share,
                density_share_difference=sim.density_share - obs.density_share,
                simulated_mean_height_m=sim.mean_height_m,
                target_mean_height_m=obs.mean_height_m,
                mean_height_difference_m=_difference(sim.mean_height_m, obs.mean_height_m),
                simulated_height_contribution=sim.contribution_to_mean_height,
                target_height_contribution=obs.contribution_to_mean_height,
                height_contribution_difference=(
                    sim.contribution_to_mean_height - obs.contribution_to_mean_height
                ),
            )
        )
    return tuple(rows)


def run_hierarchical_diagnostics(
    simulated_dir: Path,
    target_dir: Path,
) -> tuple[tuple[dict, ...], tuple[dict, ...]]:
    parameters = build_parameters()
    profiles: list[dict] = []
    comparisons: list[dict] = []
    for year in YEARS:
        target = load_native_state(
            target_dir / f'ecouves_a5_native_initial_state_{year}.npz',
            'U0',
        )
        target_profile = hierarchy_profile(
            target,
            parameters,
            year=year,
            source='reconstructed_target',
        )
        profiles.extend(row.record() for row in target_profile)

        if year == 1992:
            simulated = target.copy()
        else:
            simulated = load_native_state(
                simulated_dir / f'ecouves_a5_simulated_state_{year}.npz',
                'U',
            )
        simulated_profile = hierarchy_profile(
            simulated,
            parameters,
            year=year,
            source='simulated',
        )
        profiles.extend(row.record() for row in simulated_profile)
        comparisons.extend(
            row.record() for row in compare_profiles(simulated_profile, target_profile)
        )
    return tuple(profiles), tuple(comparisons)
