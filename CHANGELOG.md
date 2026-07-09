# Changelog

All notable changes to PyDynamicForest will be documented in this file.

The project follows a pragmatic semantic versioning scheme during the research-code refactor phase.

## Unreleased

### Added

- Modular package structure under `pydynamicforest/`.
- Structured API based on `simulate(x0, p, c)`.
- Dataclasses for initial conditions, parameters, context, states, time series and simulation results.
- Dense legacy-like one-step solver.
- Sparse legacy-like one-step solver.
- Automatic solver selection from numerical parameters.
- Baseline scenario configuration in `simulations/baseline/config.py`.
- Configurable baseline command-line script.
- CSV, JSON, TXT and NPZ result exports.
- Model observations selected by stand age.
- Observation loading utilities.
- Plotting utilities for observations, observation comparisons and diagnostic time series.
- End-to-end CLI workflow test.
- Slow regression test against the reduced legacy reference.
- Editable Python packaging through `pyproject.toml`.
- Console entry points prefixed by `pydf-`.
- LGPL-3.0-or-later license.
- SPDX headers in active Python source files.

### Changed

- The baseline reduced scenario now uses the sparse legacy-like solver by default.
- The solver is selected from `p.numerics.matrix_storage` unless explicitly overridden.
- Baseline scenario values are centralized in `simulations/baseline/config.py`.
- Snapshot terminology has been replaced by observation terminology.
- Mass conventions have been clarified:
  - `trapezoidal_mass`;
  - `legacy_mass`;
  - `total_mass`.

### Kept for reproducibility

- Legacy scripts are kept under `legacy/`.
- Reduced legacy reference outputs are kept under `reference_outputs/`.
- Regression scripts and slow tests compare the refactored sparse solver with the reduced legacy reference.

## Planned tags

### `v0.1.0-original`

Original research script before modular refactor.

This tag is intended to point to the last commit of `main` before the refactor branch.

### `v0.2.0-refactor`

Modular technical refactor preserving the numerical behavior of the original model.

This version is intended to remain scientifically equivalent to the original model.

### `v1.0.0-submission`

Version used for manuscript submission.