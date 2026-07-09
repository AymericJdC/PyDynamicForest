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

The builders can also accept an optional configuration dictionary, for example:

    config = copy_baseline_config()
    config["grid"]["nx"] = 10
    config["grid"]["ny"] = 10

    x0 = build_initial_condition(config)
    p = build_parameters(config)
    c = build_context(config)

This enables lightweight scenario variants without duplicating the baseline files.

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

## Baseline CLI overrides

The configurable baseline runner now supports command-line overrides for selected scenario configuration values.

Available overrides include:

    --nx
    --ny
    --n-steps
    --t-end
    --initial-age
    --final-age
    --observation-ages

For example:

    pydf-run-baseline --nx 10 --ny 10 --n-steps 20 --max-steps 5 --output-dir outputs\cli_small_grid

This temporarily overrides the grid size and time discretization for the current run only.

Custom observation ages can be requested with:

    pydf-run-baseline --max-steps 5 --observation-ages 18 20 25 --output-dir outputs\cli_custom_observations

The same options are available through the developer-style module command:

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m scripts.run_baseline --nx 10 --ny 10 --n-steps 20 --max-steps 5 --output-dir outputs\cli_small_grid

These CLI overrides are applied to a deep copy of `BASELINE_CONFIG`, so the default configuration file is not modified.

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

## Solver selection

The simulation solver is selected from the numerical parameters by default.

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

## Observation exports

Selected observations are exported as `.npz` files under:

    outputs/<run_name>/observations/

Each `.npz` file contains:

- `U`: simulated density field;
- `time`: simulation time;
- `age`: stand age;
- `step_index`: numerical time-step index;
- `height_grid`: normalized height grid;
- `dbh_grid`: normalized DBH grid;
- `height_grid_physical`: height grid in physical units;
- `dbh_grid_physical`: DBH grid in physical units.

## Plotting

`pydynamicforest/plotting.py` provides reusable plotting functions.

User-facing plotting scripts include:

    pydf-plot-observations
    pydf-plot-observation-comparisons
    pydf-plot-diagnostics

The current plotting workflow is functional but still provisional in terms of figure quality. A dedicated visualization-quality improvement step is planned for later.

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

The refactor distinguishes several mass conventions:

- `trapezoidal_mass`;
- `legacy_mass`;
- `total_mass`.

The `legacy_mass` convention is kept for regression comparisons with the original implementation.

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

Other current limitations include:

- quadrature conventions are clearer but still need further scientific review;
- legacy and diagnostic masses coexist for comparison purposes;
- plotting is functional but still provisional in terms of figure quality;
- recruitment is not yet implemented;
- alternative mortality laws are not yet implemented;
- alternative growth and status definitions remain to be explored.

## Versioning strategy

The project uses Git tags to distinguish important scientific and technical states of the code.

Planned tags include:

- `v0.1.0-original`: original research script developed before the modular refactor;
- `v0.2.0-refactor`: modular technical refactor preserving the numerical behavior of the original model;
- `v1.0.0-submission`: version used for manuscript submission.

The `legacy/` directory is currently kept for reproducibility and regression testing.

The current refactor version is intended to remain scientifically equivalent to the original model. Future versions may introduce explicit model extensions, such as nonlinear dependencies on the state variable `U` or on derived quantities.

## License

PyDynamicForest is distributed under the GNU Lesser General Public License v3.0 or later.

SPDX-License-Identifier: LGPL-3.0-or-later

## Next steps

Recommended next steps:

1. Continue improving scenario configuration.
2. Consider external configuration files later if needed.
3. Further consolidate CLI workflows.
4. Further harmonize quadrature rules across diagnostics.
5. Clarify the scientific meaning of diagnostic mass in future outputs and figures.
6. Prepare future scientific extensions:
   - recruitment;
   - alternative mortality laws;
   - alternative growth functions;
   - alternative status definitions;
   - nonlinear dependencies on `U` or derived quantities.
7. Continue improving visualization quality in a dedicated future step.