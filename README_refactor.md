# PyDynamicForest refactor notes

## Purpose

This document summarizes the ongoing refactor of the original `DynamicForestModel_2D.py` script.

The goal is to transform the initial research script into a structured, modular, maintainable and scientifically traceable codebase, while preserving the numerical and scientific behavior of the original implementation during the transition.

The current development line follows the stable refactor tag:

    v0.2.0-refactor

and continues as:

    0.3.0.dev0

The `v0.2.0-refactor` tag corresponds to a modular technical refactor preserving the numerical behavior of the original model. Subsequent development may prepare or introduce model extensions, but these should be clearly separated from the validated refactor milestone.

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

This structure is inspired by the conceptual organization previously used in C-STABILITY.

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
- `ModelFields`
- `TimeSeries`
- `SimulationResults`

The `ModelFields` object represents model coefficient fields evaluated on the numerical grid:

- diffusion;
- mortality;
- height growth;
- DBH growth;
- optional status field.

It prepares future model extensions in which coefficient fields may depend on the current state, derived quantities and the simulation context.

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

## Baseline scenario configuration

The baseline reduced scenario uses a centralized Python configuration file:

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

## Baseline presets

The baseline configuration layer provides presets.

Current presets are:

- `baseline`: default reduced baseline scenario;
- `short-debug`: lightweight sparse-solver debug scenario;
- `dense-debug`: lightweight dense-solver debug scenario.

They can be selected from the command line:

    pydf-run-baseline --preset baseline

    pydf-run-baseline --preset short-debug

    pydf-run-baseline --preset dense-debug

Internally, presets are built from:

    make_baseline_config()
    make_short_debug_config()
    make_dense_debug_config()
    build_baseline_config_from_preset(...)

Presets are generated from deep copies of `BASELINE_CONFIG`, so the default configuration is not mutated.

## Baseline CLI overrides

The configurable baseline runner supports command-line overrides for selected scenario configuration values.

Available overrides include:

    --nx
    --ny
    --n-steps
    --t-end
    --initial-age
    --final-age
    --observation-ages

For example:

    pydf-run-baseline --preset short-debug --nx 12 --ny 12 --max-steps 5 --output-dir outputs\short_debug_12x12

or:

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m scripts.run_baseline --preset short-debug --nx 12 --ny 12 --max-steps 5 --output-dir outputs\short_debug_12x12

These CLI overrides are applied to a deep copy of the selected preset.

## Configurable baseline run

The main baseline command-line script is:

    scripts/run_baseline.py

It can be used through the console entry point:

    pydf-run-baseline

or through the module form:

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m scripts.run_baseline

Examples:

    pydf-run-baseline --preset baseline --max-steps 10 --output-dir outputs\baseline_short_cli

    pydf-run-baseline --preset short-debug --output-dir outputs\short_debug

    pydf-run-baseline --preset dense-debug --max-steps 2 --output-dir outputs\dense_debug

By default, the solver is selected from the numerical parameters.

## Packaging

A minimal `pyproject.toml` file has been added.

The project can be installed in editable mode with:

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m pip install -e .

or with development dependencies:

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m pip install -e ".[dev]"

The packaging configuration includes:

- `pydynamicforest`;
- `simulations`;
- `scripts`.

## Console entry points

Console entry points are declared in `pyproject.toml`.

Available commands include:

    pydf-run-baseline
    pydf-run-baseline-reduced-sparse
    pydf-compare-reduced-reference
    pydf-plot-observations
    pydf-plot-observation-comparisons
    pydf-plot-diagnostics

These are wrappers around the corresponding script modules.

If the `pydf-*` commands are not found on Windows, check that the `Scripts` directory of the environment is available in the `PATH`.

## Solver selection

The simulation solver is selected from the numerical parameters by default.

The standard API is:

    results = simulate(x0, p, c)

The effective one-step solver is selected from:

    p.numerics.matrix_storage

Currently supported values are:

- `"dense"`: dense legacy-like solver;
- `"sparse"`: sparse legacy-like solver.

For the baseline reduced scenario:

    matrix_storage="sparse"
    linear_solver="scipy.sparse.linalg.spsolve"

For regression tests or debugging, the solver can still be explicitly overridden:

    results = simulate(x0, p, c, solver_name="dense")

or:

    results = simulate(x0, p, c, solver_name="sparse")

In addition to the dense/sparse solver choice, the numerical parameters now also include a model-field evaluation mode:

    model_field_evaluation="legacy"

The default value `"legacy"` preserves the validated legacy-compatible evaluation pathway. The alternative value `"state"` is intended for future development of state-aware model laws.

## Model field evaluation

The current code distinguishes several model-field evaluation layers.

### Legacy time-based interface

The legacy-compatible interface remains available:

    evaluate_model_fields(p, time=...)

or equivalently in the solver:

    evaluate_model_fields(p, t_current)

This interface preserves compatibility with the existing dense and sparse legacy-like solvers.

It is still the default pathway used by the solver, through the configurable solver-side wrapper described below.

### State-aware interface

A state-aware and context-aware model-field evaluation interface has been introduced:

    evaluate_state_model_fields(
        p,
        state,
        derived=None,
        context=None,
    )

This function returns a `ModelFields` object.

