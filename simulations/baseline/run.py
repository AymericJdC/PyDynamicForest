"""
Run the baseline reduced scenario.

At this stage, this script only builds the core conceptual objects:
    - x0: InitialCondition
    - p : Parameters
    - c : SimulationContext

The actual refactored solver will be connected in a later step.
"""

from simulations.baseline.initial_condition import build_initial_condition
from simulations.baseline.parameters import build_parameters
from simulations.baseline.context import build_context


def main() -> None:
    x0 = build_initial_condition()
    p = build_parameters()
    c = build_context()

    print("Baseline scenario successfully built.")
    print()
    print("Initial condition:")
    print(f"  name         = {x0.name}")
    print(f"  initial_age  = {x0.initial_age}")
    print(f"  mass_target  = {x0.mass_target}")
    print()
    print("Parameters:")
    print(f"  name         = {p.name}")
    print(f"  grid         = {p.numerics.grid.nx} x {p.numerics.grid.ny}")
    print(f"  time steps   = {p.numerics.time.n_steps}")
    print(f"  dt           = {p.numerics.time.dt}")
    print()
    print("Context:")
    print(f"  name         = {c.name}")
    print(f"  initial_age  = {c.initial_age}")
    print(f"  final_age    = {c.final_age}")
    print(f"  snapshots    = {c.output.snapshot_ages}")


if __name__ == "__main__":
    main()