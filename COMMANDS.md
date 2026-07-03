# PyDynamicForest command reference

This file summarizes the main commands used during the refactor and development of PyDynamicForest.

The examples below assume that commands are run from the root directory of the repository.

## 1. Environment

### Activate the conda environment

    conda activate pydynamicforest

### Use the explicit Python interpreter

If the conda activation does not correctly select the Python interpreter, use:

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe

### Recreate the conda environment

    conda env create -f environment.yml
    conda activate pydynamicforest

### Install dependencies from requirements.txt

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m pip install -r requirements.txt

## 2. Git workflow

### Check current branch and status

    git branch
    git status

### Stage and commit changes

    git add <file_or_directory>
    git commit -m "Commit message"

### Push the refactor branch

    git push origin refactor-julien

### Restore a modified file

    git restore path\to\file.py

### Show differences in a file

    git diff path\to\file.py

## 3. Tests

### Run the fast test suite

By default, slow tests are excluded through `pytest.ini`.

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m pytest tests

### Run only slow tests

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m pytest tests -m slow

### Run the end-to-end CLI workflow test

The end-to-end test checks the complete command-line workflow:

- baseline simulation;
- result exports;
- observation exports;
- individual observation plots;
- observation comparison plots;
- diagnostic time-series plots.

Run it with:

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m pytest tests\test_end_to_end_cli.py -m e2e

or together with other slow tests:

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m pytest tests -m slow

### Run all tests, including slow tests

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m pytest tests -m "slow or not slow"

### Run a specific test file

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m pytest tests\test_baseline_config.py

### Run a specific test by name

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m pytest tests -k "observation"

## 4. Baseline scenario configuration

The baseline scenario values are centralized in:

    simulations/baseline/config.py

This file defines the main configuration values used by:

    simulations/baseline/initial_condition.py
    simulations/baseline/parameters.py
    simulations/baseline/context.py

It currently contains:

- stand ages;
- initial condition parameters;
- physical scales;
- grid definition;
- time discretization;
- model coefficient values;
- solver settings;
- observation and output settings.

This allows the baseline scenario to be modified from a single configuration file instead of editing several files independently.

## 5. Baseline simulations

### Run the short baseline scenario

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m simulations.baseline.run

This runs a short sparse simulation using the solver selected from numerical parameters.

### Run a configurable short baseline simulation

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m scripts.run_baseline --max-steps 10 --output-dir outputs\baseline_short_cli

### Run the full reduced baseline

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m scripts.run_baseline --full --output-dir outputs\baseline_reduced_sparse_cli

### Override the solver explicitly

For debugging or regression checks:

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m scripts.run_baseline --max-steps 2 --solver-name dense --output-dir outputs\baseline_dense_debug

### Run the older explicit reduced sparse baseline script

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m scripts.run_baseline_reduced_sparse

## 6. Legacy references

### Run the short legacy reference

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe legacy\DynamicForestModel_2D_short_reference.py > reference_outputs\legacy_short_console_output.txt

### Run the reduced legacy reference

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe legacy\DynamicForestModel_2D_reduced_reference.py > reference_outputs\legacy_reduced_console_output.txt

Warning: the reduced legacy reference uses the dense legacy solver and may be slower than the refactored sparse solver.

## 7. Comparisons and validation

### Compare sparse refactor with reduced legacy reference

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m scripts.compare_reduced_reference

This compares:

- final top height;
- final basal area;
- final legacy mass;
- minimum density over the trajectory.

### Expected validation status

For the reduced reference case, the sparse refactored solver should match the legacy reduced reference up to numerical precision.

Typical discrepancies are expected to be close to machine precision.

## 8. Observation exports

Selected model observations are exported as `.npz` files under:

    outputs/<run_name>/observations/

Example after running the reduced sparse baseline:

    outputs/baseline_reduced_sparse/observations/

Each observation file can be loaded in Python with:

    import numpy as np

    data = np.load("path/to/observation_file.npz")
    U = data["U"]
    age = data["age"]
    height_grid_physical = data["height_grid_physical"]
    dbh_grid_physical = data["dbh_grid_physical"]

Observation files contain:

- `U`;
- `time`;
- `age`;
- `step_index`;
- `height_grid`;
- `dbh_grid`;
- `height_grid_physical`;
- `dbh_grid_physical`.

## 9. Plotting exported observations

After running a simulation that exports observations, figures can be generated from the saved `.npz` files without rerunning the model.

Default command:

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m scripts.plot_observations

This command reads observations from:

    outputs/baseline_reduced_sparse/observations/