It prepares future model extensions where diffusion, mortality or growth laws may depend on:

- the current state `U`;
- derived quantities;
- the simulation context.

The interface is designed to support future laws with richer signatures such as:

    law.function(
        t,
        x,
        y,
        state=state,
        derived=derived,
        context=context,
        parameters=law.parameters,
    )

while remaining compatible with legacy laws of the form:

    law.function(t, x, y)

The state-aware interface is currently tested with coefficient laws depending on:

- the simulation context;
- global derived quantities such as `derived.total_mass`;
- local derived fields such as `derived.status_field`.

These tests are intentionally kept outside the baseline scenario. They validate the future extension mechanism without changing the scientific model currently used by the validated baseline and legacy-regression workflows.

### Solver-side model-field evaluation mode

A solver-side wrapper has been introduced:

    evaluate_model_fields_for_solver(
        state,
        p,
        context=None,
    )

This function centralizes the choice between the legacy and state-aware model-field evaluation pathways.

The choice is controlled by:

    p.numerics.model_field_evaluation

Currently supported values are:

- `"legacy"`: use the legacy time-based interface;
- `"state"`: use the state-aware interface.

The baseline configuration uses:

    model_field_evaluation="legacy"

Therefore, the validated numerical behavior remains unchanged by default.

The `"state"` mode is currently preparatory. It allows the solver infrastructure to be progressively migrated toward state-aware model laws, but should be used carefully because future dependencies on `U`, derived quantities or context may change the mathematical and numerical interpretation of the scheme.

Future state-dependent laws are expected to be introduced first as explicit dependencies on the current state `U^n`, before considering fully implicit nonlinear solves involving `U^{n+1}`.

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

The dense solver is retained as a regression reference on small cases.

## Observation management

In PyDynamicForest, observations are simulated model states selected for storage and analysis at requested stand ages.

They should not be confused with empirical field observations.

Observation ages are defined in the simulation context through the output specification:

    OutputSpecification(
        observation_ages=[18.0, 45.0, 69.0],
        save_full_trajectory=False,
    )

When `save_full_trajectory` is `False`, only states close to the requested stand ages are stored in `results.observations`.

## Observation exports

Selected observations are exported as `.npz` files under:

    outputs/<run_name>/observations/

Each `.npz` file contains:

- `U`;
- `time`;
- `age`;
- `step_index`;
- `height_grid`;
- `dbh_grid`;
- `height_grid_physical`;
- `dbh_grid_physical`.

## Plotting

`pydynamicforest/plotting.py` provides reusable plotting functions.

User-facing plotting commands include:

    pydf-plot-observations
    pydf-plot-observation-comparisons
    pydf-plot-diagnostics

The plotting workflow is functional but still provisional in terms of figure quality. A dedicated visualization-quality improvement step is planned for later.

## End-to-end CLI workflow test

An end-to-end command-line workflow test verifies the complete user-facing workflow:

1. run a configurable baseline simulation;
2. export time series, metadata, summary and observations;
3. plot individual observations;
4. plot observation comparison figures;
5. plot diagnostic time series.

The test is marked as both `slow` and `e2e`.

It can be run with:

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m pytest tests\test_end_to_end_cli.py -m e2e

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

- quadrature conventions still need further scientific review;
- legacy and diagnostic masses coexist for comparison purposes;
- plotting is functional but still provisional;
- recruitment is not yet implemented;
- alternative mortality laws are not yet implemented;
- alternative growth and status definitions remain to be explored;
- nonlinear dependencies on `U`, derived quantities or simulation context remain future model extensions;
- the current solver uses `model_field_evaluation="legacy"` by default;
- the `"state"` model-field evaluation mode is preparatory and is not yet the validated production pathway;
- the current solver does not yet implement nonlinear fixed-point or Newton iterations.

## Versioning strategy

The project uses Git tags to distinguish important scientific and technical states of the code.

Current and planned tags include:

- `v0.1.0-original`: original research script before the modular refactor;
- `v0.2.0-refactor`: modular technical refactor preserving the numerical behavior of the original model;
- `v1.0.0-submission`: future version used for manuscript submission.

The `legacy/` directory is currently kept for reproducibility and regression testing.

The current development branch follows `v0.2.0-refactor` and uses version:

    0.3.0.dev0

Future versions may introduce explicit model extensions, such as nonlinear dependencies on the state variable `U`, derived quantities or the simulation context.

## License

PyDynamicForest is distributed under the GNU Lesser General Public License v3.0 or later.

SPDX-License-Identifier: LGPL-3.0-or-later

## Next steps

Recommended next steps:

1. Continue improving scenario configuration.
2. Keep the legacy time-based solver path stable until state-aware evaluation is fully validated.
3. Prepare a controlled migration of the solver toward `evaluate_state_model_fields`.
4. Further consolidate CLI workflows.
5. Further harmonize quadrature rules across diagnostics.
6. Clarify the scientific meaning of diagnostic mass in future outputs and figures.
7. Prepare future scientific extensions:
   - recruitment;
   - alternative mortality laws;
   - alternative growth functions;
   - alternative status definitions;
   - nonlinear dependencies on `U`, derived quantities or simulation context.
8. Continue improving visualization quality in a dedicated future step.