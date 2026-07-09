# SPDX-License-Identifier: LGPL-3.0-or-later

"""
Baseline simulation context.

This file defines c, the SimulationContext object used in:

    results = simulate(x0, p, c)

The scenario values are read from simulations.baseline.config.
"""

from simulations.baseline.config import BASELINE_CONFIG

from pydynamicforest.types import OutputSpecification, SimulationContext


def build_context(config: dict | None = None) -> SimulationContext:
    """
    Build the baseline simulation context.

    The baseline context requests observations at biologically meaningful
    stand ages rather than at hard-coded numerical indices.

    With save_full_trajectory=False, only the requested observations are stored
    in results.observations, while time series diagnostics are still computed
    at every time step.
    """

    if config is None:
        config = BASELINE_CONFIG

    ages_cfg = config["ages"]
    output_cfg = config["output"]

    output = OutputSpecification(
        observation_ages=output_cfg["observation_ages"],
        save_full_trajectory=output_cfg["save_full_trajectory"],
        compute_time_series=output_cfg["compute_time_series"],
        save_figures=output_cfg["save_figures"],
        save_tables=output_cfg["save_tables"],
    )

    return SimulationContext(
        name=f"{config['name']}_context",
        initial_age=ages_cfg["initial_age"],
        final_age=ages_cfg["final_age"],
        output=output,
        description=(
            "Baseline context corresponding to a simulation from stand age "
            f"{ages_cfg['initial_age']} to stand age {ages_cfg['final_age']}. "
            "Only requested model observations are stored."
        ),
    )