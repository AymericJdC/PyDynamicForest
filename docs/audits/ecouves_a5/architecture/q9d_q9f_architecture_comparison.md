# Q-9D versus Q-9F architectural comparison - initial static audit

Date: 2026-10-23T16:49:47+02:00  
Branch: `feature/observation-quadrature`  
HEAD: `8ad8ae177514e55d7bff97da852f13142c33adff`

## Scope

This is a static, read-only comparison. It does not run tests or simulations and does not propose moving files yet.

## Git status

```text
?? compare_q9d_q9f_architectures.py
?? q9d_q9f_architecture_components.csv
```

## Inventory

- Q-9D components: 9
- Q-9E/Q-9F Python components: 35
- Total: 44

Detailed inventory: `q9d_q9f_architecture_components.csv`.

## Feature map

### initial_state_U0: shared candidate

Q-9D:
- `simulations/article/copula_initial_condition.py`
- `simulations/article/initial_state_sensitivity.py`
- `simulations/article/q9d_full_run.py`
- `simulations/article/scenarios.py`
Q-9E/Q-9F:
- `scripts/article/diagnose_ecouves_a5_status_shape_mass_balance.py`
- `scripts/article/run_ecouves_a5_main_trajectory.py`
- `scripts/article/run_ecouves_a5_mechanistic_sensitivity.py`
- `scripts/article/run_ecouves_a5_short_dynamic_control.py`
- `scripts/article/run_ecouves_a5_status_shape_sensitivity.py`
- `scripts/article/validate_ecouves_a5_initial_states.py`
- `simulations/article/ecouves_a5/distributional_diagnostics.py`
- `simulations/article/ecouves_a5/height_growth_allocation_audit.py`
- `simulations/article/ecouves_a5/hierarchical_height_diagnostics.py`
- `simulations/article/ecouves_a5/main_dynamic_trajectory.py`
- `simulations/article/ecouves_a5/mechanistic_sensitivity.py`
- `simulations/article/ecouves_a5/pydynamicforest_adapter.py`
- `simulations/article/ecouves_a5/short_dynamic_control.py`
- `simulations/article/ecouves_a5/state_compatibility.py`
- `simulations/article/ecouves_a5/status_shape_mass_balance.py`
- `simulations/article/ecouves_a5/status_shape_sensitivity.py`

### output_isolation: shared candidate

Q-9D:
- `simulations/article/analyze_dynamic_sensitivity.py`
- `simulations/article/compare_q9d_rho.py`
- `simulations/article/q9d_full_run.py`
- `simulations/article/run_dynamic_sensitivity.py`
- `simulations/article/run_q9d_scenarios.py`
Q-9E/Q-9F:
- `scripts/article/audit_ecouves_a5.py`
- `scripts/article/audit_ecouves_a5_height_growth_allocation.py`
- `scripts/article/diagnose_ecouves_a5_distributions.py`
- `scripts/article/diagnose_ecouves_a5_height_hierarchy.py`
- `scripts/article/diagnose_ecouves_a5_status_shape_mass_balance.py`
- `scripts/article/project_ecouves_a5_heights_to_grid.py`
- `scripts/article/reconstruct_ecouves_a5_heights.py`
- `scripts/article/run_ecouves_a5_main_trajectory.py`
- `scripts/article/run_ecouves_a5_mechanistic_sensitivity.py`
- `scripts/article/run_ecouves_a5_short_dynamic_control.py`
- `scripts/article/run_ecouves_a5_status_shape_sensitivity.py`
- `scripts/article/validate_ecouves_a5_initial_states.py`
- `simulations/article/ecouves_a5/height_export.py`
- `simulations/article/ecouves_a5/inventory.py`

### overwrite_guard: Q-9D only

Q-9D:
- `simulations/article/q9d_full_run.py`
- `simulations/article/run_dynamic_sensitivity.py`
- `simulations/article/run_q9d_scenarios.py`

### configuration_manifest: Q-9D only

