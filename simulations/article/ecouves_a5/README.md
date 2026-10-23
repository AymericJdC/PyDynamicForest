# Q-9E.1 modules

`inventory.py` reads and normalizes the individual and aggregate workbooks, evaluates inclusion rules, reconciles inventories and detects anomalies. `stand_metrics.py` contains unit-explicit dendrometric functions. The package is independent of any height model.

## Q-9E.2

The height interface is split into typed domain objects, generic providers, non-mutating validation, weighted diagnostics, a Q-9E.1 adapter and stable CSV export. See `docs/article/q9e2_height_provider_interface.md`.

## Q-9E.3

`savine_height_provider.py` implements the provisional even-aged Douglas fixed-effect relation from supplementary Table S5. `height_reconstruction.py` orchestrates validation and diagnostics without calibration or randomization.
