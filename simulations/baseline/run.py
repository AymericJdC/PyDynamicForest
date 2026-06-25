"""
Run the baseline reduced scenario.

At this stage, this script builds:
    - x0: InitialCondition
    - p : Parameters
    - c : SimulationContext
    - state0: initial discretized State
"""

from simulations.baseline.initial_condition import build_initial_condition
from simulations.baseline.parameters import build_parameters
from simulations.baseline.context import build_context

from pydynamicforest.initial_conditions import (
    build_initial_state,
    integrate_2d_trapezoidal,
)


def main() -> None:
    x0 = build_initial_condition()
    p = build_parameters()
    c = build_context()

    state0 = build_initial_state(x0, p, c)

    grid = p.numerics.grid
    initial_mass = integrate_2d_trapezoidal(state0.U, grid.dx, grid.dy)

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
    print()
    print("Initial state:")
    print(f"  time         = {state0.time}")
    print(f"  age          = {state0.age}")
    print(f"  U shape      = {state0.U.shape}")
    print(f"  min(U)       = {state0.U.min()}")
    print(f"  max(U)       = {state0.U.max()}")
    print(f"  mass         = {initial_mass}")


if __name__ == "__main__":
    main()