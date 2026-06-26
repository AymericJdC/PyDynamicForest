# PyDynamicForest refactor notes

## Purpose

This document summarizes the ongoing refactor of the original `DynamicForestModel_2D.py` script.

The goal is to transform the initial research script into a more structured, modular and maintainable scientific code, while preserving the numerical and scientific behavior of the original implementation during the transition.

The refactor follows a progressive strategy:

1. preserve the original legacy script;
2. create a reduced reference case;
3. introduce conceptual objects;
4. separate initial conditions, model laws, numerical routines, diagnostics, solver and outputs;
5. progressively improve the numerical implementation.

## Conceptual architecture

The target conceptual API is:

```python
results = simulate(x0, p, c)
```

where:

- `x0` is an `InitialCondition`;
- `p` is a `Parameters` object;
- `c` is a `SimulationContext`;
- `results` is a `SimulationResults` object.

The object `Parameters` separates:

- `ModelParameters`: scientific and mathematical model assumptions;
- `NumericalParameters`: grid, time discretization, numerical scheme and solver choices.

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

```text
pydynamicforest/
├── __init__.py
├── types.py
├── initial_conditions.py
├── model.py
├── numerics.py
├── solver.py
├── diagnostics.py
└── outputs.py
```

## Scenario structure

A baseline reduced scenario has been introduced in:

```text
simulations/baseline/
├── __init__.py
├── initial_condition.py
├── parameters.py
├── context.py
└── run.py
```

This scenario defines:

```python
x0 = build_initial_condition()
p = build_parameters()
c = build_context()
```

and runs a short sparse simulation using:

```python
results = simulate(
    x0,
    p,
    c,
    max_steps=10,
    solver_name="sparse",
)
```

## Legacy reference

The original script has been preserved in:

```text
legacy/DynamicForestModel_2D_legacy.py
```

A reduced reference case has also been created:

```text
legacy/DynamicForestModel_2D_reduced_reference.py
```

A short reference case has been created for fast regression checks:

```text
legacy/DynamicForestModel_2D_short_reference.py
```

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
- top height;
- basal area;
- minimum density;
- marginal height distribution;
- marginal DBH distribution.

### Numerical derived quantities

`pydynamicforest/numerics.py`

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
- returns structured `SimulationResults`.

The high-level simulation API is:

```python
results = simulate(
    x0,
    p,
    c,
    max_steps=None,
    solver_name="sparse",
)
```

Available solver names are currently:

- `"dense"`: dense legacy-like solver using `numpy.linalg.solve`;
- `"sparse"`: sparse legacy-like solver using `scipy.sparse`.

### Outputs

`pydynamicforest/outputs.py`

- exports time series to CSV;
- exports metadata to JSON;
- exports a human-readable summary.

## Sparse solver validation

A sparse version of the legacy one-step solver has been implemented.

It has been validated against:

1. the dense refactored one-step solver;
2. the dense refactored short simulation;
3. the reduced legacy full reference case.

For the reduced reference case:

```text
Nx = 20
Ny = 20
Nt = 1000
solver = sparse
```

The sparse solver reproduces the reduced legacy reference up to numerical precision for the main scalar outputs:

- final top height;
- final basal area;
- final legacy mass;
- minimum density over the trajectory.

The reduced sparse case currently runs in approximately 9 seconds on the working machine.

## Important limitation

The dense solver still uses the dense legacy linear algebra strategy:

```python
np.linalg.solve(A, b)
```

This reproduces the original implementation but is computationally expensive.

The sparse solver should now be preferred for practical simulations, while the dense solver remains useful as a regression reference on small cases.

## Tests

The current test suite checks:

- initial state construction;
- diagnostics;
- model field evaluation;
- derived numerical quantities;
- dense one-step solver;
- sparse one-step solver;
- short simulation loop;
- sparse simulation against dense simulation;
- structured exports;
- short legacy reference regression.

Tests can be run with:

```bat
C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m pytest tests
```

## Scripts

The following scripts are currently available.

### Short baseline run

```bat
C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m simulations.baseline.run
```

This runs a short baseline simulation using the sparse solver, typically with:

```python
max_steps=10
solver_name="sparse"
```

### Full reduced sparse run

```bat
C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m scripts.run_baseline_reduced_sparse
```

This runs the full reduced baseline case:

```text
Nx = 20
Ny = 20
Nt = 1000
solver = sparse
```

and exports results to:

```text
outputs/baseline_reduced_sparse/
```

### Reduced reference comparison

```bat
C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m scripts.compare_reduced_reference
```

This compares the refactored sparse solver against:

```text
reference_outputs/legacy_reduced_console_output.txt
```

The comparison currently checks:

- final top height;
- final basal area;
- final legacy mass;
- minimum density over the trajectory.

## Environment and reproducibility

The Python dependencies are documented in two files:

```text
requirements.txt
environment.yml
```

The conda environment can be recreated with:

```bat
conda env create -f environment.yml
conda activate pydynamicforest
```

The package currently depends on:

- numpy
- scipy
- matplotlib
- pytest

## Useful commands

Run the full test suite:

```bat
C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m pytest tests
```

Run the short baseline scenario:

```bat
C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m simulations.baseline.run
```

Run the full reduced sparse baseline:

```bat
C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m scripts.run_baseline_reduced_sparse
```

Compare the sparse refactored solver with the reduced legacy reference:

```bat
C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m scripts.compare_reduced_reference
```

## Current validation status

The sparse solver reproduces the reduced legacy reference case up to numerical precision for the main scalar outputs:

- final top height;
- final basal area;
- final legacy mass;
- minimum density over the trajectory.

For the reduced reference case, the observed discrepancies are at or near machine precision.

## Next steps

Recommended next steps:

1. Add a pytest marker for long or slow tests.
2. Decide whether the reduced full sparse comparison should remain a manual script or become an optional regression test.
3. Improve snapshot management using `OutputSpecification.snapshot_ages`.
4. Avoid storing the full trajectory by default when only selected snapshots are needed.
5. Harmonize quadrature rules across diagnostics.
6. Clarify the distinction between:
   - legacy mass;
   - trapezoidal mass;
   - scientific diagnostic mass.
7. Make `sparse` the default solver for practical simulations.
8. Keep the dense solver available for regression checks on small cases.
9. Add more user-facing documentation to the main `README.md`.
10. Prepare future scientific extensions:
    - recruitment;
    - alternative mortality laws;
    - alternative growth functions;
    - alternative status definitions;
    - silvicultural or environmental scenarios.
