# SPDX-License-Identifier: LGPL-3.0-or-later
"""
Run the baseline reduced scenario.

This script builds:
    - x0: InitialCondition
    - p : Parameters
    - c : SimulationContext

Then it runs a short refactored simulation using:

    results = simulate(x0, p, c, max_steps=10)

and exports structured results to the outputs/ directory.
"""
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
        max_steps=10,
        solver_name="sparse",
    )

    elapsed = perf_counter() - start


    output_files = save_simulation_results(
        results,
        output_dir="outputs/baseline_reduced_sparse",
    )

    print("Baseline simulation completed.")
    print(f"  elapsed_seconds   = {elapsed:.2f}")
    print()
    print("Initial condition:")
    print(f"  name              = {x0.name}")
    print(f"  initial_age       = {x0.initial_age}")
    print(f"  mass_target       = {x0.mass_target}")
    print()
    print("Parameters:")
    print(f"  name              = {p.name}")
    print(f"  grid              = {p.numerics.grid.nx} x {p.numerics.grid.ny}")
    print(f"  total time steps  = {p.numerics.time.n_steps}")
    print(f"  dt                = {p.numerics.time.dt}")
    print()
    print("Context:")
    print(f"  name              = {c.name}")
    print(f"  initial_age       = {c.initial_age}")
    print(f"  final_age         = {c.final_age}")
    print()
    print("Run metadata:")
    for key, value in results.metadata.items():
        print(f"  {key:18s} = {value}")
    print()
    print("Final state after short run:")
    print(f"  step_index        = {results.final_state.step_index}")
    print(f"  time              = {results.final_state.time}")
    print(f"  age               = {results.final_state.age}")
    print(f"  U shape           = {results.final_state.U.shape}")
    print()
    print("Final diagnostics after short run:")
    print(f"  total_mass        = {results.time_series.total_mass[-1]}")
    print(f"  minimum_density   = {results.time_series.minimum_density[-1]}")
    print(f"  top_height        = {results.time_series.top_height[-1]}")
    print(f"  basal_area        = {results.time_series.basal_area[-1]}")
    print()
    print("Output files:")
    for name, path in output_files.items():
        print(f"  {name:18s} = {path}")


if __name__ == "__main__":
    main()