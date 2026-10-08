# Manuscript-associated legacy scenario

## Purpose

This directory reconstructs the numerical scenario associated with the
`Modele2DImpliciteV3.py` script transmitted by Aymeric Jacob de Cordemoy.
It provides a traceable reference for the numerical revision of the
IDEAForDynamics manuscript.

This is a **legacy-reproduction scenario**, not the scientifically revised
Écouves scenario. Historical conventions are preserved explicitly so that
changes in the revised workflow can be separated from refactoring effects.

## Scenario

- stand ages: 18 to 69 years;
- simulation horizon: 51 years;
- normalized height-DBH grid: 40 x 40;
- time steps: 10,000;
- physical height scale: 50 m;
- physical DBH scale: 1 m;
- initial number of stems: 1,924.34 stems/ha;
- diffusion coefficient: 1e-5;
- mortality coefficient: 0.033 per year;
- physical height-growth rate: 1.66 m/year;
- physical DBH-growth rate: 0.0155 m/year.

The complete parameterization is stored in `config.py` and copied to each
full-run output directory as `configuration.json`.

## Components

- `config.py`: fixed scenario configuration;
- `initial_condition.py`: Gaussian initial condition;
- `parameters.py`: model and numerical parameters;
- `context.py`: simulation ages and requested observations;
- `legacy_reference.py`: independent short-run transcription of the legacy
  discrete equations;
- `full_run.py`: sparse full-run pipeline and output writer.

## Historical diagnostic conventions

### Number of stems

The manuscript-associated curve uses:

```text
legacy_mass = dx * dy * sum(U[1:, 1:])
```

The pipeline also records the two-dimensional trapezoidal mass. These two
quantities must not be treated as mathematically identical.

### Dominant height

`legacy_top_height` reproduces the historical discrete convention:

1. cells are sorted by decreasing DBH;
2. DBH ties are broken by decreasing height;
3. each cell represents `dx * dy * U[i, j]` stems/ha;
4. the last cell is used fractionally to reach 100 stems/ha;
5. physical heights are averaged arithmetically.

The full-run CSV also records the current `top_height` implementation. That
implementation sorts by DBH only and is retained for comparison, not as a
scientifically endorsed alternative.

The historical dominant-height curve is sensitive to the discretized DBH
class crossing the 100-stem threshold. The pipeline therefore records the
threshold class, the stems above it, and the fraction selected from it.

## Validation

The modular sparse implementation matches an independent transcription of the
legacy scheme after 1, 10, and 100 time steps, including the complete density
field and selected forest diagnostics.

The ordinary quick suite excludes tests marked `slow`:

```bash
python -m pytest -ra
```

Run the complete legacy reference test explicitly with:

```bash
python -m pytest -ra -m slow \
  tests/test_article_submission_full_reference.py
```

This test runs all 10,000 steps and may take approximately seven minutes on the
reference Windows workstation.

## Running the scenario

Short smoke run:

```bash
python -m simulations.article_submission_legacy.full_run \
  --max-steps 10 \
  --output-dir outputs/article_submission_legacy_smoke
```

Complete run:

```bash
python -m simulations.article_submission_legacy.full_run \
  --output-dir outputs/article_submission_legacy
```

The complete run writes:

- `time_series_legacy.csv`;
- `metadata.json`;
- `configuration.json`;
- compressed states near ages 18, 45, and 69 years.

## Full-run reference values

The following values were obtained from the sparse full run associated with
Git commit `37e7fe3e9ae833f4317ce8828f5b695a2e6e1adb`.

| Target age | Actual age | Step | Legacy stems/ha | Trapezoidal stems/ha | Legacy dominant height (m) | Current top height (m) | Basal area (m2/ha) |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 18 | 18.0000 | 0 | 1924.332965 | 1924.340000 | 10.604744 | 8.613782 | 21.598524 |
| 45 | 44.9994 | 5294 | 1089.056078 | 1089.614586 | 31.556381 | 31.101420 | 65.108364 |
| 69 | 69.0000 | 10000 | 681.846645 | 682.563421 | 40.558368 | 39.645023 | 88.563159 |

No negative density was detected during this run. The global minimum was zero,
already present in the numerically underflowed tails of the initial Gaussian.
This is an empirical scenario-level result, not a general positivity proof.

## Reproducibility status

The legacy scenario is now suitable as a patrimonial numerical reference.
Future work must remain separate and includes:

- a revised, quadrature-consistent dominant-height operator;
- sensitivity to DBH-grid resolution;
- time-step and mesh convergence;
- biological evaluation of the Écouves trajectory;
- comparison with the figures and observations used in the manuscript.
