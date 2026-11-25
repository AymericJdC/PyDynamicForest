# Écouves A5 prototype scripts (archived)

These scripts produced the first version of the Écouves A5 results of the
JoMB article (November 2026): audits of the inventory files, extraction of
measured heights, height completion, regularised targets, main trajectory,
diffusion screen and figures. They were written step by step, with paths and
choices fixed in each script.

They are superseded by the pipeline `studies/ecouves_a5`, which reproduces
their results from a single configuration file and records a manifest with
checksums (see `studies/ecouves_a5/README.md`). In particular:

| Prototype script | Replaced by |
|---|---|
| `build_ecouves_regularized_targets.py` | `studies/ecouves_a5/heights.py`, `regularise.py` |
| `run_ecouves_regularized_main_trajectory.py` | `studies/ecouves_a5/dynamics.py` |
| `generate_ecouves_A5_regularized_figures.py` | `studies/ecouves_a5/figures.py` |

The audit scripts and the diffusion screen (`run_ecouves_1985_diffusion_screen.py`)
were exploratory and have no counterpart in the pipeline.

The scripts are kept unchanged for traceability and are not maintained or tested.
They expect to be run from the repository root and may need path edits.
