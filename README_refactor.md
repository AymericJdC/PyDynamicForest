# PyDynamicForest refactor notes

## Purpose

This document summarizes the ongoing refactor of the original `DynamicForestModel_2D.py` script.

The goal is to transform the initial research script into a more structured, modular, maintainable and scientifically traceable codebase, while preserving the numerical and scientific behavior of the original implementation during the transition.

The refactor follows a progressive strategy:

1. preserve the original legacy script;
2. create reduced and short reference cases;
3. introduce conceptual objects;
4. separate initial conditions, model laws, numerical routines, diagnostics, solver and outputs;
5. validate each refactor step against legacy behavior;
6. progressively improve the numerical implementation.

## Conceptual architecture

The target conceptual API is:

    results = simulate(x0, p, c)

where:

- `x0` is an `InitialCondition`;
- `p` is a `Parameters` object;
- `c` is a `SimulationContext`;
- `results` is a `SimulationResults` object.

The object `Parameters` separates:

- `ModelParameters`: scientific and mathematical model assumptions;
- `NumericalParameters`: grid, time discretization, numerical scheme and solver choices.

This structure is inspired by the conceptual organization previously used in C-STABILITY, where a simulation is defined by an initial state, a set of parameters and a context.

## Main conceptual objects

The current refactor introduces the following objects in `pydynamicforest/types.py`:

- `InitialCondition`
- `PhysicalScales`
- `CoefficientLaw`
- `StatusModel`
- `ModelParameters`
- `GridDefinition`
- `TimeDiscretization`
- `NumericalParameters`
- `Parameters`
- `OutputSpecification`
- `SimulationContext`
- `State`
- `DerivedQuantities`
- `TimeSeries`
- `SimulationResults`

## Current package structure

    pydynamicforest/
    ├── __init__.py
    ├── types.py
    ├── initial_conditions.py
    ├── model.py
    ├── numerics.py
    ├── solver.py
    ├── diagnostics.py
    ├── io.py
    └── plotting.py

    simulations/
    └── baseline/
        ├── __init__.py
        ├── config.py
        ├── initial_condition.py
        ├── parameters.py
        ├── context.py
        └── run.py

    scripts/
    ├── __init__.py
    ├── run_baseline.py
    ├── run_baseline_reduced_sparse.py
    ├── compare_reduced_reference.py
    ├── plot_observations.py
    ├── plot_observation_comparisons.py
    └── plot_diagnostics.py

    legacy/
    ├── DynamicForestModel_2D_legacy.py
    ├── DynamicForestModel_2D_reduced_reference.py
    └── DynamicForestModel_2D_short_reference.py

    tests/
    reference_outputs/
    outputs/

## Scenario structure

A baseline reduced scenario has been introduced in:

    simulations/baseline/

This scenario defines:

    x0 = build_initial_condition()
    p = build_parameters()
    c = build_context()

and can be run through:

    results = simulate(
        x0,
        p,
        c,
        max_steps=10,
    )

The baseline scenario separates:

- the initial condition in `initial_condition.py`;
- model and numerical parameters in `parameters.py`;
- simulation context and requested observations in `context.py`;
- the runnable scenario in `run.py`.

## Baseline scenario configuration

The baseline reduced scenario now uses a centralized Python configuration file:

    simulations/baseline/config.py

This file gathers the main scenario settings:

- stand ages;
- initial condition;
- physical scales;
- numerical grid;
- time discretization;
- model coefficient laws;
- solver configuration;
- output and observation settings.

The builders:

    build_initial_condition()
    build_parameters()
    build_context()

read their values from this configuration.

This is a first step toward more flexible scenario management.

At this stage, the configuration is still expressed as a Python dictionary rather than an external YAML, JSON or TOML file. This avoids introducing an additional dependency and keeps the refactor incremental.

Future scenario-management work may introduce:

- alternative baseline configurations;
- high-resolution sparse configurations;
- dense debug configurations;
- alternative growth or mortality scenarios;
- external configuration files.

## Configurable baseline run

A configurable command-line script has been added:

    scripts/run_baseline.py

It can run either a short baseline simulation:

    pydf-run-baseline --max-steps 10 --output-dir outputs\baseline_short_cli

