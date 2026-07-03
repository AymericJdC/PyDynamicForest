"""
Output utilities for PyDynamicForest.

This module contains functions used to export SimulationResults objects.

It is intentionally kept separate from:
    - solver logic,
    - model equations,
    - numerical methods,
    - diagnostics.
"""

import csv
import json
from pathlib import Path
from typing import Any

from pydynamicforest.types import SimulationResults


def ensure_output_dir(output_dir: str | Path) -> Path:
    """
    Ensure that an output directory exists and return it as a Path.
    """

    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_time_series_csv(
    results: SimulationResults,
    output_dir: str | Path,
    filename: str = "time_series.csv",
) -> Path:
    """
    Save simulation time series to a CSV file.

    Columns:
        - time
        - age
        - total_mass
        - minimum_density
        - top_height
        - basal_area
    """

    output_path = ensure_output_dir(output_dir)
    csv_path = output_path / filename

    ts = results.time_series

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        writer.writerow(
            [
                "time",
                "age",
                "total_mass",
                "legacy_mass",
                "minimum_density",
                "top_height",
                "basal_area",
            ]
        )

        for row in zip(
            ts.times,
            ts.ages,
            ts.total_mass,
            ts.legacy_mass,
            ts.minimum_density,
            ts.top_height,
            ts.basal_area,
        ):
            writer.writerow(row)

    return csv_path


def _json_safe(value: Any) -> Any:
    """
    Convert simple Python objects to JSON-safe representations.
    """

    if isinstance(value, (str, int, float, bool)) or value is None:
        return value

    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}

    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]

    return str(value)


def save_metadata_json(
    results: SimulationResults,
    output_dir: str | Path,
    filename: str = "metadata.json",
) -> Path:
    """
    Save simulation metadata and high-level provenance to JSON.
    """

    output_path = ensure_output_dir(output_dir)
    json_path = output_path / filename

    metadata = {
        "initial_condition": {
            "name": results.initial_condition.name,
            "initial_age": results.initial_condition.initial_age,
            "mass_target": results.initial_condition.mass_target,
            "distribution_kind": results.initial_condition.distribution_kind,
            "source": results.initial_condition.source,
        },
        "parameters": {
            "name": results.parameters.name,
            "grid": {
                "nx": results.parameters.numerics.grid.nx,
                "ny": results.parameters.numerics.grid.ny,
                "x_min": results.parameters.numerics.grid.x_min,
                "x_max": results.parameters.numerics.grid.x_max,
                "y_min": results.parameters.numerics.grid.y_min,
                "y_max": results.parameters.numerics.grid.y_max,
                "dx": results.parameters.numerics.grid.dx,
                "dy": results.parameters.numerics.grid.dy,
            },
            "time": {
                "t_start": results.parameters.numerics.time.t_start,
                "t_end": results.parameters.numerics.time.t_end,
                "n_steps": results.parameters.numerics.time.n_steps,
                "dt": results.parameters.numerics.time.dt,
            },
            "scheme_name": results.parameters.numerics.scheme_name,
            "matrix_storage": results.parameters.numerics.matrix_storage,
            "linear_solver": results.parameters.numerics.linear_solver,
        },
        "context": {
            "name": results.context.name,
            "initial_age": results.context.initial_age,
            "final_age": results.context.final_age,
            "snapshot_ages": results.context.output.snapshot_ages,
        },
        "run_metadata": results.metadata,
        "final_state": {
           "step_index": results.final_state.step_index,
            "time": results.final_state.time,
            "age": results.final_state.age,
            "shape": list(results.final_state.U.shape),
        },
        "snapshots": {
            "number": len(results.snapshots),
            "requested_ages": results.context.output.snapshot_ages,
            "save_full_trajectory": results.context.output.save_full_trajectory,
            "saved": [
                {
                    "step_index": snapshot.step_index,
                    "time": snapshot.time,
                    "age": snapshot.age,
                    "shape": list(snapshot.U.shape),
                }
                for snapshot in results.snapshots
            ],
        },
    }

    with json_path.open("w", encoding="utf-8") as f:
        json.dump(_json_safe(metadata), f, indent=2, ensure_ascii=False)

    return json_path


def save_summary_txt(
    results: SimulationResults,
    output_dir: str | Path,
    filename: str = "summary.txt",
) -> Path:
    """
    Save a compact human-readable summary of the simulation.
    """

    output_path = ensure_output_dir(output_dir)
    summary_path = output_path / filename

    ts = results.time_series

    with summary_path.open("w", encoding="utf-8") as f:
        f.write("PyDynamicForest simulation summary\n")
        f.write("==================================\n\n")

        f.write("Initial condition\n")
        f.write("-----------------\n")
        f.write(f"name        = {results.initial_condition.name}\n")
        f.write(f"initial_age = {results.initial_condition.initial_age}\n")
        f.write(f"mass_target = {results.initial_condition.mass_target}\n\n")

        f.write("Parameters\n")
        f.write("----------\n")
        f.write(f"name        = {results.parameters.name}\n")
        f.write(
            f"grid        = "
            f"{results.parameters.numerics.grid.nx} x "
            f"{results.parameters.numerics.grid.ny}\n"
        )
        f.write(f"dt          = {results.parameters.numerics.time.dt}\n\n")

        f.write("Run metadata\n")
        f.write("------------\n")
        for key, value in results.metadata.items():
            f.write(f"{key} = {value}\n")

        f.write("\nFinal diagnostics\n")
        f.write("-----------------\n")
        f.write(f"final_time        = {results.final_state.time}\n")
        f.write(f"final_age         = {results.final_state.age}\n")
        f.write(f"final_step        = {results.final_state.step_index}\n")

        if ts.total_mass:
            f.write(f"total_mass        = {ts.total_mass[-1]}\n")
        if ts.legacy_mass:
            f.write(f"legacy_mass      = {ts.legacy_mass[-1]}\n")
        if ts.minimum_density:
            f.write(f"minimum_density   = {ts.minimum_density[-1]}\n")
        if ts.top_height:
            f.write(f"top_height        = {ts.top_height[-1]}\n")
        if ts.basal_area:
            f.write(f"basal_area        = {ts.basal_area[-1]}\n")
        
        f.write("\nSnapshots\n")
        f.write("---------\n")
        f.write(f"number              = {len(results.snapshots)}\n")
        f.write(
            f"requested_ages      = "
            f"{results.context.output.snapshot_ages}\n"
        )
        f.write(
            f"save_full_trajectory = "
            f"{results.context.output.save_full_trajectory}\n"
        )

        for snapshot in results.snapshots:
            f.write(
                f"step={snapshot.step_index}, "
                f"time={snapshot.time}, "
                f"age={snapshot.age}, "
                f"shape={snapshot.U.shape}\n"
            )
    return summary_path


def save_simulation_results(
    results: SimulationResults,
    output_dir: str | Path,
) -> dict[str, Path]:
    """
    Save the main outputs of a SimulationResults object.

    Returns a dictionary containing the generated file paths.
    """

    output_path = ensure_output_dir(output_dir)

    files = {
        "time_series": save_time_series_csv(results, output_path),
        "metadata": save_metadata_json(results, output_path),
        "summary": save_summary_txt(results, output_path),
    }

    return files