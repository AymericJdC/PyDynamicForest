# SPDX-License-Identifier: LGPL-3.0-or-later
from time import perf_counter

from simulations.baseline.initial_condition import build_initial_condition
from simulations.baseline.parameters import build_parameters
from simulations.baseline.context import build_context

from pydynamicforest.solver import simulate
from pydynamicforest.io import save_simulation_results


def main() -> None:
    x0 = build_initial_condition()
    p = build_parameters()
    c = build_context()

    start = perf_counter()

    results = simulate(
        x0,
        p,
        c,
        max_steps=None,
        solver_name="sparse",
    )

    elapsed = perf_counter() - start

    output_files = save_simulation_results(
        results,
        output_dir="outputs/baseline_reduced_sparse",
    )

    print("Baseline reduced sparse simulation completed.")
    print()
    print("Run information:")
    print(f"  solver            = {results.metadata['solver']}")
    print(f"  n_steps_run       = {results.metadata['n_steps_run']}")
    print(f"  dt                = {results.metadata['dt']}")
    print(f"  elapsed_seconds   = {elapsed:.2f}")
    print()
    print("Final state:")
    print(f"  step_index        = {results.final_state.step_index}")
    print(f"  time              = {results.final_state.time}")
    print(f"  age               = {results.final_state.age}")
    print()
    print("Final diagnostics:")
    print(f"  total_mass        = {results.time_series.total_mass[-1]}")
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
        print(f"  {name:18s} = {path}")


if __name__ == "__main__":
    main()