or the full reduced baseline simulation:

    pydf-run-baseline --full --output-dir outputs\baseline_reduced_sparse_cli

The equivalent developer commands using `python -m` remain available:

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m scripts.run_baseline --max-steps 10 --output-dir outputs\baseline_short_cli

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m scripts.run_baseline --full --output-dir outputs\baseline_reduced_sparse_cli

The script also allows an explicit solver override for debugging or regression checks:

    pydf-run-baseline --max-steps 2 --solver-name dense --output-dir outputs\baseline_dense_debug

By default, the solver is selected from the numerical parameters.

## Packaging

A minimal `pyproject.toml` file has been added.

The project can now be installed in editable mode with:

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m pip install -e .

or with development dependencies:

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m pip install -e ".[dev]"

The current packaging configuration includes:

- `pydynamicforest`;
- `simulations`;
- `scripts`.

This keeps the existing command-line workflow based on `python -m scripts...` functional after editable installation.

## Console entry points

Console entry points have been added through `pyproject.toml`.

After editable installation, the following commands are available:

    pydf-run-baseline
    pydf-run-baseline-reduced-sparse
    pydf-compare-reduced-reference
    pydf-plot-observations
    pydf-plot-observation-comparisons
    pydf-plot-diagnostics

These commands are wrappers around the corresponding script modules.

For example:

    pydf-run-baseline --max-steps 10 --output-dir outputs\baseline_short_cli

is equivalent to:

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m scripts.run_baseline --max-steps 10 --output-dir outputs\baseline_short_cli

If the `pydf-*` commands are not found on Windows, check that the `Scripts` directory of the environment is available in the `PATH`.

The executables can also be called explicitly, for example:

    C:\Users\saintemarie\.conda\envs\pydynamicforest\Scripts\pydf-run-baseline.exe --max-steps 10 --output-dir outputs\baseline_short_cli

## Legacy reference

The original script has been preserved in:

    legacy/DynamicForestModel_2D_legacy.py

A reduced reference case has also been created:

    legacy/DynamicForestModel_2D_reduced_reference.py

A short reference case has been created for fast regression checks:

    legacy/DynamicForestModel_2D_short_reference.py

The reduced and short reference cases are used to compare the refactored implementation against the original legacy numerical behavior.

## Current status

The following components have been implemented.

### Initial condition

`pydynamicforest/initial_conditions.py`

- builds the initial Gaussian density;
- normalizes it to the target number of trees per hectare;
- returns a `State`.

### Diagnostics

`pydynamicforest/diagnostics.py`

- total mass;
- trapezoidal mass;
- legacy mass;
- mass diagnostics;
- top height;
- basal area;
- minimum density;
- marginal height distribution;
- marginal DBH distribution.

### Numerical derived quantities

`pydynamicforest/numerics.py`

- grid index flattening;
- 2D trapezoidal weights;
- 2D trapezoidal integration;
- 2D cumulative trapezoidal integral;
- status field;
- derived numerical quantities.

### Model laws

`pydynamicforest/model.py`

- evaluates diffusion;
- evaluates mortality;
- evaluates height growth velocity;
- evaluates DBH growth velocity.

### Solver

`pydynamicforest/solver.py`

- implements a dense legacy-like one-step solver;
- implements a sparse legacy-like one-step solver;
- implements a structured simulation loop;
- supports observation selection by stand age;
- selects the one-step solver from numerical parameters by default;
- returns structured `SimulationResults`.

The high-level simulation API is:

    results = simulate(
        x0,
        p,
        c,
        max_steps=None,
    )

The solver can still be explicitly overridden if needed:

    results = simulate(x0, p, c, solver_name="dense")
    results = simulate(x0, p, c, solver_name="sparse")

Available solver names are currently:

- `"dense"`: dense legacy-like solver using `numpy.linalg.solve`;
- `"sparse"`: sparse legacy-like solver using `scipy.sparse`.

### I/O

`pydynamicforest/io.py`

- exports time series to CSV;
- exports metadata to JSON;
- exports a human-readable summary;
- exports selected observations as `.npz` files;
- loads exported observations from `.npz` files.

### Plotting

`pydynamicforest/plotting.py`

- plots 2D density fields from exported observations;
- plots marginal height distributions;
- plots marginal DBH distributions;
- plots diagnostic time series;
- plots comparison figures between observations.

