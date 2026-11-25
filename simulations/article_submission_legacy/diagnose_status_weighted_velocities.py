# SPDX-License-Identifier: LGPL-3.0-or-later
"""Diagnose status-weighted growth velocities and mortality by status class.

Q-7A-5a describes how the current population is allocated across the status
field and how the common status hierarchy modulates height growth, DBH growth,
and mortality. It diagnoses population-weighted fields, not transport
flux divergences.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np

from pydynamicforest.numerics import (
    compute_derived_quantities,
    product_trapezoidal_weights,
)
from pydynamicforest.observation_operators import (
    physical_dbh_nodes,
    physical_height_nodes,
)
from pydynamicforest.solver import evaluate_model_fields_for_solver
from pydynamicforest.types import State
from simulations.article_submission_legacy.parameters import build_parameters

DEFAULT_STATE_FILES = {
    18: "state_age_18.npz",
    45: "state_age_44p9994.npz",
    69: "state_age_69.npz",
}
STATUS_EDGES = np.array([0.0, 0.2, 0.4, 0.6, 0.8, 1.0])
QUANTILE_PROBABILITIES = (0.0, 0.1, 0.25, 0.5, 0.75, 0.9, 1.0)
TOP_STATUS_FRACTIONS = (0.1, 0.2)

CLASS_FIELDS = [
    "target_age", "actual_age", "status_class", "status_lower",
    "status_upper", "upper_inclusive", "stem_number", "stem_fraction",
    "mean_status", "mean_height_m", "height_sd_m", "mean_dbh_cm",
    "dbh_sd_cm", "mean_height_reference_velocity_m_year",
    "mean_effective_height_velocity_m_year",
    "mean_effective_dbh_velocity_cm_year",
    "mean_effective_mortality_year",
    "height_velocity_sum_m_trees_ha_year",
    "height_velocity_share", "mortality_sum_trees_ha_year",
    "mortality_share", "status_modulation_ratio",
]
QUANTILE_FIELDS = ["target_age", "variable", "probability", "weighted_quantile"]
GLOBAL_FIELDS = [
    "target_age", "stand_density", "mean_status",
    "mean_height_reference_velocity_m_year",
    "mean_effective_height_velocity_m_year",
    "mean_effective_dbh_velocity_cm_year",
    "mean_effective_mortality_year", "near_zero_height_velocity_fraction",
    "top_10_status_height_velocity_share", "top_20_status_height_velocity_share",
    "height_velocity_gini",
]


def load_saved_state(path: str | Path) -> State:
    with np.load(Path(path)) as saved:
        return State(
            time=float(saved["time"]), age=float(saved["age"]),
            U=np.array(saved["U"], dtype=float),
            step_index=int(saved["step_index"]),
        )


def weighted_quantile(values, weights, probabilities=QUANTILE_PROBABILITIES):
    """Return left-continuous weighted empirical quantiles."""
    values = np.asarray(values, dtype=float).ravel()
    weights = np.asarray(weights, dtype=float).ravel()
    probabilities = np.asarray(probabilities, dtype=float)
    if values.shape != weights.shape:
        raise ValueError("values and weights must have identical shapes.")
    if np.any(~np.isfinite(values)) or np.any(~np.isfinite(weights)):
        raise ValueError("values and weights must be finite.")
    if np.any(weights < 0.0):
        raise ValueError("weights must be non-negative.")
    if np.any((probabilities < 0.0) | (probabilities > 1.0)):
        raise ValueError("probabilities must lie in [0, 1].")
    positive = weights > 0.0
    if not np.any(positive):
        return np.full(probabilities.shape, np.nan)
    values = values[positive]
    weights = weights[positive]
    order = np.argsort(values, kind="mergesort")
    values = values[order]
    cumulative = np.cumsum(weights[order])
    cumulative /= cumulative[-1]
    indices = np.searchsorted(cumulative, probabilities, side="left")
    indices = np.clip(indices, 0, values.size - 1)
    return values[indices]


def weighted_gini(values, weights) -> float:
    """Return the weighted Gini coefficient of a non-negative variable."""
    values = np.asarray(values, dtype=float).ravel()
    weights = np.asarray(weights, dtype=float).ravel()
    positive = weights > 0.0
    values = values[positive]
    weights = weights[positive]
    if values.size == 0 or np.sum(weights) <= 0.0:
        return float("nan")
    if np.any(values < 0.0) or np.any(~np.isfinite(values)):
        raise ValueError("Gini values must be finite and non-negative.")
    weighted_sum = float(np.sum(weights * values))
    if weighted_sum <= 0.0:
        return 0.0
    order = np.argsort(values, kind="mergesort")
    values = values[order]
    weights = weights[order]
    cumulative_weight = np.cumsum(weights)
    cumulative_value = np.cumsum(weights * values)
    lorenz_x = np.concatenate(([0.0], cumulative_weight / cumulative_weight[-1]))
    lorenz_y = np.concatenate(([0.0], cumulative_value / cumulative_value[-1]))
    return float(1.0 - 2.0 * np.trapezoid(lorenz_y, lorenz_x))


def _weighted_mean(values, weights):
    total = float(np.sum(weights))
    return float("nan") if total <= 0.0 else float(np.sum(weights * values) / total)


def _weighted_sd(values, weights):
    mean = _weighted_mean(values, weights)
    if not np.isfinite(mean):
        return float("nan")
    return float(np.sqrt(max(0.0, _weighted_mean((values - mean) ** 2, weights))))


def _top_status_share(status, contribution, population_weights, fraction):
    order = np.argsort(status.ravel(), kind="mergesort")[::-1]
    pop = population_weights.ravel()[order]
    contrib = contribution.ravel()[order]
    total_pop = float(np.sum(pop))
    total_contrib = float(np.sum(contrib))
    if total_pop <= 0.0 or total_contrib <= 0.0:
        return float("nan")
    cutoff = fraction * total_pop
    cumulative = np.cumsum(pop)
    full = cumulative <= cutoff
    selected = float(np.sum(contrib[full]))
    first_partial = int(np.sum(full))
    previous = float(cumulative[first_partial - 1]) if first_partial else 0.0
    if first_partial < pop.size and pop[first_partial] > 0.0:
        selected += contrib[first_partial] * (cutoff - previous) / pop[first_partial]
    return selected / total_contrib


def diagnose_state(state: State, p=None, target_age=None):
    if p is None:
        p = build_parameters()
    derived = compute_derived_quantities(state, p)
    fields = evaluate_model_fields_for_solver(state, p)
    status = np.clip(derived.status_field, 0.0, 1.0)
    weights = product_trapezoidal_weights(p) * state.U
    height = np.broadcast_to(physical_height_nodes(p)[:, None], state.U.shape)
    dbh_cm = np.broadcast_to(physical_dbh_nodes(p, unit="cm")[None, :], state.U.shape)
    height_scale_m = float(p.model.physical_scales.height_scale)
    Ch = height_scale_m * fields["height_growth"]
    Cd_cm = 100.0 * fields["dbh_growth"]
    mortality_reference = fields["mortality"]
    effective_height = Ch * status
    effective_dbh = Cd_cm * status
    effective_mortality = mortality_reference * (1.0 - status)
    total_stems = float(np.sum(weights))
    total_height_velocity = float(np.sum(weights * effective_height))
    total_mortality = float(np.sum(weights * effective_mortality))
    age = state.age if target_age is None else target_age

    class_rows = []
    for index, (lower, upper) in enumerate(zip(STATUS_EDGES[:-1], STATUS_EDGES[1:])):
        upper_inclusive = index == len(STATUS_EDGES) - 2
        mask = (status >= lower) & ((status <= upper) if upper_inclusive else (status < upper))
        class_weights = np.where(mask, weights, 0.0)
        stems = float(np.sum(class_weights))
        velocity_sum = float(np.sum(class_weights * effective_height))
        mortality_sum = float(np.sum(class_weights * effective_mortality))
        mean_Ch = _weighted_mean(Ch, class_weights)
        mean_effective_height = _weighted_mean(effective_height, class_weights)
        class_rows.append({
            "target_age": age, "actual_age": state.age,
            "status_class": f"[{lower:.1f}, {upper:.1f}{']' if upper_inclusive else '['}",
            "status_lower": lower, "status_upper": upper,
            "upper_inclusive": upper_inclusive, "stem_number": stems,
            "stem_fraction": stems / total_stems if total_stems > 0.0 else float("nan"),
            "mean_status": _weighted_mean(status, class_weights),
            "mean_height_m": _weighted_mean(height, class_weights),
            "height_sd_m": _weighted_sd(height, class_weights),
            "mean_dbh_cm": _weighted_mean(dbh_cm, class_weights),
            "dbh_sd_cm": _weighted_sd(dbh_cm, class_weights),
            "mean_height_reference_velocity_m_year": mean_Ch,
            "mean_effective_height_velocity_m_year": mean_effective_height,
            "mean_effective_dbh_velocity_cm_year": _weighted_mean(effective_dbh, class_weights),
            "mean_effective_mortality_year": _weighted_mean(effective_mortality, class_weights),
            "height_velocity_sum_m_trees_ha_year": velocity_sum,
            "height_velocity_share": velocity_sum / total_height_velocity if total_height_velocity > 0.0 else float("nan"),
            "mortality_sum_trees_ha_year": mortality_sum,
            "mortality_share": mortality_sum / total_mortality if total_mortality > 0.0 else float("nan"),
            "status_modulation_ratio": mean_effective_height / mean_Ch if np.isfinite(mean_Ch) and mean_Ch != 0.0 else float("nan"),
        })

    variables = {
        "status": status,
        "height_reference_velocity_m_year": Ch,
        "effective_height_velocity_m_year": effective_height,
        "effective_dbh_velocity_cm_year": effective_dbh,
        "effective_mortality_year": effective_mortality,
    }
    quantile_rows = []
    for name, values in variables.items():
        quantiles = weighted_quantile(values, weights, QUANTILE_PROBABILITIES)
        for probability, value in zip(QUANTILE_PROBABILITIES, quantiles):
            quantile_rows.append({
                "target_age": age, "variable": name,
                "probability": probability, "weighted_quantile": float(value),
            })

    positive_population = weights > 0.0
    max_velocity = (
        float(np.max(effective_height[positive_population]))
        if np.any(positive_population)
        else 0.0
    )
    near_zero = (
        effective_height < 0.1 * max_velocity
        if max_velocity > 0.0
        else np.ones_like(effective_height, dtype=bool)
    )
    global_row = {
        "target_age": age, "stand_density": total_stems,
        "mean_status": _weighted_mean(status, weights),
        "mean_height_reference_velocity_m_year": _weighted_mean(Ch, weights),
        "mean_effective_height_velocity_m_year": _weighted_mean(effective_height, weights),
        "mean_effective_dbh_velocity_cm_year": _weighted_mean(effective_dbh, weights),
        "mean_effective_mortality_year": _weighted_mean(effective_mortality, weights),
        "near_zero_height_velocity_fraction": float(np.sum(weights * near_zero) / total_stems),
        "top_10_status_height_velocity_share": _top_status_share(status, weights * effective_height, weights, 0.1),
        "top_20_status_height_velocity_share": _top_status_share(status, weights * effective_height, weights, 0.2),
        "height_velocity_gini": weighted_gini(effective_height, weights),
    }
    return class_rows, quantile_rows, global_row


def diagnose_saved_states(state_dir, state_files=DEFAULT_STATE_FILES):
    p = build_parameters()
    class_rows, quantile_rows, global_rows = [], [], []
    for age, filename in state_files.items():
        path = Path(state_dir) / filename
        if not path.is_file():
            raise FileNotFoundError(f"Saved state not found: {path}")
        classes, quantiles, global_row = diagnose_state(load_saved_state(path), p, age)
        class_rows.extend(classes)
        quantile_rows.extend(quantiles)
        global_rows.append(global_row)
    return class_rows, quantile_rows, global_rows


def write_outputs(output_dir, class_rows, quantile_rows, global_rows, state_dir):
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    files = {
        "class_csv": output / "status_class_summary.csv",
        "quantile_csv": output / "weighted_velocity_quantiles.csv",
        "global_csv": output / "status_velocity_concentration.csv",
        "json": output / "status_weighted_velocities.json",
        "markdown": output / "status_weighted_velocities.md",
    }
    for key, rows, fields in (
        ("class_csv", class_rows, CLASS_FIELDS),
        ("quantile_csv", quantile_rows, QUANTILE_FIELDS),
        ("global_csv", global_rows, GLOBAL_FIELDS),
    ):
        with files[key].open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader(); writer.writerows(rows)
    payload = {
        "scope": "population-weighted status, effective velocities, and mortality",
        "state_directory": str(state_dir), "status_edges": STATUS_EDGES.tolist(),
        "class_convention": "left-closed/right-open except final class closed",
        "quantile_probabilities": list(QUANTILE_PROBABILITIES),
        "near_zero_definition": (
            "effective physical height velocity below 10% of its maximum "
            "on cells carrying positive population weight"
        ),
        "class_rows": class_rows, "quantile_rows": quantile_rows,
        "global_rows": global_rows,
    }
    files["json"].write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Q-7A-5a status-weighted velocities", "",
        "This diagnostic describes population-weighted fields, not transport divergences.", "",
        "| Age | Mean status | Mean Ch | Mean Ch*S | Near-zero fraction | Top 10% share | Top 20% share | Gini |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in global_rows:
        lines.append(
            "| {target_age:g} | {mean_status:.4f} | {mean_height_reference_velocity_m_year:.4f} | "
            "{mean_effective_height_velocity_m_year:.4f} | {near_zero_height_velocity_fraction:.4f} | "
            "{top_10_status_height_velocity_share:.4f} | {top_20_status_height_velocity_share:.4f} | "
            "{height_velocity_gini:.4f} |".format(**row)
        )
    lines.extend(["", "## Status classes", "",
        "| Age | Class | Stem fraction | Mean H | Mean D | Mean Ch*S | Velocity share | Mean mortality | Mortality share |",
        "|---:|:---|---:|---:|---:|---:|---:|---:|---:|",
    ])
    for row in class_rows:
        lines.append(
            "| {target_age:g} | {status_class} | {stem_fraction:.4f} | {mean_height_m:.3f} | "
            "{mean_dbh_cm:.3f} | {mean_effective_height_velocity_m_year:.4f} | "
            "{height_velocity_share:.4f} | {mean_effective_mortality_year:.4f} | {mortality_share:.4f} |".format(**row)
        )
    files["markdown"].write_text("\n".join(lines) + "\n", encoding="utf-8")
    return files


def run_diagnostic(state_dir, output_dir):
    rows = diagnose_saved_states(state_dir)
    return write_outputs(output_dir, *rows, state_dir)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-dir", default="outputs/observation_quadrature_full")
    parser.add_argument("--output-dir", default="outputs/status_weighted_velocities")
    args = parser.parse_args()
    files = run_diagnostic(args.state_dir, args.output_dir)
    for name, path in files.items():
        print(f"{name}: {path.resolve()}")


if __name__ == "__main__":
    main()
