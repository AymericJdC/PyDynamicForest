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

and runs a short simulation using:

```python
results = simulate(x0, p, c, max_steps=10)
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

The reduced reference case is used for fast regression checks during refactoring.

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
- implements a short simulation loop;
- returns structured `SimulationResults`.

### Outputs

`pydynamicforest/outputs.py`

- exports time series to CSV;
- exports metadata to JSON;
- exports a human-readable summary.

## Important limitation

The current solver still uses the dense legacy linear algebra strategy:

```python
np.linalg.solve(A, b)
```

This reproduces the original implementation but is computationally expensive.

The full legacy configuration is therefore not suitable as a daily regression test.

The next numerical improvement will be to replace the dense assembly and solve by a sparse implementation.

## Tests

The current test suite checks:

- initial state construction;
- diagnostics;
- model field evaluation;
- derived numerical quantities;
- one-step solver;
- short simulation loop;
- structured exports.

Tests can be run with:

```bat
C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m pytest tests
```

## Next steps

Recommended next steps:

1. Compare the refactored short simulation with the reduced legacy reference.
2. Add explicit regression tests on selected scalar outputs.
3. Improve the output of the reduced legacy case for easier comparison.
4. Introduce a sparse matrix assembly and sparse linear solver.
5. Reduce unnecessary memory storage.
6. Harmonize quadrature rules across all diagnostics.
7. Replace hard-coded age or time indices by explicit age mapping utilities.
8. Add documentation to the main README.
