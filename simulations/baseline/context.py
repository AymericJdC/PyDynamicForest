"""
Baseline simulation context.

This file defines c, the SimulationContext object used in:

    results = simulate(x0, p, c)
"""

from pydynamicforest.types import OutputSpecification, SimulationContext


def build_context() -> SimulationContext:
    """
    Build the baseline simulation context.
    """

    output = OutputSpecification(
        snapshot_ages=[18.0, 45.0, 69.0],
        save_full_trajectory=True,
        compute_time_series=True,
        save_figures=False,
        save_tables=False,
    )

    return SimulationContext(
        name="baseline_reduced_context",
        initial_age=18.0,
        final_age=69.0,
        output=output,
        description=(
            "Baseline context corresponding to a simulation from stand age "
            "18 to stand age 69, matching the reduced legacy reference case."
        ),
    )