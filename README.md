# PyDynamicForest

PyDynamicForest is a Python research code for simulating size-structured forest stand dynamics.

The model describes the evolution of a tree density distribution structured by height and DBH.
The repository is currently being refactored from an initial research script into a modular, maintainable and scientifically traceable codebase.

## Current status

The current refactor introduces the API:

    results = simulate(x0, p, c)

where:

- `x0` is an `InitialCondition`;
- `p` is a `Parameters` object;
- `c` is a `SimulationContext`;
- `results` is a `SimulationResults` object.

The solver is selected automatically from the numerical parameters.

For the baseline reduced scenario, the default solver is the sparse legacy-like solver.

The solver can still be explicitly overridden when needed, for example for regression tests:

    results = simulate(x0, p, c, solver_name="dense")
    results = simulate(x0, p, c, solver_name="sparse")

The sparse solver has been validated against the reduced legacy reference case up to numerical precision.

The current development version is `0.3.0.dev0`, following the stable refactor tag:

    v0.2.0-refactor

## Main structure

    pydynamicforest/
    simulations/
    scripts/
    legacy/
    tests/
    reference_outputs/
    outputs/

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

    pydf-run-baseline --preset baseline --full --output-dir outputs\baseline_reduced_sparse

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

Run the full reduced baseline with:

    pydf-run-baseline --preset baseline --full --output-dir outputs\baseline_reduced_sparse

Run the short debug preset with:

    pydf-run-baseline --preset short-debug --output-dir outputs\short_debug

Run the dense debug preset with:

    pydf-run-baseline --preset dense-debug --max-steps 2 --output-dir outputs\dense_debug

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

The baseline configuration currently provides three presets:

- `baseline`: the default reduced baseline scenario;
- `short-debug`: a lightweight sparse configuration for fast debugging;
- `dense-debug`: a lightweight dense configuration for regression/debugging.

Examples:

    pydf-run-baseline --preset baseline --max-steps 10 --output-dir outputs\preset_baseline

    pydf-run-baseline --preset short-debug --output-dir outputs\preset_short_debug

    pydf-run-baseline --preset dense-debug --max-steps 2 --output-dir outputs\preset_dense_debug

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

For example, run a small grid debug simulation with:

    pydf-run-baseline --preset baseline --nx 10 --ny 10 --n-steps 20 --max-steps 5 --output-dir outputs\cli_small_grid

Run with custom observation ages:

    pydf-run-baseline --preset baseline --max-steps 5 --observation-ages 18 20 25 --output-dir outputs\cli_custom_observations

Override the simulation horizon:

    pydf-run-baseline --preset baseline --t-end 10 --n-steps 20 --max-steps 5 --output-dir outputs\cli_time_override

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

The code is still under active refactoring.

The dense solver is retained for regression checks but is computationally expensive.

The sparse solver is preferred for practical runs.

The distinction between legacy mass, trapezoidal mass, and scientific diagnostic mass has been clarified in the code, but the scientific interpretation of these conventions still needs to be reviewed.

Quadrature conventions should continue to be harmonized across diagnostics.

The current plotting workflow is functional but still provisional. A future visualization-quality improvement step is planned.

Future scientific extensions such as recruitment, alternative mortality laws, alternative growth functions, alternative status definitions, and nonlinear dependencies on `U` or derived quantities remain to be implemented.

## Authors and contributors

This code originates from the IDEAForDynamics project.

### Original implementation

- **Aymeric Jacob de Cordemoy** — original Python implementation and initial research code.

### Scientific supervision and refactor

- **Julien SAINTE-MARIE** — scientific supervision, conceptual restructuring, and current refactor toward a modular research code.
- **Takeo TAKAHASHI** — scientific supervision.

### IDEAForDynamics project members

To be completed.

Additional contributors can be added here as the project evolves.

## Acknowledgements

This work was supported by the interdisciplinary program ARTEMIS of Lorraine Université d'Excellence (ANR-15-IDEX-04-LUE).

## License

PyDynamicForest is distributed under the GNU Lesser General Public License v3.0 or later.

SPDX-License-Identifier: LGPL-3.0-or-later

This license allows PyDynamicForest to be used as a library by other software, including software distributed under different licenses, while requiring modifications to PyDynamicForest itself to remain available under the same LGPL terms.