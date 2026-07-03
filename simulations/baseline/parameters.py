# SPDX-License-Identifier: LGPL-3.0-or-later
"""
Baseline parameters for the reduced reference case.

This file defines p, the Parameters object used in:

    results = simulate(x0, p, c)

The object p separates:
    - ModelParameters: scientific/model assumptions
    - NumericalParameters: grid, time stepping, solver choices
"""

from pydynamicforest.types import (
    CoefficientLaw,
    GridDefinition,
    ModelParameters,
    NumericalParameters,
    Parameters,
    PhysicalScales,
    TimeDiscretization,
)


def build_parameters() -> Parameters:
    """
    Build the baseline parameter set corresponding to the reduced
    legacy reference case.
    """

    # ------------------------------------------------------------------
    # Physical scales
    # ------------------------------------------------------------------

    physical_scales = PhysicalScales(
        height_scale=50.0,
        dbh_scale=0.9,
        height_unit="m",
        dbh_unit="m",
    )

    Hphys = physical_scales.height_scale
    Dphys = physical_scales.dbh_scale

    Lx = 1.0
    Ly = 1.0

    # ------------------------------------------------------------------
    # Model coefficient laws
    # ------------------------------------------------------------------

    def diffusion(t: float, x: float, y: float) -> float:
        return 0.00001

    def mortality(t: float, x: float, y: float) -> float:
        return 0.0365

    rh = 1.78 / Hphys

    def height_growth(t: float, x: float, y: float) -> float:
        return rh * (1.0 - x / Lx)

    rd = 0.0135 / Dphys

    def dbh_growth(t: float, x: float, y: float) -> float:
        return rd * (1.0 - y / Ly)

    model = ModelParameters(
        physical_scales=physical_scales,
        diffusion_law=CoefficientLaw(
            name="constant_diffusion",
            function=diffusion,
            parameters={"value": 0.00001},
            units="normalized_size_squared_per_year",
        ),
        mortality_law=CoefficientLaw(
            name="constant_status_dependent_mortality",
            function=mortality,
            parameters={"value": 0.0365},
            units="per_year",
        ),
        height_growth_law=CoefficientLaw(
            name="linear_height_growth_velocity",
            function=height_growth,
            parameters={
                "rh": rh,
                "physical_increment": 1.78,
            },
            units="normalized_height_per_year",
        ),
        dbh_growth_law=CoefficientLaw(
            name="linear_dbh_growth_velocity",
            function=dbh_growth,
            parameters={
                "rd": rd,
                "physical_increment": 0.0135,
            },
            units="normalized_dbh_per_year",
        ),
        description="Model parameters from the reduced legacy reference case.",
    )

    # ------------------------------------------------------------------
    # Numerical parameters
    # ------------------------------------------------------------------

    grid = GridDefinition(
        x_min=0.0,
        x_max=1.0,
        y_min=0.0,
        y_max=1.0,
        nx=20,
        ny=20,
    )

    time = TimeDiscretization(
        t_start=0.0,
        t_end=51.0,
        n_steps=1000,
    )

    numerics = NumericalParameters(
        grid=grid,
        time=time,
        scheme_name="legacy_semi_implicit_sparse_reduced",
        matrix_storage="sparse",
        linear_solver="scipy.sparse.linalg.spsolve",
        epsilon_zero_mass=1e-15,
        positivity_tolerance=1e-12,
        description=(
            "Reduced numerical configuration using the sparse legacy-like "
            "solver validated against the reduced legacy reference case."
        ),
    )

    return Parameters(
        name="baseline_reduced_parameters",
        model=model,
        numerics=numerics,
        description=(
            "Baseline reduced parameter set reproducing the reference "
            "legacy configuration with Nx=20, Ny=20, Nt=1000."
        ),
    )