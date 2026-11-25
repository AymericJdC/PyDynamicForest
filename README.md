# PyDynamicForest

PyDynamicForest is a Python research code for simulating size-structured forest stand dynamics.

The model describes the evolution of a tree density distribution structured by height and DBH.
It was refactored from an initial research script into a modular, tested and scientifically traceable codebase.

## Current status

Version 1.0.0 is the version used for the article

> A. Jacob de Cordemoy, J. Sainte-Marie and T. Takahashi,
> *A well-posed height–diameter population model of forest stand dynamics
> with a non-local size hierarchy*, submitted to the Journal of Mathematical
> Biology.

All numerical results of this article, from the completion of missing tree
heights to Figures 1–3 and the tables of Online Resource 1, are produced by
the pipeline `studies/ecouves_a5` (see below).

The general simulation API is

    results = simulate(x0, p, c)

where `x0` is an `InitialCondition`, `p` a `Parameters` object, `c` a
`SimulationContext` and `results` a `SimulationResults` object. The solver is
selected from the numerical parameters and can be overridden
(`solver_name="dense"`, `"sparse"`, `"vectorised"` or `"vectorised_cg"`). The
vectorised solver (`pydynamicforest/fast_solver.py`) assembles the
semi-implicit scheme with sparse diagonals and solves the symmetric positive
definite system by a direct method or by the conjugate gradient method with a
Jacobi preconditioner; it reproduces the reference implementation to
numerical precision.

## Reproducing the results of the JoMB article

From the repository root:

    python -m studies.ecouves_a5.run_all --config CONFIG.toml --output-dir OUT --with-sensitivity

`CONFIG.toml` only needs the values that differ from
`studies/ecouves_a5/config.toml`, usually the paths of the input files.
`OUT/manifest.json` records the configuration, the code version, the library
versions and the SHA-256 checksums of the inputs and of every output. The
main trajectory on the 313×313 grid takes about 1 min, the bootstrap about
4 min and the grid and sensitivity studies about 20 min. Details are given in
`studies/ecouves_a5/README.md`.

The individual-tree records of the Écouves A5 trial belong to the GIS
Coopérative de données sur la croissance des peuplements forestiers (GIS
Coop) and are not distributed with this repository. They can be requested
from the GIS Coop.

## Main structure

    pydynamicforest/     model, solvers and diagnostics
    studies/ecouves_a5/  reproducible pipeline of the JoMB article
    simulations/         baseline and development scenarios
    scripts/             command-line tools of the refactor
    tests/               test suite (fast tests run in CI)
    legacy/              original scripts, kept unchanged for traceability
    reference_outputs/   reference outputs of the legacy implementation
    docs/                development notes and audits

## Installation

Create the conda environment with:

    conda env create -f environment.yml
    conda activate pydynamicforest

Or install dependencies with:

    python -m pip install -r requirements.txt

Main dependencies:

- numpy;
- scipy;
- matplotlib;
- tqdm;
- pytest.

## Editable installation

PyDynamicForest can be installed in editable development mode from the repository root:

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m pip install -e .

For development dependencies, use:

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m pip install -e ".[dev]"

This makes the `pydynamicforest`, `simulations` and `scripts` modules importable while keeping the source tree editable.

## Console entry points

After editable installation, PyDynamicForest provides command-line entry points.

Recommended commands include:

    pydf-run-baseline --preset short-debug --output-dir outputs\short_debug

    pydf-run-baseline --preset baseline --full --progress --output-dir outputs\baseline_reduced_sparse

    pydf-run-baseline --preset state-debug --progress --max-steps 5 --output-dir outputs\state_debug

    pydf-plot-observations --input-dir outputs\baseline_reduced_sparse

    pydf-plot-observation-comparisons --input-dir outputs\baseline_reduced_sparse

    pydf-plot-diagnostics --input-file outputs\baseline_reduced_sparse\time_series.csv

    pydf-compare-reduced-reference

The corresponding developer-style commands using `python -m` remain available.

If the `pydf-*` commands are not found on Windows, verify that the `Scripts` directory of the environment is available in the `PATH`, or use the full executable path, for example:

    C:\Users\saintemarie\.conda\envs\pydynamicforest\Scripts\pydf-run-baseline.exe --preset short-debug --output-dir outputs\short_debug

A temporary fix for the current terminal is:

    set "CONDA_ENV=C:\Users\saintemarie\.conda\envs\pydynamicforest"
    set "PATH=%CONDA_ENV%;%CONDA_ENV%\Scripts;%CONDA_ENV%\Library\bin;%PATH%"

