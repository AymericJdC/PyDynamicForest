# Q-9F.2 historical versus reproducible run comparison

Reference: `outputs\article_scenarios\ecouves_a5_main_trajectory_1992_2020`  
Candidate: `outputs\article_scenarios\ecouves_a5_main_trajectory_1992_2020_repro_c0d5916`  
Tolerance: atol=1e-12, rtol=1e-12

## Verdict

- Scientific outputs equal within tolerance: **True**.
- Candidate manifests complete and consistent: **True**.

## Files

- `ecouves_a5_main_trajectory_time_series.csv`: scientific_equal=True; byte_identical=True; 58 rows; max_abs_diff=0
- `ecouves_a5_main_trajectory_comparison.csv`: scientific_equal=True; byte_identical=True; 44 rows; max_abs_diff=0
- `ecouves_a5_simulated_state_1992.npz`: scientific_equal=True; byte_identical=True; U: shape=(40, 40), max_abs_diff=0; actual_age: shape=(), max_abs_diff=0; requested_age: shape=(), max_abs_diff=0; step_index: shape=(), max_abs_diff=0; time: shape=(), max_abs_diff=0; year: shape=(), max_abs_diff=0
- `ecouves_a5_simulated_state_1998.npz`: scientific_equal=True; byte_identical=True; U: shape=(40, 40), max_abs_diff=0; actual_age: shape=(), max_abs_diff=0; requested_age: shape=(), max_abs_diff=0; step_index: shape=(), max_abs_diff=0; time: shape=(), max_abs_diff=0; year: shape=(), max_abs_diff=0
- `ecouves_a5_simulated_state_2016.npz`: scientific_equal=True; byte_identical=True; U: shape=(40, 40), max_abs_diff=0; actual_age: shape=(), max_abs_diff=0; requested_age: shape=(), max_abs_diff=0; step_index: shape=(), max_abs_diff=0; time: shape=(), max_abs_diff=0; year: shape=(), max_abs_diff=0
- `ecouves_a5_simulated_state_2020.npz`: scientific_equal=True; byte_identical=True; U: shape=(40, 40), max_abs_diff=0; actual_age: shape=(), max_abs_diff=0; requested_age: shape=(), max_abs_diff=0; step_index: shape=(), max_abs_diff=0; time: shape=(), max_abs_diff=0; year: shape=(), max_abs_diff=0

## Manifest checks

- All required fields are present and internally consistent.

## Decision

The reproducible run can replace the historical run as the frozen Q-9F.2 reference only if both verdicts above are true. The historical directory should remain untouched until the archive policy is decided.
