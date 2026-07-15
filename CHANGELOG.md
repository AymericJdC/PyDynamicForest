# Changelog

All notable changes to PyDynamicForest will be documented in this file.

The project follows a pragmatic semantic versioning scheme during the research-code refactor phase.

## Unreleased

### Added

- Baseline configuration presets:
  - `baseline`;
  - `short-debug`;
  - `dense-debug`.
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
- Documentation of the distinction between:
  - the legacy code used for the initial manuscript submission;
  - the modular refactored implementation;
  - future model extension work.

### Changed

- The configurable baseline runner can now select presets and override selected configuration values from the command line.
- The solver now uses an intermediate model-field evaluation wrapper while preserving the legacy evaluation pathway by default.
- The state-aware model-field pathway is available for testing, but the default validated mode remains `"legacy"`.
- The development line now explicitly distinguishes:
  - legacy submission code;
  - validated technical refactor;
  - future extensions.

### Documentation

- Documented baseline presets and CLI overrides.
- Documented the state-aware model-field evaluation interface.
- Documented the configurable model-field evaluation mode.
- 