## Tests

Run fast tests with:

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m pytest tests

Run slow tests with:

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m pytest tests -m slow

Run the end-to-end CLI workflow test with:

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m pytest tests\test_end_to_end_cli.py -m e2e

Run all tests, including slow tests, with:

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m pytest tests -m "slow or not slow"

## Simulations

Run a configurable baseline simulation with:

    pydf-run-baseline --preset baseline --max-steps 10 --output-dir outputs\baseline_short_cli

or equivalently:

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m scripts.run_baseline --preset baseline --max-steps 10 --output-dir outputs\baseline_short_cli

Run the full reduced baseline with a progress bar:

    pydf-run-baseline --preset baseline --full --progress --output-dir outputs\baseline_reduced_sparse

Run the short debug preset with:

    pydf-run-baseline --preset short-debug --output-dir outputs\short_debug

Run the dense debug preset with:

    pydf-run-baseline --preset dense-debug --max-steps 2 --output-dir outputs\dense_debug

Run the state-aware debug preset with:

    pydf-run-baseline --preset state-debug --progress --max-steps 5 --output-dir outputs\state_debug

The optional progress bar can be enabled with:

    --progress

The progress bar is disabled by default to keep tests, automated workflows and scripted runs quiet unless explicitly requested.

The solver is selected by default from the numerical parameters. It can still be overridden explicitly:

    pydf-run-baseline --preset short-debug --solver-name dense --max-steps 2 --output-dir outputs\dense_override

The older explicit sparse baseline script is still available:

    pydf-run-baseline-reduced-sparse

or:

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m scripts.run_baseline_reduced_sparse

## Baseline scenario configuration

The baseline scenario is configured through:

    simulations/baseline/config.py

This file centralizes the main values used by the baseline scenario:

- stand ages;
- initial condition;
- physical scales;
- numerical grid;
- time discretization;
- model coefficient laws;
- solver configuration;
- output and observation settings.

The following builders read their values from this configuration:

    build_initial_condition()
    build_parameters()
    build_context()

The builders can also accept a custom configuration dictionary, which allows creating scenario variants without duplicating the baseline files.

## Baseline presets

The baseline configuration currently provides four presets:

- `baseline`: the default reduced baseline scenario;
- `short-debug`: a lightweight sparse configuration for fast debugging;
- `dense-debug`: a lightweight dense configuration for regression/debugging;
- `state-debug`: a lightweight sparse debug configuration using the state-aware model-field evaluation pathway.

Examples:

    pydf-run-baseline --preset baseline --max-steps 10 --output-dir outputs\preset_baseline

    pydf-run-baseline --preset short-debug --output-dir outputs\preset_short_debug

    pydf-run-baseline --preset dense-debug --max-steps 2 --output-dir outputs\preset_dense_debug

    pydf-run-baseline --preset state-debug --progress --max-steps 5 --output-dir outputs\preset_state_debug

Presets can be combined with CLI overrides, for example:

    pydf-run-baseline --preset short-debug --nx 12 --ny 12 --max-steps 5 --output-dir outputs\short_debug_12x12

## Baseline CLI overrides

The configurable baseline runner can override selected baseline configuration values directly from the command line.

Available configuration override options include:

    --nx
    --ny
    --n-steps
    --t-end
    --initial-age
    --final-age
    --observation-ages
    --model-field-evaluation
    --progress

For example, run a small grid debug simulation with:

    pydf-run-baseline --preset baseline --nx 10 --ny 10 --n-steps 20 --max-steps 5 --output-dir outputs\cli_small_grid

Run with custom observation ages:

    pydf-run-baseline --preset baseline --max-steps 5 --observation-ages 18 20 25 --output-dir outputs\cli_custom_observations

Override the simulation horizon:

    pydf-run-baseline --preset baseline --t-end 10 --n-steps 20 --max-steps 5 --output-dir outputs\cli_time_override

Select the model-field evaluation mode explicitly:

    pydf-run-baseline --preset short-debug --model-field-evaluation legacy --max-steps 5 --output-dir outputs\mfe_legacy_debug

or:

    pydf-run-baseline --preset short-debug --model-field-evaluation state --max-steps 5 --output-dir outputs\mfe_state_debug

Enable a progress bar explicitly:

    pydf-run-baseline --preset short-debug --progress --max-steps 5 --output-dir outputs\progress_debug

The default model-field evaluation mode is:

    --model-field-evaluation legacy

The `state` mode is preparatory. It evaluates model fields through the state-aware interface, while the current solver supports both dictionary-based fields and `ModelFields`.

