# SPDX-License-Identifier: LGPL-3.0-or-later

"""
Baseline model and numerical parameters.

This module defines p, the Parameters object used in:

    results = simulate(x0, p, c)

The scenario values are read from simulations.baseline.config.
"""

from simulations.baseline.config import BASELINE_CONFIG

from pydynamicforest.types import (
    CoefficientLaw,
    GridDefinition,
    ModelParameters,
    NumericalParameters,
    Parameters,
    PhysicalScales,
    StatusModel,
    TimeDiscretization,
)


def build_parameters(config: dict | None = None) -> Parameters:
    """
    Build baseline model and numerical parameters.

    The baseline configuration corresponds to the reduced legacy reference
    case, but uses the sparse legacy-like solver by default.
    """

    if config is None:
        config = BASELINE_CONFIG

    scale_cfg = config["physical_scales"]
    grid_cfg = config["grid"]
    time_cfg = config["time"]
    model_cfg = config["model"]
    solver_cfg = config["solver"]

    # ------------------------------------------------------------------
    # Physical scales
    # ------------------------------------------------------------------

    physical_scales = PhysicalScales(
        height_scale=scale_cfg["height_scale"],
        dbh_scale=scale_cfg["dbh_scale"],
        height_unit="m",
        dbh_unit="m",
    )

    # ------------------------------------------------------------------
    # Coefficient laws
    # ------------------------------------------------------------------

    diffusion_value = model_cfg["diffusion"]["value"]
    mortality_value = model_cfg["mortality"]["value"]

    height_rate_normalized = (
        model_cfg["height_growth"]["physical_rate"]
        / physical_scales.height_scale
    )

    dbh_rate_normalized = (
        model_cfg["dbh_growth"]["physical_rate"]
        / physical_scales.dbh_scale
    )

    def diffusion(t: float, x: float, y: float) -> float:
        return diffusion_value

    def mortality(t: float, x: float, y: float) -> float:
        return mortality_value

    def height_growth(t: float, x: float, y: float) -> float:
        return height_rate_normalized * (1.0 - x)

    def dbh_growth(t: float, x: float, y: float) -> float:
        return dbh_rate_normalized * (1.0 - y)

    diffusion_law = CoefficientLaw(
        name=model_cfg["diffusion"]["name"],
        function=diffusion,
        description="Constant diffusion coefficient from baseline config.",
        parameters={
            "value": diffusion_value,
        },
        units="normalized^2/year",
    )

    mortality_law = CoefficientLaw(
        name=model_cfg["mortality"]["name"],
        function=mortality,
        description="Constant mortality coefficient from baseline config.",
        parameters={
            "value": mortality_value,
        },
        units="1/year",
    )

    height_growth_law = CoefficientLaw(
        name=model_cfg["height_growth"]["name"],
        function=height_growth,
        description=(
            "Linear height growth velocity normalized by the physical "
            "height scale."
        ),
        parameters={
            "physical_rate": model_cfg["height_growth"]["physical_rate"],
            "normalized_rate": height_rate_normalized,
        },
        units="normalized_height/year",
    )

    dbh_growth_law = CoefficientLaw(
        name=model_cfg["dbh_growth"]["name"],
        function=dbh_growth,
        description=(
            "Linear DBH growth velocity normalized by the physical "
            "DBH scale."
        ),
        parameters={
            "physical_rate": model_cfg["dbh_growth"]["physical_rate"],
            "normalized_rate": dbh_rate_normalized,
        },
        units="normalized_dbh/year",
    )

    status_model = StatusModel(
        name=model_cfg["status"]["name"],
        description=model_cfg["status"]["description"],
    )

    model = ModelParameters(
        physical_scales=physical_scales,
        diffusion_law=diffusion_law,
        mortality_law=mortality_law,
        height_growth_law=height_growth_law,
        dbh_growth_law=dbh_growth_law,
        status_model=status_model,
        description=(
            "Baseline model parameters read from simulations.baseline.config."
        ),
    )

    # ------------------------------------------------------------------
    # Numerical grid
    # ------------------------------------------------------------------

    grid = GridDefinition(
        x_min=grid_cfg["x_min"],
        x_max=grid_cfg["x_max"],
        y_min=grid_cfg["y_min"],
        y_max=grid_cfg["y_max"],
        nx=grid_cfg["nx"],
        ny=grid_cfg["ny"],
    )

    # ------------------------------------------------------------------
    # Time discretization
    # ------------------------------------------------------------------

    time = TimeDiscretization(
        t_start=time_cfg["t_start"],
        t_end=time_cfg["t_end"],
        n_steps=time_cfg["n_steps"],
    )

    # ------------------------------------------------------------------
    # Numerical solver configuration
    # ------------------------------------------------------------------

    numerics = NumericalParameters(
        grid=grid,
        time=time,
        scheme_name=solver_cfg["scheme_name"],
        matrix_storage=solver_cfg["matrix_storage"],
        linear_solver=solver_cfg["linear_solver"],
        epsilon_zero_mass=solver_cfg["epsilon_zero_mass"],
        positivity_tolerance=solver_cfg["positivity_tolerance"],
        description=(
            "Baseline numerical parameters read from "
            "simulations.baseline.config."
        ),
    )

    return Parameters(
        model=model,
        numerics=numerics,
        name=config["name"],
        description=config["description"],
    )