User-facing plotting scripts are available:

    scripts/plot_observations.py
    scripts/plot_observation_comparisons.py
    scripts/plot_diagnostics.py

They generate figures from exported observation files and time-series files without rerunning the simulation.

## Solver selection

The simulation solver is now selected from the numerical parameters by default.

The standard API is therefore:

    results = simulate(x0, p, c)

The effective one-step solver is selected from:

    p.numerics.matrix_storage

Currently supported values are:

- `"dense"`: uses the dense legacy-like solver;
- `"sparse"`: uses the sparse legacy-like solver.

For the baseline reduced scenario, the numerical parameters are configured as:

    matrix_storage="sparse"
    linear_solver="scipy.sparse.linalg.spsolve"

Therefore, the default baseline simulation uses the sparse solver.

For regression tests or debugging, the solver can still be explicitly overridden:

    results = simulate(x0, p, c, solver_name="dense")

or:

    results = simulate(x0, p, c, solver_name="sparse")

The simulation metadata records:

- the effective solver used;
- the requested solver override, if any;
- the matrix storage mode;
- the linear solver name.

## Sparse solver validation

A sparse version of the legacy one-step solver has been implemented.

It has been validated against:

1. the dense refactored one-step solver;
2. the dense refactored short simulation;
3. the reduced legacy full reference case.

For the reduced reference case:

    Nx = 20
    Ny = 20
    Nt = 1000
    solver = sparse

The sparse solver reproduces the reduced legacy reference up to numerical precision for the main scalar outputs:

- final top height;
- final basal area;
- final legacy mass;
- minimum density over the trajectory.

The reduced sparse case currently runs in approximately 9 seconds on the working machine.

The dense solver is retained as a regression reference on small cases, but the sparse solver should now be preferred for practical simulations.

## Observation management

The simulation context supports observation selection by stand age.

In PyDynamicForest, observations are simulated model states selected for storage and analysis at requested stand ages.

They should not be confused with empirical field observations.

Observation ages are defined in the simulation context through the output specification, for example:

    OutputSpecification(
        observation_ages=[18.0, 45.0, 69.0],
        save_full_trajectory=False,
    )

When `save_full_trajectory` is `False`, only states close to the requested stand ages are stored in `results.observations`.

This avoids hard-coded numerical indices such as:

    U[5294, :, :]

and makes output selection closer to the scientific interpretation of the simulation.

## Observation exports

Selected observations are exported as `.npz` files under:

    outputs/<run_name>/observations/

Each observation corresponds to a simulated model state selected at a requested stand age.

Each `.npz` file contains:

- `U`: simulated density field;
- `time`: simulation time;
- `age`: stand age;
- `step_index`: numerical time-step index;
- `height_grid`: normalized height grid;
- `dbh_grid`: normalized DBH grid;
- `height_grid_physical`: height grid in physical units;
- `dbh_grid_physical`: DBH grid in physical units.

The normalized grids are useful for numerical consistency, while the physical grids are useful for biological interpretation and plotting.

## Observation plotting

A plotting module has been introduced:

    pydynamicforest/plotting.py

It provides reusable functions to generate figures from exported observations.

Observation plotting scripts include:

    scripts/plot_observations.py
    scripts/plot_observation_comparisons.py

They generate individual and comparison figures from exported observations.

## Diagnostic time-series plotting

Diagnostic time series are exported to:

    time_series.csv

A plotting utility has been added to generate figures from this file.

The reusable functions are implemented in:

    pydynamicforest/plotting.py

The user-facing script is:

    scripts/plot_diagnostics.py

Typical command:

    pydf-plot-diagnostics --input-file outputs\baseline_reduced_sparse\time_series.csv

By default, this reads:

    outputs/baseline_reduced_sparse/time_series.csv

and writes figures to:

    outputs/baseline_reduced_sparse/figures/time_series/

The standard diagnostic figures are:

- total mass;
- legacy mass;
- minimum density;
- top height;
- basal area.

## End-to-end CLI workflow test

An end-to-end command-line workflow test has been added.

It verifies the complete user-facing workflow:

1. run a short configurable baseline simulation;
2. export time series, metadata, summary and observations;
3. plot individual observations;
4. plot observation comparison figures;
5. plot diagnostic time series.

