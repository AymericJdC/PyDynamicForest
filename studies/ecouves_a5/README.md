# Écouves A5 study (JoMB article)

This folder reproduces the numerical results of the article *A well-posed
height–diameter population model of forest stand dynamics with a non-local
size hierarchy*: completion of missing heights, regularised observations,
calibration, simulation 1985–2020, diagnostics, sensitivity analyses and
Figures 1–3.

## Run

From the repository root:

```
python -m studies.ecouves_a5.run_all --data-dir DATA --output-dir OUT
```

`DATA` contains the restricted inventory files named in `config.toml`
(`[data]`). Without them, set `assigned_heights` in `[data]` to an existing
assigned-height table; the step `heights` then only copies it.

| Step | Output (in `OUT`) | Duration (313×313) |
|---|---|---|
| `heights` | `heights/assigned_heights.csv`, `completion_summary.csv` | seconds |
| `regularise` | `regularised/observed_state_YYYY.npz`, `observed_summary.csv` | seconds |
| `calibrate` | `calibration/parameters.json` (and `history.csv`) | ~1 min per evaluation |
| `simulate` | `simulation/simulated_state_YYYY.npz`, `comparison.csv`, `time_series.csv` | ~1 min |
| `completion` | `completion/completion_sensitivity.csv` (Table S5) | seconds |
| `sensitivity` | `sensitivity/grid_study.json`, `height_status_sensitivity.json` | long (625×625 grid) |
| `figures` | `figures/figure_[1-3]_*.pdf` | seconds |

Options:

- `--from STEP --to STEP` runs part of the pipeline; each step reads the
  outputs of the previous ones in `OUT`.
- `--grid-nodes N` overrides the grid for quick checks (e.g. 40).
- `--recalibrate` re-estimates `K` and `c_phi`; otherwise the values of
  `[model]` are used and recorded.
- `--with-sensitivity` runs the grid study and the height-status exponents.

`OUT/manifest.json` records the configuration, the git commit (`-dirty` if
the working tree has changes), the library versions, the input checksums
(compared with those of the article inputs) and the checksum of every output.

## Reproduction check

With the article configuration, the pipeline reproduces the values of the
article (`simulation/comparison.csv`, Table S5, grid and exponent studies)
to a relative difference below 1e-13.

## Code

- `settings.py`: configuration and model parameters.
- `heights.py`: allometry and completion of missing heights.
- `regularise.py`: grid-independent triangular-kernel regularisation.
- `dynamics.py`: simulation (`pydynamicforest.fast_solver.ConstantCoefficientStepper`) and diagnostics.
- `calibration.py`: sequential calibration of `K` and `c_phi`.
- `completion.py`: sensitivity to the completion of missing heights.
- `figures.py`: Figures 1–3.
- `run_all.py`: command-line pipeline.

Tests: `tests/studies/test_ecouves_a5_pipeline.py` (synthetic data).
