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

---

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

---

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

---

## Current package structure

    pydynamicforest/
    ├── __init__.py
    ├── types.py
    ├── initial_conditions.py
    ├── model.py
    ├── numerics.py
    ├── solver.py
    ├── diagnostics.py
    └── outputs.py

    simulations/
    └── baseline/
        ├── __init__.py
        ├── initial_condition.py
        ├── parameters.py
        ├── context.py
        └── run.py

    scripts/
    ├── __init__.py
    ├── run_baseline_reduced_sparse.py
    └── compare_reduced_reference.py

    legacy/
    ├── DynamicForestModel_2D_legacy.py
    ├── DynamicForestModel_2D_reduced_reference.py
    └── DynamicForestModel_2D_short_reference.py

    tests/
    reference_outputs/
    outputs/

---

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
        solver_name="sparse",
    )

The baseline scenario separates:

- the initial condition in `initial_condition.py`;
- model and numerical parameters in `parameters.py`;
- simulation context and requested observations in `context.py`;
- the runnable scenario in `run.py`.

---

## Legacy reference

The original script has been preserved in:

    legacy/DynamicForestModel_2D_legacy.py

A reduced reference case has also been created:

    legacy/DynamicForestModel_2D_reduced_reference.py

A short reference case has been created for fast regression checks:

    legacy/DynamicForestModel_2D_short_reference.py

The reduced and short reference cases are used to compare the refactored implementation against the original legacy numerical behavior.

---

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
- returns structured `SimulationResults`.

The high-level simulation API is:

    results = simulate(
        x0,
        p,
        c,
        max_steps=None,
        solver_name="sparse",
    )

Available solver names are currently:

- `"dense"`: dense legacy-like solver using `numpy.linalg.solve`;
- `"sparse"`: sparse legacy-like solver using `scipy.sparse`.

### Outputs

`pydynamicforest/outputs.py`

- exports time series to CSV;
- exports metadata to JSON;
- exports a human-readable summary;
- records saved observations in metadata and summary files.

---

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

---

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

---

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

This distinction is important because legacy regression tests should use `legacy_mass`, whereas scientific diagnostics should preferably use `trapezoidal_mass` or `total_mass`.

Time series now include both:

- `total_mass`;
- `legacy_mass`.

This makes exported results easier to compare with the legacy implementation while preserving a cleaner diagnostic convention.

---

## Quadrature utilities

Quadrature utilities have been centralized in:

    pydynamicforest/numerics.py

This includes:

- `trapezoidal_weights_2d`;
- `integrate_2d_trapezoidal`;
- `cumulative_integral_2d_trapezoidal`.

This avoids duplicating quadrature logic across initial condition construction and diagnostics.

The current preferred convention for scientific diagnostics is the 2D trapezoidal rule.

---

## Important limitation

The dense solver still uses the dense legacy linear algebra strategy:

    np.linalg.solve(A, b)

This reproduces the original implementation but is computationally expensive.

The sparse solver should now be preferred for practical simulations, while the dense solver remains useful as a regression reference on small cases.

Other current limitations include:

- quadrature conventions are clearer but still need further scientific review;
- legacy and diagnostic masses coexist for comparison purposes;
- recruitment is not yet implemented;
- alternative mortality laws are not yet implemented;
- alternative growth and status definitions remain to be explored;
- scenario management is still minimal.

---

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
- short legacy reference regression.

Tests can be run with:

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m pytest tests

Slow tests are excluded by default through `pytest.ini`.

To run only slow tests:

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m pytest tests -m slow

To run all tests, including slow tests:

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m pytest tests -m "slow or not slow"

---

## Slow regression test

A slow regression test has been added for the reduced sparse reference case.

It runs the full reduced baseline simulation with:

    Nx = 20
    Ny = 20
    Nt = 1000
    solver = sparse

and compares the outputs against the reduced legacy reference.

This test is marked with:

    @pytest.mark.slow

and is therefore not run by default.

---

## Scripts

The following scripts are currently available.

### Short baseline run

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m simulations.baseline.run

This runs a short baseline simulation using the sparse solver, typically with:

    max_steps=10
    solver_name="sparse"

### Full reduced sparse run

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m scripts.run_baseline_reduced_sparse

This runs the full reduced baseline case:

    Nx = 20
    Ny = 20
    Nt = 1000
    solver = sparse

and exports results to:

    outputs/baseline_reduced_sparse/

### Reduced reference comparison

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m scripts.compare_reduced_reference

This compares the refactored sparse solver against:

    reference_outputs/legacy_reduced_console_output.txt

The comparison currently checks:

- final top height;
- final basal area;
- final legacy mass;
- minimum density over the trajectory.

---

## Environment and reproducibility

The Python dependencies are documented in two files:

    requirements.txt
    environment.yml

The conda environment can be recreated with:

    conda env create -f environment.yml
    conda activate pydynamicforest

The package currently depends on:

- numpy;
- scipy;
- matplotlib;
- pytest.

---

## Useful commands

A full command reference is available in:

    COMMANDS.md

Run the full fast test suite:

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m pytest tests

Run the short baseline scenario:

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m simulations.baseline.run

Run the full reduced sparse baseline:

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m scripts.run_baseline_reduced_sparse

Compare the sparse refactored solver with the reduced legacy reference:

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m scripts.compare_reduced_reference

---

## Current validation status

The sparse solver reproduces the reduced legacy reference case up to numerical precision for the main scalar outputs:

- final top height;
- final basal area;
- final legacy mass;
- minimum density over the trajectory.

For the reduced reference case, the observed discrepancies are at or near machine precision.

---

## Documentation files

The current documentation files are:

- `README.md`: user-facing project introduction;
- `README_refactor.md`: technical and conceptual refactor notes;
- `COMMANDS.md`: command reference for development, tests, scripts and troubleshooting.

---

## Next steps

Recommended next steps:

1. Review whether the reduced full sparse comparison should remain both a manual script and an optional slow regression test.
2. Continue improving observation export, possibly by exporting selected observed states as `.npz` files.
3. Further harmonize quadrature rules across diagnostics.
4. Clarify the scientific meaning of diagnostic mass in future outputs and figures.
5. Make `sparse` the default solver for practical simulations.
6. Keep the dense solver available for regression checks on small cases.
7. Improve the main user-facing `README.md`.
8. Prepare future scientific extensions:
   - recruitment;
   - alternative mortality laws;
   - alternative growth functions;
   - alternative status definitions;
   - silvicultural or environmental scenarios.
9. Consider adding configuration files for scenarios.
10. Consider packaging the project as an installable Python package.