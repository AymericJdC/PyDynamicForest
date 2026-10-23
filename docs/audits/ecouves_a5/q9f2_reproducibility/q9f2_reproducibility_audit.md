# Q-9F.2 reproducibility audit against Q-9D

Date: 2026-10-23T16:52:09+02:00  
Branch: `feature/observation-quadrature`  
HEAD: `8ad8ae177514e55d7bff97da852f13142c33adff`

## Scope

Read-only audit of the main empirical trajectory. No test or simulation was run.

## Git status

```text
?? audit_q9f2_reproducibility.py
?? compare_q9d_q9f_architectures.py
?? q9d_q9f_architecture_comparison.md
?? q9d_q9f_architecture_components.csv
?? q9f2_reproducibility_fields.csv
```

## Reference code

- `simulations/article/q9d_full_run.py`: _git_value, _tracked_worktree_clean, _write_csv, run_q9d_scenario
- `scripts/article/run_ecouves_a5_main_trajectory.py`: main, root, writecsv
- `simulations/article/ecouves_a5/main_dynamic_trajectory.py`: StandSummary, load_empirical_targets, nearest_target_steps, record, run_main_trajectory, summarize_density

## Q-9F.2 outputs discovered

Files: **9**.
- `outputs/article_scenarios/ecouves_a5_main_trajectory_1992_2020/.gitkeep`
- `outputs/article_scenarios/ecouves_a5_main_trajectory_1992_2020/ecouves_a5_main_trajectory_comparison.csv`
- `outputs/article_scenarios/ecouves_a5_main_trajectory_1992_2020/ecouves_a5_main_trajectory_metadata.json`
- `outputs/article_scenarios/ecouves_a5_main_trajectory_1992_2020/ecouves_a5_main_trajectory_report.md`
- `outputs/article_scenarios/ecouves_a5_main_trajectory_1992_2020/ecouves_a5_main_trajectory_time_series.csv`
- `outputs/article_scenarios/ecouves_a5_main_trajectory_1992_2020/ecouves_a5_simulated_state_1992.npz`
- `outputs/article_scenarios/ecouves_a5_main_trajectory_1992_2020/ecouves_a5_simulated_state_1998.npz`
- `outputs/article_scenarios/ecouves_a5_main_trajectory_1992_2020/ecouves_a5_simulated_state_2016.npz`
- `outputs/article_scenarios/ecouves_a5_main_trajectory_1992_2020/ecouves_a5_simulated_state_2020.npz`

## Guarantee matrix

Detailed matrix: `q9f2_reproducibility_fields.csv`.

Fields absent from detected Q-9F.2 outputs: **16**.
Q-9D guarantees potentially transferable: **10**.

## Missing or implicit fields

- `git_commit`: Q-9D guarantee missing from Q-9F.2; action: transfer guarantee from Q-9D to Q-9F.2.
- `git_worktree_status`: Q-9D guarantee missing from Q-9F.2; action: transfer guarantee from Q-9D to Q-9F.2.
- `python_version`: Q-9D guarantee missing from Q-9F.2; action: transfer guarantee from Q-9D to Q-9F.2.
- `numpy_version`: Q-9D guarantee missing from Q-9F.2; action: transfer guarantee from Q-9D to Q-9F.2.
- `scipy_version`: Q-9D guarantee missing from Q-9F.2; action: transfer guarantee from Q-9D to Q-9F.2.
- `execution_timestamp`: not detected; action: add if required for reproducibility.
- `initial_state_path`: present in Q-9F.2 code but not detected in outputs; action: ensure emitted in final Q-9F.2 manifest.
- `initial_state_sha256`: not detected; action: add if required for reproducibility.
- `inventory_source`: not detected; action: add explicit scientific provenance to Q-9F.2 manifest.
- `aggregate_source`: not detected; action: add explicit scientific provenance to Q-9F.2 manifest.
- `age_convention`: present in Q-9F.2 code but not detected in outputs; action: ensure emitted in final Q-9F.2 manifest.
- `target_age`: Q-9D guarantee missing from Q-9F.2; action: transfer guarantee from Q-9D to Q-9F.2.
- `no_recalibration`: present in Q-9F.2 code but not detected in outputs; action: ensure emitted in final Q-9F.2 manifest.
- `output_overwrite_guard`: Q-9D guarantee missing from Q-9F.2; action: transfer guarantee from Q-9D to Q-9F.2.
- `configuration_manifest`: Q-9D guarantee missing from Q-9F.2; action: transfer guarantee from Q-9D to Q-9F.2.
- `reproducibility_manifest`: Q-9D guarantee missing from Q-9F.2; action: transfer guarantee from Q-9D to Q-9F.2.

## Scientific safeguards

The final Q-9F.2 manifest should distinguish the GIS Coop aggregate series from the individual inventories transmitted by Francois Ningre. Small discrepancies, including age-label differences, must remain documented by source rather than silently reconciled.

The manifest should also identify reconstructed heights as deterministic provisional values from the selected height-diameter relation, not as measured individual heights.

## Decision rule

Do not refactor the simulation architecture in this lot. Add only missing manifest fields and overwrite protection after reviewing this audit. Preserve the existing tested scientific modules.
