# Changelog

All notable changes to PyDynamicForest will be documented in this file.

The project follows a pragmatic semantic versioning scheme during the research-code refactor phase.

## Unreleased

### Added

- Baseline configuration presets:
  - `baseline`;
  - `short-debug`;
  - `dense-debug`;
  - `state-debug`.
- Command-line preset selection through:

      pydf-run-baseline --preset

- Command-line baseline configuration overrides:
  - `--nx`;
  - `--ny`;
  - `--n-steps`;
  - `--t-end`;
  - `--initial-age`;
  - `--final-age`;
  - `--observation-ages`;
  - `--model-field-evaluation`.
- `ModelFields` type for model coefficient fields evaluated on the numerical grid.
- Solver model-field access adapter:

      get_model_field(fields, name)

- Explicit conversion helper:

      model_fields_to_legacy_dict(fields)

- State-aware model-field evaluation interface:

      evaluate_state_model_fields(...)

- Solver-side model-field evaluation wrapper:

      evaluate_model_fields_for_solver(...)

- Numerical parameter `model_field_evaluation` with supported values:
  - `"legacy"`;
  - `"state"`.
- Tests for context-dependent coefficient laws.
- Tests for derived-dependent coefficient laws.
- Tests comparing legacy and state model-field evaluation modes for the current baseline laws.
- Tests comparing short simulations run with legacy and state model-field evaluation modes.
- Tests for solver model-field adapters supporting both dictionary-based fields and `ModelFields`.
- Archived manuscript-associated legacy script:

      legacy/article_submission/Modele2DImpliciteV3.py

- Documentation of the distinction between:
  - the legacy code associated with the initial manuscript submission;
  - the modular refactored implementation;
  - future model extension work.

### Changed

- The configurable baseline runner can now select presets and override selected configuration values from the command line.
- The solver now uses an intermediate model-field evaluation wrapper while preserving the legacy evaluation pathway by default.
- The solver can now access model coefficient fields through `get_model_field(...)`, allowing it to handle both dictionary-based fields and `ModelFields`.
- In `model_field_evaluation="legacy"` mode, `evaluate_model_fields_for_solver(...)` returns the historical dictionary-based field representation.
- In `model_field_evaluation="state"` mode, `evaluate_model_fields_for_solver(...)` now returns a `ModelFields` object.
- The state-aware model-field pathway is available for testing, but the default validated mode remains `"legacy"`.
- The development line now explicitly distinguishes:
  - legacy submission-associated code;
  - validated technical refactor;
  - future extensions.

### Documentation

- Documented baseline presets and CLI overrides.
- Documented the state-aware model-field evaluation interface.
- Documented the configurable model-field evaluation mode.
- Documented the solver field adapter `get_model_field(...)`.
- Documented that solver-side `"legacy"` and `"state"` modes preserve their respective field formats.
- Documented the equivalence tests between legacy and state model-field evaluation modes.
- Documented the short simulation comparison between legacy and state model-field evaluation modes.
- Documented the archived legacy script associated with the initially submitted manuscript.
- Clarified that the manuscript associated with this codebase was initially submitted to the Journal of Mathematical Biology using a legacy Python implementation.
- Clarified that the current refactored code is a modular technical reimplementation validated against reduced legacy reference cases, not the exact code version used for the initial manuscript submission unless explicitly stated by a dedicated tag or release.

### Notes

The manuscript associated with this codebase was initially submitted to the Journal of Mathematical Biology using a legacy Python implementation.

A legacy script associated with the numerical simulations reported in the initially submitted manuscript is archived in:

    legacy/article_submission/Modele2DImpliciteV3.py

This archived script is kept for traceability. It is not part of the refactored `pydynamicforest` package and should not be modified directly.

The current refactored code is a modular technical reimplementation validated against reduced legacy reference cases. It should not be interpreted as the exact code version used for the initial manuscript submission unless explicitly stated by a dedicated tag or release.

A specific traceability tag for the legacy code associated with the initial manuscript submission may be introduced later if the exact corresponding commit is confirmed and if such a tag is useful.

## v0.2.0-refactor

### Added

- Modular package structure under `pydynamicforest/`.
- Structured API based on:

      simulate(x0, p, c)

- Dataclasses for initial conditions, parameters, context, states, time series and simulation results.
- Dense legacy-like one-step solver.
- Sparse legacy-like one-step solver.
- Automatic solver selection from numerical parameters.
- Baseline scenario configuration in:

      simulations/baseline/config.py

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
- Baseline scenario values are centralized in:

      simulations/baseline/config.py

- Snapshot terminology has been replaced by observation terminology.
- Mass conventions have been clarified:
  - `trapezoidal_mass`;
  - `legacy_mass`;
  - `total_mass`.

### Kept for reproducibility

- Legacy scripts are kept under:

      legacy/

- Reduced legacy reference outputs are kept under:

      reference_outputs/

- Regression scripts and slow tests compare the refactored sparse solver with the reduced legacy reference.

### Scientific status

This version is a modular technical refactor preserving the numerical behavior of the reduced legacy reference case.

It is not the exact version used for the initial manuscript submission to the Journal of Mathematical Biology. The initial manuscript submission used the legacy Python implementation.

## Version tags

### `v0.1.0-original`

Original legacy implementation before modular refactor.

This tag is intended to point to the original code state before the refactor branch.

### `v0.2.0-refactor`

Modular technical refactor preserving the numerical behavior of the reduced legacy reference case.

This version is intended to remain scientifically equivalent to the validated legacy reference cases, while improving modularity, maintainability, testing and extensibility.

### Possible future traceability tags

A specific tag may be introduced later to identify the exact legacy commit associated with the initial manuscript submission, if needed and if the corresponding commit is confirmed.

No final article or accepted-version tag is currently defined.