Q-9D:
- `simulations/article/q9d_full_run.py`

### reproducibility_metadata: Q-9D only

Q-9D:
- `simulations/article/q9d_full_run.py`

### observation_operators: shared candidate

Q-9D:
- `simulations/article/analyze_dynamic_sensitivity.py`
- `simulations/article/compare_q9d_rho.py`
- `simulations/article/copula_initial_condition.py`
- `simulations/article/initial_state_sensitivity.py`
- `simulations/article/q9d_full_run.py`
- `simulations/article/scenarios.py`
Q-9E/Q-9F:
- `scripts/article/reconstruct_ecouves_a5_heights.py`
- `simulations/article/ecouves_a5/__init__.py`
- `simulations/article/ecouves_a5/distributional_diagnostics.py`
- `simulations/article/ecouves_a5/height_growth_allocation_audit.py`
- `simulations/article/ecouves_a5/height_providers.py`
- `simulations/article/ecouves_a5/hierarchical_height_diagnostics.py`
- `simulations/article/ecouves_a5/inventory.py`
- `simulations/article/ecouves_a5/main_dynamic_trajectory.py`
- `simulations/article/ecouves_a5/mechanistic_sensitivity.py`
- `simulations/article/ecouves_a5/pydynamicforest_adapter.py`
- `simulations/article/ecouves_a5/savine_height_provider.py`
- `simulations/article/ecouves_a5/short_dynamic_control.py`
- `simulations/article/ecouves_a5/state_compatibility.py`
- `simulations/article/ecouves_a5/status_shape_mass_balance.py`
- `simulations/article/ecouves_a5/status_shape_sensitivity.py`

### state_validation: shared candidate

Q-9D:
- `simulations/article/copula_initial_condition.py`
- `simulations/article/q9d_full_run.py`
- `simulations/article/scenarios.py`
Q-9E/Q-9F:
- `scripts/article/diagnose_ecouves_a5_distributions.py`
- `scripts/article/diagnose_ecouves_a5_status_shape_mass_balance.py`
- `scripts/article/project_ecouves_a5_heights_to_grid.py`
- `scripts/article/run_ecouves_a5_status_shape_sensitivity.py`
- `scripts/article/validate_ecouves_a5_initial_states.py`
- `simulations/article/ecouves_a5/__init__.py`
- `simulations/article/ecouves_a5/distributional_diagnostics.py`
- `simulations/article/ecouves_a5/grid_projection.py`
- `simulations/article/ecouves_a5/height_diagnostics.py`
- `simulations/article/ecouves_a5/height_growth_allocation_audit.py`
- `simulations/article/ecouves_a5/height_types.py`
- `simulations/article/ecouves_a5/height_validation.py`
- `simulations/article/ecouves_a5/hierarchical_height_diagnostics.py`
- `simulations/article/ecouves_a5/pydynamicforest_adapter.py`
- `simulations/article/ecouves_a5/savine_height_provider.py`
- `simulations/article/ecouves_a5/short_dynamic_control.py`
- `simulations/article/ecouves_a5/state_compatibility.py`
- `simulations/article/ecouves_a5/status_shape_mass_balance.py`
- `simulations/article/ecouves_a5/status_shape_sensitivity.py`

### horizon_validation: shared candidate

Q-9D:
- `simulations/article/analyze_dynamic_sensitivity.py`
- `simulations/article/q9d_full_run.py`
- `simulations/article/run_dynamic_sensitivity.py`
- `simulations/article/run_q9d_scenarios.py`
- `simulations/article/scenarios.py`
Q-9E/Q-9F:
- `scripts/article/diagnose_ecouves_a5_status_shape_mass_balance.py`
- `scripts/article/run_ecouves_a5_main_trajectory.py`
- `scripts/article/run_ecouves_a5_short_dynamic_control.py`
- `simulations/article/ecouves_a5/main_dynamic_trajectory.py`
- `simulations/article/ecouves_a5/short_dynamic_control.py`
- `simulations/article/ecouves_a5/status_shape_mass_balance.py`

