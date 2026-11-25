# SPDX-License-Identifier: LGPL-3.0-or-later

"""
Baseline initial condition.

This module defines x0, the InitialCondition object used in:

    results = simulate(x0, p, c)

The scenario values are read from simulations.baseline.config.
"""

from simulations.baseline.config import BASELINE_CONFIG

from pydynamicforest.types import InitialCondition


def build_initial_condition(config: dict | None = None) -> InitialCondition:
    """
    Build the baseline Gaussian initial condition.

    The physical Gaussian parameters are expressed in physical units:

        - height in meters;
        - DBH in meters.

    Normalization to the target number of trees per hectare is performed later
    when the continuous initial condition is discretized on the numerical grid.
    """

    if config is None:
        config = BASELINE_CONFIG

    ages_cfg = config["ages"]
    ic_cfg = config["initial_condition"]

    return InitialCondition(
        name=ic_cfg["name"],
        initial_age=ages_cfg["initial_age"],
        mass_target=ic_cfg["mass_target"],
        distribution_kind=ic_cfg["distribution_kind"],
        distribution_parameters={
            "h0_physical": ic_cfg["h0_physical"],
            "d0_physical": ic_cfg["d0_physical"],
            "sigma_h_physical": ic_cfg["sigma_h_physical"],
            "sigma_d_physical": ic_cfg["sigma_d_physical"],
        },
        source=ic_cfg["source"],
        description=(
            "Baseline Gaussian initial condition read from "
            "simulations.baseline.config."
        ),
    )