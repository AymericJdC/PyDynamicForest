"""
Baseline initial condition for the reduced reference case.

This file defines x0, the initial condition object used in:

    results = simulate(x0, p, c)
"""

from pydynamicforest.types import InitialCondition


def build_initial_condition() -> InitialCondition:
    """
    Build the baseline initial condition.

    This corresponds to the Gaussian initial condition used in the
    reduced legacy reference case.
    """

    return InitialCondition(
        name="baseline_gaussian_initial_condition",
        initial_age=18.0,
        mass_target=2154.6,
        distribution_kind="gaussian_2d",
        distribution_parameters={
            "h0_physical": 10.50887557,
            "d0_physical": 0.1176045686,
            "sigma_h_physical": 1.5,
            "sigma_d_physical": 0.04,
        },
        source="legacy/DynamicForestModel_2D_reduced_reference.py",
        description=(
            "Gaussian initial condition from the reduced legacy reference case. "
            "Physical values are converted to normalized coordinates using "
            "the physical scales defined in ModelParameters."
        ),
    )