### state_snapshots: shared candidate

Q-9D:
- `simulations/article/q9d_full_run.py`
- `simulations/article/scenarios.py`
Q-9E/Q-9F:
- `scripts/article/diagnose_ecouves_a5_status_shape_mass_balance.py`
- `scripts/article/project_ecouves_a5_heights_to_grid.py`
- `scripts/article/run_ecouves_a5_main_trajectory.py`
- `scripts/article/run_ecouves_a5_mechanistic_sensitivity.py`
- `scripts/article/run_ecouves_a5_short_dynamic_control.py`
- `scripts/article/run_ecouves_a5_status_shape_sensitivity.py`
- `scripts/article/validate_ecouves_a5_initial_states.py`
- `simulations/article/ecouves_a5/distributional_diagnostics.py`
- `simulations/article/ecouves_a5/height_growth_allocation_audit.py`
- `simulations/article/ecouves_a5/hierarchical_height_diagnostics.py`
- `simulations/article/ecouves_a5/main_dynamic_trajectory.py`
- `simulations/article/ecouves_a5/mechanistic_sensitivity.py`
- `simulations/article/ecouves_a5/status_shape_sensitivity.py`

### multi_scenario_comparison: shared candidate

Q-9D:
- `simulations/article/analyze_dynamic_sensitivity.py`
- `simulations/article/compare_q9d_rho.py`
- `simulations/article/copula_initial_condition.py`
- `simulations/article/dynamic_sensitivity.py`
- `simulations/article/initial_state_sensitivity.py`
- `simulations/article/q9d_full_run.py`
- `simulations/article/run_dynamic_sensitivity.py`
- `simulations/article/run_q9d_scenarios.py`
- `simulations/article/scenarios.py`
Q-9E/Q-9F:
- `scripts/article/audit_ecouves_a5.py`
- `scripts/article/audit_ecouves_a5_height_growth_allocation.py`
- `scripts/article/diagnose_ecouves_a5_distributions.py`
- `scripts/article/diagnose_ecouves_a5_height_hierarchy.py`
- `scripts/article/diagnose_ecouves_a5_status_shape_mass_balance.py`
- `scripts/article/project_ecouves_a5_heights_to_grid.py`
- `scripts/article/reconstruct_ecouves_a5_heights.py`
- `scripts/article/run_ecouves_a5_main_trajectory.py`
- `scripts/article/run_ecouves_a5_mechanistic_sensitivity.py`
- `scripts/article/run_ecouves_a5_short_dynamic_control.py`
- `scripts/article/run_ecouves_a5_status_shape_sensitivity.py`
- `scripts/article/validate_ecouves_a5_initial_states.py`
- `simulations/article/ecouves_a5/__init__.py`
- `simulations/article/ecouves_a5/height_diagnostics.py`
- `simulations/article/ecouves_a5/height_reconstruction.py`
- `simulations/article/ecouves_a5/hierarchical_height_diagnostics.py`
- `simulations/article/ecouves_a5/mechanistic_sensitivity.py`
- `simulations/article/ecouves_a5/status_shape_mass_balance.py`
- `simulations/article/ecouves_a5/status_shape_sensitivity.py`

### height_provider: Q-9E/Q-9F only

Q-9E/Q-9F:
- `scripts/article/project_ecouves_a5_heights_to_grid.py`
- `scripts/article/reconstruct_ecouves_a5_heights.py`
- `scripts/article/run_ecouves_a5_main_trajectory.py`
- `scripts/article/run_ecouves_a5_mechanistic_sensitivity.py`
- `scripts/article/run_ecouves_a5_short_dynamic_control.py`
- `scripts/article/validate_ecouves_a5_initial_states.py`
- `simulations/article/ecouves_a5/__init__.py`
- `simulations/article/ecouves_a5/height_adapter.py`
- `simulations/article/ecouves_a5/height_reconstruction.py`
- `simulations/article/ecouves_a5/main_dynamic_trajectory.py`
- `simulations/article/ecouves_a5/mechanistic_sensitivity.py`
- `simulations/article/ecouves_a5/pydynamicforest_adapter.py`
- `simulations/article/ecouves_a5/savine_height_provider.py`
- `simulations/article/ecouves_a5/short_dynamic_control.py`
- `simulations/article/ecouves_a5/status_shape_mass_balance.py`
- `simulations/article/ecouves_a5/status_shape_sensitivity.py`