and writes figures to:

    outputs/baseline_reduced_sparse/figures/

The script generates, for each observation:

- a 2D density field;
- a height distribution;
- a DBH distribution.

The input and output directories can also be specified explicitly:

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m scripts.plot_observations --input-dir outputs\baseline_reduced_sparse --figures-dir outputs\baseline_reduced_sparse\figures

## 10. Plotting observation comparisons

After exporting observations, comparison figures across stand ages can be generated with:

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m scripts.plot_observation_comparisons

This command reads observations from:

    outputs/baseline_reduced_sparse/observations/

and writes figures to:

    outputs/baseline_reduced_sparse/figures/comparisons/

The script generates:

- height distribution comparisons;
- DBH distribution comparisons;
- density field comparisons.

The input and output directories can also be specified explicitly:

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m scripts.plot_observation_comparisons --input-dir outputs\baseline_reduced_sparse --figures-dir outputs\baseline_reduced_sparse\figures\comparisons

## 11. Plotting diagnostic time series

After running a simulation that exports `time_series.csv`, diagnostic figures can be generated without rerunning the model.

Default command:

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m scripts.plot_diagnostics

This command reads:

    outputs/baseline_reduced_sparse/time_series.csv

and writes figures to:

    outputs/baseline_reduced_sparse/figures/time_series/

The script generates figures for:

- total mass;
- legacy mass;
- minimum density;
- top height;
- basal area.

Use simulation time instead of stand age on the x-axis with:

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m scripts.plot_diagnostics --x-key time

The input file and output directory can also be specified explicitly:

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m scripts.plot_diagnostics --input-file outputs\baseline_reduced_sparse\time_series.csv --figures-dir outputs\baseline_reduced_sparse\figures\time_series

## 12. Syntax checks

### Compile a single Python file

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m py_compile pydynamicforest\solver.py

### Compile all package files

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m compileall pydynamicforest

## 13. Outputs

Simulation outputs are currently written under:

    outputs/

This directory is ignored by Git.

Example:

    outputs/baseline_reduced_sparse/
    ├── time_series.csv
    ├── metadata.json
    ├── summary.txt
    ├── observations/
    └── figures/
        ├── observation_step_.../
        ├── comparisons/
        └── time_series/

## 14. Development notes

### Main conceptual API

    results = simulate(x0, p, c)

where:

- `x0` is an `InitialCondition`;
- `p` is a `Parameters` object;
- `c` is a `SimulationContext`;
- `results` is a `SimulationResults` object.

### Solver selection

The recommended simulation call is:

    results = simulate(x0, p, c)

By default, the solver is selected from:

    p.numerics.matrix_storage

Currently supported values are:

    matrix_storage="dense"
    matrix_storage="sparse"

The baseline reduced scenario is configured to use:

    matrix_storage="sparse"
    linear_solver="scipy.sparse.linalg.spsolve"

For regression tests or debugging, the solver can still be overridden explicitly:

    results = simulate(x0, p, c, solver_name="dense")
    results = simulate(x0, p, c, solver_name="sparse")

### Observation management

Observations can be requested through the simulation context:

    OutputSpecification(
        observation_ages=[18.0, 45.0, 69.0],
        save_full_trajectory=False,
    )

When `save_full_trajectory` is `False`, only states close to the requested stand ages are stored in `results.observations`.

In this codebase, observations are simulated model states selected for analysis. They should not be confused with empirical field observations.

## 15. Common troubleshooting

### Python points to the wrong executable

Check:

    where python
    python -c "import sys; print(sys.executable)"

If needed, use the explicit interpreter:

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe

### `ModuleNotFoundError: No module named 'simulations'`

Run scripts as modules from the repository root:

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m scripts.run_baseline

rather than:

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe scripts\run_baseline.py

### Windows encoding issue in redirected legacy outputs

Some legacy outputs may be encoded with Windows console encoding. The comparison scripts handle this by trying UTF-8 first and falling back to cp1252.

### Matplotlib / Tk issue

Plotting uses the non-interactive `Agg` backend in `pydynamicforest/plotting.py`.

This avoids errors related to missing Tk libraries when generating figures in tests or batch runs.

## 16. Recommended daily workflow

A typical development cycle is:

    git status
    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m pytest tests
    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m simulations.baseline.run
    git add <modified_files>
    git commit -m "Meaningful commit message"
    git push origin refactor-julien

For deeper validation, run:

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m pytest tests -m slow
    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m scripts.compare_reduced_reference

For end-to-end CLI validation, run:

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m pytest tests\test_end_to_end_cli.py -m e2e