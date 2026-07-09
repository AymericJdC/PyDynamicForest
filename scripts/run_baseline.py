# SPDX-License-Identifier: LGPL-3.0-or-later

"""
Run the PyDynamicForest baseline scenario.

This script provides a configurable command-line entry point for running
the baseline reduced scenario.

Typical usage from the repository root:

    python -m scripts.run_baseline --max-steps 10 --output-dir outputs/baseline_short

Run the full reduced baseline:

    python -m scripts.run_baseline --full --output-dir outputs/baseline_reduced_sparse

Force a solver explicitly, for debugging or regression checks:

    python -m scripts.run_baseline --max-steps 10 --solver-name dense
"""

from argparse import ArgumentParser
from pathlib import Path
from time import perf_counter

from simulations.baseline.initial_condition import build_initial_condition
from simulations.baseline.parameters import build_parameters
from simulations.baseline.context import build_context

from pydynamicforest.solver import simulate
from pydynamicforest.io import save_simulation_results


def build_parser() -> ArgumentParser:
    """
    Build command-line argument parser.
    """

    parser = ArgumentParser(
        description="Run the PyDynamicForest baseline reduced scenario."
    )

    run_group = parser.add_mutually_exclusive_group()

    run_group.add_argument(
        "--max-steps",
        type=int,
        default=10,
        help=(
            "Maximum number of time steps to run. "
            "Default: 10. Ignored if --full is used."
        ),
    )

    run_group.add_argument(
        "--full",
        action="store_true",
        help="Run the full baseline reduced scenario.",
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs/baseline_run"),
        help="Directory where outputs will be written. Default: outputs/baseline_run",
    )

    parser.add_argument(
        "--solver-name",
        type=str,
        default=None,
        choices=["dense", "sparse"],
        help=(
            "Optional solver override. "
            "If omitted, the solver is selected from p.numerics.matrix_storage."
        ),
    )

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    x0 = build_initial_condition()
    p = build_parameters()
    c = build_context()

    if args.full:
        max_steps = None
    else:
        max_steps = args.max_steps

    start = perf_counter()

    results = simulate(
        x0,
        p,
        c,
        max_steps=max_steps,
        solver_name=args.solver_name,
    )

    elapsed = perf_counter() - start

    output_files = save_simulation_results(
        results,
        output_dir=args.output_dir,
    )

    print("Baseline simulation completed.")
    print("==============================")
    print()
    print("Run configuration:")
    print(f"  output_dir        = {args.output_dir}")
    print(f"  full_run          = {args.full}")
    print(f"  max_steps         = {max_steps}")
    print(f"  solver_override   = {args.solver_name}")
    print()
    print("Numerical configuration:")
    print(f"  grid              = {p.numerics.grid.nx} x {p.numerics.grid.ny}")
    print(f"  n_steps_requested = {p.numerics.time.n_steps}")
    print(f"  dt                = {p.numerics.time.dt}")
    print(f"  matrix_storage    = {p.numerics.matrix_storage}")
    print(f"  linear_solver     = {p.numerics.linear_solver}")
    print()
    print("Run metadata:")
    for key, value in results.metadata.items():
        print(f"  {key:18s} = {value}")
    print(f"  elapsed_seconds   = {elapsed:.2f}")
    print()
    print("Final state:")
    print(f"  step_index        = {results.final_state.step_index}")
    print(f"  time              = {results.final_state.time}")
    print(f"  age               = {results.final_state.age}")
    print()
    print("Final diagnostics:")
    print(f"  total_mass        = {results.time_series.total_mass[-1]}")
    print(f"  legacy_mass       = {results.time_series.legacy_mass[-1]}")
    print(f"  minimum_density   = {results.time_series.minimum_density[-1]}")
    print(f"  top_height        = {results.time_series.top_height[-1]}")
    print(f"  basal_area        = {results.time_series.basal_area[-1]}")
    print()
    print("Saved observations:")
    print(f"  number of observations = {len(results.observations)}")

    for observation in results.observations:
        print(
            f"  step={observation.step_index:4d}, "
            f"time={observation.time:.6f}, "
            f"age={observation.age:.6f}, "
            f"shape={observation.U.shape}"
        )

    print()
    print("Output files:")
    for name, path in output_files.items():
        if isinstance(path, list):
            print(f"  {name:18s} = {len(path)} files")
            for item in path:
                print(f"    - {item}")
        else:
            print(f"  {name:18s} = {path}")


if __name__ == "__main__":
    main()