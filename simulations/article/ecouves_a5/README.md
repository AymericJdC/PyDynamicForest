# Q-9E.1 modules

`inventory.py` reads and normalizes the individual and aggregate workbooks, evaluates inclusion rules, reconciles inventories and detects anomalies. `stand_metrics.py` contains unit-explicit dendrometric functions. The package is independent of any height model.

## Q-9E.2

The height interface is split into typed domain objects, generic providers, non-mutating validation, weighted diagnostics, a Q-9E.1 adapter and stable CSV export. See `docs/article/q9e2_height_provider_interface.md`.

## Q-9E.3

`savine_height_provider.py` implements the provisional even-aged Douglas fixed-effect relation from supplementary Table S5. `height_reconstruction.py` orchestrates validation and diagnostics without calibration or randomization.

## Q-9E.4

`grid_projection.py` implements compact conservative bilinear regularisation onto tensor-grid nodes. Mass and first moments are conserved under trapezoidal quadrature; non-conserved diagnostics remain explicit.

## Q-9E.5

`pydynamicforest_adapter.py` converts conservative Q-9E.4 nodal masses to the native normalized `(height, DBH)` solver state. `state_compatibility.py` checks mass, moments, units, axes and observation operators without advancing the model.

## Q-9F.1

`short_dynamic_control.py` performs a few sparse legacy steps from the reconstructed 1992 native state and reports numerical stability without calibration.

## Q-9F.2

`main_dynamic_trajectory.py` advances the reconstructed 1992 native state to 2020 with unchanged dynamics and compares it with independently reconstructed 1998, 2016 and 2020 states.

## Q-9F.3

`distributional_diagnostics.py` compares simulated and reconstructed DBH/height marginals, quantiles, joint dependence and slenderness without calibration.

## Q-9F.4

`mechanistic_sensitivity.py` performs a centred OAT screening of growth, diffusion and mortality mechanisms from the fixed reconstructed 1992 state, without calibration.

## Q-9F.5

`hierarchical_height_diagnostics.py` localises vertical discrepancies across state-specific relative-DBH hierarchy classes without calibration.

## Q-9F.6

`height_growth_allocation_audit.py` separates the global height-growth field from the implemented joint-cumulative status allocation without simulating an alternative law.

## Q-9F.7

`status_shape_sensitivity.py` applies `S^gamma` only to height transport, with gamma 1 as an exact solver non-regression control and no calibration.