These overrides modify a copy of the baseline configuration for the current run only. The file `simulations/baseline/config.py` is not modified.

## Validation against legacy references

The original implementation is preserved in the `legacy/` directory.

Compare the sparse refactored solver with the reduced legacy reference using:

    pydf-compare-reduced-reference

or equivalently:

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m scripts.compare_reduced_reference

The comparison checks:

- final top height;
- final basal area;
- final legacy mass;
- minimum density over the trajectory.

## Observation management

The simulation context supports observation selection by stand age.

In PyDynamicForest, observations are simulated model states selected for storage and analysis at requested stand ages.
They should not be confused with empirical field observations.

Observation ages are defined in the simulation context through the output specification, for example:

    OutputSpecification(
        observation_ages=[18.0, 45.0, 69.0],
        save_full_trajectory=False,
    )

This avoids hard-coded numerical indices such as:

    U[5294,:,:]

## Output files

Simulation outputs are written to the `outputs/` directory, which is ignored by Git.

A typical output directory contains:

    time_series.csv
    metadata.json
    summary.txt
    observations/
    figures/
        observation_step_.../
        comparisons/
        time_series/

The `observations/` directory contains exported `.npz` files for selected model observations.

Each observation file contains:

- `U`: simulated density field;
- `time`: simulation time;
- `age`: stand age;
- `step_index`: numerical time-step index;
- `height_grid`: normalized height grid;
- `dbh_grid`: normalized DBH grid;
- `height_grid_physical`: height grid in physical units;
- `dbh_grid_physical`: DBH grid in physical units.

## Plotting observations

After running a simulation and exporting observations, standard figures can be generated with:

    pydf-plot-observations --input-dir outputs\baseline_reduced_sparse

For each observation, the script currently generates:

- a 2D density field;
- a height distribution;
- a DBH distribution.

## Plotting observation comparisons

After exporting observations, comparison figures across stand ages can be generated with:

    pydf-plot-observation-comparisons --input-dir outputs\baseline_reduced_sparse

The script currently generates:

- height distribution comparisons;
- DBH distribution comparisons;
- density field comparisons.

## Plotting diagnostic time series

After running a simulation and exporting the time series, diagnostic figures can be generated with:

    pydf-plot-diagnostics --input-file outputs\baseline_reduced_sparse\time_series.csv

The script currently generates one figure for each of the following diagnostics:

- total mass;
- legacy mass;
- minimum density;
- top height;
- basal area.

The x-axis can be changed from stand age to simulation time with:

    pydf-plot-diagnostics --x-key time

## Command reference

A full command reference is available in:

    COMMANDS.md

## Refactor notes

Detailed refactor notes are available in:

    README_refactor.md

## Current limitations

Outside the pipeline of the JoMB article, parts of the code are still being refactored.

The dense solver is retained for regression checks but is computationally expensive.

The sparse solver is preferred for practical runs.

The distinction between legacy mass, trapezoidal mass, and scientific diagnostic mass has been clarified in the code, but the scientific interpretation of these conventions still needs to be reviewed.

Quadrature conventions should continue to be harmonized across diagnostics.

The current plotting workflow is functional but still provisional. A future visualization-quality improvement step is planned.

The `state` model-field evaluation mode is available for testing and future model extensions, but the default validated pathway remains `legacy`.

Future scientific extensions such as recruitment, alternative mortality laws, alternative growth functions, alternative status definitions, and nonlinear dependencies on `U` or derived quantities remain to be implemented.

## Authors and contributors

This code originates from the IDEAForDynamics project.

### Original implementation

- **Aymeric Jacob de Cordemoy** — original Python implementation and initial research code.

### Scientific supervision

- **Julien SAINTE-MARIE** — scientific supervision and conceptual restructuring.
- **Takeo TAKAHASHI** — scientific supervision.
- **Jean-Daniel Bontemps** — scientific supervision.

### Refactor

- **Julien SAINTE-MARIE** — refactor toward a modular research code and reproducible pipeline of the JoMB article.

### IDEAForDynamics project members

To be completed.

Additional contributors can be added here as the project evolves.

## Acknowledgements

This work was supported by the interdisciplinary program ARTEMIS of Lorraine Université d'Excellence (ANR-15-IDEX-04-LUE).

## License

PyDynamicForest is distributed under the GNU Lesser General Public License v3.0 or later.

SPDX-License-Identifier: LGPL-3.0-or-later

This license allows PyDynamicForest to be used as a library by other software, including software distributed under different licenses, while requiring modifications to PyDynamicForest itself to remain available under the same LGPL terms.