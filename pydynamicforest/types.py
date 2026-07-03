# SPDX-License-Identifier: LGPL-3.0-or-later
"""
Core conceptual types for PyDynamicForest.

The architecture follows the conceptual pattern:

    results = simulate(x0, p, c)

where:
    x0 : InitialCondition
    p  : Parameters
    c  : SimulationContext

The goal is to separate:
    - initial conditions,
    - scientific model parameters,
    - numerical parameters,
    - simulation context,
    - dynamic states,
    - diagnostics and results.
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Optional
import numpy as np


@dataclass
class InitialCondition:
    """
    Description of the initial stand state.

    This object corresponds to x0 in the conceptual API:

        results = simulate(x0, p, c)

    It may either contain a fully discretized initial density U0,
    or the parameters required to build it on a given grid.
    """

    name: str
    initial_age: float
    mass_target: float
    distribution_kind: str = "gaussian_2d"
    distribution_parameters: dict[str, Any] = field(default_factory=dict)
    source: Optional[str] = None
    description: Optional[str] = None
    U0: Optional[np.ndarray] = None


@dataclass
class PhysicalScales:
    """
    Physical scaling used to map normalized variables to physical variables.
    """

    height_scale: float
    dbh_scale: float
    height_unit: str = "m"
    dbh_unit: str = "m"


@dataclass
class CoefficientLaw:
    """
    Generic representation of a model coefficient or process law.

    Examples:
        - diffusion coefficient
        - mortality coefficient
        - height growth velocity
        - dbh growth velocity
    """

    name: str
    function: Callable[..., float]
    description: Optional[str] = None
    parameters: dict[str, Any] = field(default_factory=dict)
    units: Optional[str] = None


@dataclass
class StatusModel:
    """
    Description of the social status / dominance model.

    In the current prototype, the status is based on a cumulative
    distribution J normalized by the total population mass.
    """

    name: str = "cumulative_fraction"
    description: Optional[str] = None


@dataclass
class ModelParameters:
    """
    Scientific parameters of the model.

    This object should contain the biological, ecological and mathematical
    assumptions, but not numerical discretization choices.
    """

    physical_scales: PhysicalScales
    diffusion_law: CoefficientLaw
    mortality_law: CoefficientLaw
    height_growth_law: CoefficientLaw
    dbh_growth_law: CoefficientLaw
    status_model: StatusModel = field(default_factory=StatusModel)
    description: Optional[str] = None


@dataclass
class GridDefinition:
    """
    Spatial grid definition in normalized variables.
    """

    x_min: float
    x_max: float
    y_min: float
    y_max: float
    nx: int
    ny: int

    @property
    def dx(self) -> float:
        return (self.x_max - self.x_min) / (self.nx - 1)

    @property
    def dy(self) -> float:
        return (self.y_max - self.y_min) / (self.ny - 1)

    @property
    def x(self) -> np.ndarray:
        return np.linspace(self.x_min, self.x_max, self.nx)

    @property
    def y(self) -> np.ndarray:
        return np.linspace(self.y_min, self.y_max, self.ny)


@dataclass
class TimeDiscretization:
    """
    Time discretization of the simulation.
    """

    t_start: float
    t_end: float
    n_steps: int

    @property
    def dt(self) -> float:
        return (self.t_end - self.t_start) / self.n_steps

    @property
    def t(self) -> np.ndarray:
        return np.linspace(self.t_start, self.t_end, self.n_steps + 1)


@dataclass
class NumericalParameters:
    """
    Numerical parameters of the simulation.

    This object contains the discretization and solver choices.
    """

    grid: GridDefinition
    time: TimeDiscretization
    scheme_name: str = "semi_implicit_diffusion_reaction_explicit_upwind_transport"
    matrix_storage: str = "dense"
    linear_solver: str = "numpy.linalg.solve"
    epsilon_zero_mass: float = 1e-15
    positivity_tolerance: float = 1e-12
    description: Optional[str] = None


@dataclass
class Parameters:
    """
    Aggregated parameters p.

    This object preserves the conceptual API:

        results = simulate(x0, p, c)

    while distinguishing scientific model parameters from numerical
    discretization and solver parameters.
    """

    model: ModelParameters
    numerics: NumericalParameters
    name: str = "default_parameters"
    description: Optional[str] = None


@dataclass
class OutputSpecification:
    """
    Specification of outputs requested from the simulation.
    """

    observation_ages: list[float] = field(default_factory=list)
    save_full_trajectory: bool = True
    compute_time_series: bool = True
    save_figures: bool = False
    save_tables: bool = False


@dataclass
class SimulationContext:
    """
    Scenario and execution context c.

    This object contains the simulation horizon, age mapping,
    output requests and possible exogenous scenarios.
    """

    name: str
    initial_age: float
    final_age: float
    output: OutputSpecification = field(default_factory=OutputSpecification)
    description: Optional[str] = None


@dataclass
class State:
    """
    Dynamic state of the system at a given time.

    The state should remain minimal: it contains the solution U and
    the associated time and age.
    """

    time: float
    age: float
    U: np.ndarray
    step_index: int = 0


@dataclass
class DerivedQuantities:
    """
    Quantities derived from a State.

    These are not part of the minimal state but may be required by
    the numerical scheme or diagnostics.
    """

    cumulative_distribution: Optional[np.ndarray] = None
    status_field: Optional[np.ndarray] = None
    transport_term: Optional[np.ndarray] = None
    total_mass: Optional[float] = None
    minimum_density: Optional[float] = None


@dataclass
class TimeSeries:
    """
    Aggregated temporal diagnostics.
    """

    times: list[float] = field(default_factory=list)
    ages: list[float] = field(default_factory=list)
    total_mass: list[float] = field(default_factory=list)
    legacy_mass: list[float] = field(default_factory=list)
    top_height: list[float] = field(default_factory=list)
    basal_area: list[float] = field(default_factory=list)
    minimum_density: list[float] = field(default_factory=list)


@dataclass
class SimulationResults:
    """
    Full result object returned by simulate(x0, p, c).
    """

    initial_condition: InitialCondition
    parameters: Parameters
    context: SimulationContext
    final_state: State
    observations: list[State] = field(default_factory=list)
    time_series: TimeSeries = field(default_factory=TimeSeries)
    diagnostics: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)