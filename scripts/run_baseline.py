# SPDX-License-Identifier: LGPL-3.0-or-later

"""
Run the PyDynamicForest baseline scenario.

This script provides a configurable command-line entry point for running
the baseline reduced scenario.

Typical usage from the repository root:

    python -m scripts.run_baseline --max-steps 10 --output-dir outputs/baseline_short

Run the full reduced baseline:

    python -m scripts.run_baseline --full --output-dir outputs/baseline_reduced_sparse

Modify selected configuration values from the command line:

    python -m scripts.run_baseline --nx 10 --ny 10 --n-steps 20 --max-steps 5
"""

from argparse import ArgumentParser, Namespace
from pathlib import Path
from time import perf_counter

from simulations.baseline.config import (
    available_baseline_presets,
    build_baseline_config_from_preset,
)
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
    
    parser.add_argument(
        "--preset",
        type=str,
        default="baseline",
        choices=available_baseline_presets(),
        help=(
            "Baseline configuration preset. "
            "Available presets: baseline, short-debug, dense-debug. "
            "Default: baseline."
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
    parser.add_argument(
        "--model-field-evaluation",
        type=str,
        default=None,
        choices=["legacy", "state"],
        help=(
            "Optional model-field evaluation mode override. "
            "Available values: 'legacy' or 'state'. "
            "If omitted, the value is read from the selected preset."
        ),
    )

    # ------------------------------------------------------------------
    # Optional configuration overrides
    # ------------------------------------------------------------------

    parser.add_argument(
        "--nx",
        type=int,
        default=None,
        help="Override the number of grid points in the height direction.",
    )

    parser.add_argument(
        "--ny",
        type=int,
        default=None,
        help="Override the number of grid points in the DBH direction.",
    )

    parser.add_argument(
        "--n-steps",
        type=int,
        default=None,
        help="Override the total number of time steps in the configuration.",
    )

    parser.add_argument(
        "--t-end",
        type=float,
        default=None,
        help="Override the final simulation time.",
    )

    parser.add_argument(
        "--initial-age",
        type=float,
        default=None,
        help="Override the initial stand age.",
    )

    parser.add_argument(
        "--final-age",
        type=float,
        default=None,
        help="Override the final stand age.",
    )

    parser.add_argument(
        "--observation-ages",
        type=float,
        nargs="+",
        default=None,
        help=(
            "Override requested observation ages. "
            "Example: --observation-ages 18 30 45 69"
        ),
    )

    return parser


def apply_cli_overrides(config: dict, args: Namespace) -> dict:
    """
    Apply command-line overrides to a baseline configuration copy.

    The input configuration is modified in place and also returned.
    """

    if args.nx is not None:
        config["grid"]["nx"] = args.nx

    if args.ny is not None:
        config["grid"]["ny"] = args.ny

    if args.n_steps is not None:
        config["time"]["n_steps"] = args.n_steps

    if args.initial_age is not None:
        config["ages"]["initial_age"] = args.initial_age

    if args.t_end is not None:
        config["time"]["t_end"] = args.t_end

    if args.final_age is not None:
        config["ages"]["final_age"] = args.final_age
    elif args.t_end is not None or args.initial_age is not None:
        config["ages"]["final_age"] = (
            config["ages"]["initial_age"] + config["time"]["t_end"]
        )

    if args.observation_ages is not None:
        config["output"]["observation_ages"] = args.observation_ages

    if args.model_field_evaluation is not None:
        config["solver"]["model_field_evaluation"] = args.model_field_evaluation

    return config


def print_configuration_summary(config: dict) -> None:
    """
    Print a compact summary of the effective scenario configuration.
    """

    print("Effective scenario configuration:")
    print(f"  name              = {config['name']}")
    print(f"  initial_age       = {config['ages']['initial_age']}")
    print(f"  final_age         = {config['ages']['final_age']}")
    print(f"  grid              = {config['grid']['nx']} x {config['grid']['ny']}")
    print(f"  t_start           = {config['time']['t_start']}")
    print(f"  t_end             = {config['time']['t_end']}")
    print(f"  n_steps           = {config['time']['n_steps']}")
    print(f"  matrix_storage    = {config['solver']['matrix_storage']}")
    print(f"  linear_solver     = {config['solver']['linear_solver']}")
    print(f" model_field_eval = {config['solver']['model_field_evaluation']}")
    print(f"  observation_ages  = {config['output']['observation_ages']}")
    print()


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    config = build_baseline_config_from_preset(args.preset)
    config = apply_cli_overrides(config, args)

    x0 = build_initial_condition(config)
    p = build_parameters(config)
    c = build_context(config)

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
    print_configuration_summary(config)

    print("Run configuration:")
    print(f" preset = {args.preset}")
    print(f"  output_dir        = {args.output_dir}")
    print(f"  full_run          = {args.full}")
    print(f"  max_steps         = {max_steps}")
    print(f"  solver_override   = {args.solver_name}")
    print(f" model_field_eval_override = {args.model_field_evaluation}")
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