The test is marked as both `slow` and `e2e`.

It can be run with:

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m pytest tests\test_end_to_end_cli.py -m e2e

or together with other slow tests:

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m pytest tests -m slow

## Mass conventions

The refactor now distinguishes several mass conventions.

### `trapezoidal_mass`

This is the preferred diagnostic mass in the refactored code.

It uses the two-dimensional trapezoidal quadrature on the normalized height-DBH grid.

### `legacy_mass`

This reproduces the mass formula used in the original legacy script:

    dx * dy * np.sum(U[1:, 1:])

This convention is kept for regression comparisons with the original implementation.

### `total_mass`

This is the default mass diagnostic used by the refactored code.

Currently, `total_mass` is an alias for `trapezoidal_mass`.

Time series now include both:

- `total_mass`;
- `legacy_mass`.

## Quadrature utilities

Quadrature utilities have been centralized in:

    pydynamicforest/numerics.py

This includes:

- `trapezoidal_weights_2d`;
- `integrate_2d_trapezoidal`;
- `cumulative_integral_2d_trapezoidal`.

## Important limitation

The dense solver still uses the dense legacy linear algebra strategy:

    np.linalg.solve(A, b)

This reproduces the original implementation but is computationally expensive.

The sparse solver should now be preferred for practical simulations, while the dense solver remains useful as a regression reference on small cases.

Other current limitations include:

- quadrature conventions are clearer but still need further scientific review;
- legacy and diagnostic masses coexist for comparison purposes;
- plotting is functional but still provisional in terms of figure quality;
- recruitment is not yet implemented;
- alternative mortality laws are not yet implemented;
- alternative growth and status definitions remain to be explored;
- scenario management is still minimal.

## Tests

The current test suite checks:

- initial state construction;
- diagnostics;
- mass conventions;
- quadrature utilities;
- model field evaluation;
- derived numerical quantities;
- dense one-step solver;
- sparse one-step solver;
- short simulation loop;
- sparse simulation against dense simulation;
- structured exports;
- observation selection by stand age;
- observation export and loading;
- plotting utilities;
- automatic solver selection from numerical parameters;
- centralized baseline scenario configuration;
- editable packaging;
- console entry points;
- end-to-end command-line workflow;
- short legacy reference regression.

Tests can be run with:

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m pytest tests

Slow tests are excluded by default through `pytest.ini`.

To run only slow tests:

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m pytest tests -m slow

To run all tests, including slow tests:

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m pytest tests -m "slow or not slow"

## Scripts

The following scripts are currently available.

### Configurable baseline run

    pydf-run-baseline --max-steps 10 --output-dir outputs\baseline_short_cli

Full reduced baseline run:

    pydf-run-baseline --full --output-dir outputs\baseline_reduced_sparse_cli

Explicit dense override:

    pydf-run-baseline --max-steps 2 --solver-name dense --output-dir outputs\baseline_dense_debug

### Full reduced sparse run

    pydf-run-baseline-reduced-sparse

### Reduced reference comparison

    pydf-compare-reduced-reference

### Observation plotting

    pydf-plot-observations --input-dir outputs\baseline_reduced_sparse

### Observation comparison plotting

    pydf-plot-observation-comparisons --input-dir outputs\baseline_reduced_sparse

### Diagnostic plotting

    pydf-plot-diagnostics --input-file outputs\baseline_reduced_sparse\time_series.csv

## License

PyDynamicForest is distributed under the GNU Lesser General Public License v3.0 or later.

SPDX-License-Identifier: LGPL-3.0-or-later

## Next steps

Recommended next steps:

1. Continue improving observation export and plotting workflows.
2. Improve scenario configuration and possibly introduce external configuration files.
3. Further consolidate console entry points and CLI tests.
4. Further harmonize quadrature rules across diagnostics.
5. Clarify the scientific meaning of diagnostic mass in future outputs and figures.
6. Keep the dense solver available for regression checks on small cases.
7. Prepare future scientific extensions:
   - recruitment;
   - alternative mortality laws;
   - alternative growth functions;
   - alternative status definitions;
   - silvicultural or environmental scenarios.
8. Continue improving visualization quality in a dedicated future step.