### conservative_projection: Q-9E/Q-9F only

Q-9E/Q-9F:
- `scripts/article/audit_ecouves_a5.py`
- `scripts/article/project_ecouves_a5_heights_to_grid.py`
- `scripts/article/run_ecouves_a5_status_shape_sensitivity.py`
- `simulations/article/ecouves_a5/__init__.py`
- `simulations/article/ecouves_a5/grid_projection.py`
- `simulations/article/ecouves_a5/grid_reconstruction.py`
- `simulations/article/ecouves_a5/pydynamicforest_adapter.py`
- `simulations/article/ecouves_a5/state_compatibility.py`

### copula_specific: Q-9D only

Q-9D:
- `simulations/article/analyze_dynamic_sensitivity.py`
- `simulations/article/compare_q9d_rho.py`
- `simulations/article/copula_initial_condition.py`
- `simulations/article/dynamic_sensitivity.py`
- `simulations/article/initial_state_sensitivity.py`
- `simulations/article/q9d_full_run.py`
- `simulations/article/run_dynamic_sensitivity.py`
- `simulations/article/run_q9d_scenarios.py`
- `simulations/article/scenarios.py`

### empirical_inventory_specific: Q-9E/Q-9F only

Q-9E/Q-9F:
- `scripts/article/audit_ecouves_a5.py`
- `scripts/article/project_ecouves_a5_heights_to_grid.py`
- `scripts/article/reconstruct_ecouves_a5_heights.py`
- `scripts/article/run_ecouves_a5_short_dynamic_control.py`
- `simulations/article/ecouves_a5/grid_projection.py`
- `simulations/article/ecouves_a5/height_adapter.py`
- `simulations/article/ecouves_a5/height_diagnostics.py`
- `simulations/article/ecouves_a5/height_export.py`
- `simulations/article/ecouves_a5/height_providers.py`
- `simulations/article/ecouves_a5/height_reconstruction.py`
- `simulations/article/ecouves_a5/height_types.py`
- `simulations/article/ecouves_a5/height_validation.py`
- `simulations/article/ecouves_a5/hierarchical_height_diagnostics.py`
- `simulations/article/ecouves_a5/inventory.py`
- `simulations/article/ecouves_a5/pydynamicforest_adapter.py`
- `simulations/article/ecouves_a5/savine_height_provider.py`
- `simulations/article/ecouves_a5/short_dynamic_control.py`
- `simulations/article/ecouves_a5/stand_metrics.py`

## Decision framework

### Likely common infrastructure

- injection and validation of a prebuilt initial state;
- output-directory isolation and overwrite protection;
- configuration, manifest and reproducibility metadata;
- observation operators;
- state, mass, finiteness and non-negativity checks;
- horizon validation and state snapshots;
- multi-scenario comparison utilities.

### Copula-specific domain logic

- truncated marginal construction;
- Gaussian copula and rho sensitivity;
- calibration under aggregate information;
- non-identifiability analysis.

### Empirical-specific domain logic

- individual-inventory reconciliation;
- height-provider interface and deterministic height reconstruction;
- conservative projection from tree cloud to physical and native grids;
- comparison of empirical reconstructed states across inventories.

### Excluded from factorization

Q-9F.7 must remain a separately archived rejected experiment.

## Next review

Review the CSV to identify semantic rather than merely lexical duplication. No move, rename or shared utility extraction should occur before that review.
