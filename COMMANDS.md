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

### Run all tests, including slow tests

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m pytest tests -m "slow or not slow"

### Run a specific test file

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m pytest tests\test_plotting.py

### Run a specific test by name

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m pytest tests -k "observation"

## 4. Baseline simulations

### Run the short baseline scenario

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m simulations.baseline.run

This runs a short sparse simulation, typically with:

    max_steps=10
    solver_name="sparse"

### Run the full reduced sparse baseline

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m scripts.run_baseline_reduced_sparse

This runs the reduced baseline case:

    Nx = 20
    Ny = 20
    Nt = 1000
    solver = sparse

Outputs are written to:

    outputs/baseline_reduced_sparse/

## 5. Legacy references

### Run the short legacy reference

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe legacy\DynamicForestModel_2D_short_reference.py > reference_outputs\legacy_short_console_output.txt

### Run the reduced legacy reference

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe legacy\DynamicForestModel_2D_reduced_reference.py > reference_outputs\legacy_reduced_console_output.txt

Warning: the reduced legacy reference uses the dense legacy solver and may be slower than the refactored sparse solver.

## 6. Comparisons and validation

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

## 7. Observation exports

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

## 8. Plotting exported observations

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

## 9. Plotting diagnostic time series

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

## 10. Syntax checks

### Compile a single Python file

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m py_compile pydynamicforest\solver.py

### Compile all package files

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m compileall pydynamicforest

## 11. Outputs

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
        └── time_series/

## 12. Development notes

### Main conceptual API

    results = simulate(x0, p, c, solver_name="sparse")

where:

- `x0` is an `InitialCondition`;
- `p` is a `Parameters` object;
- `c` is a `SimulationContext`;
- `results` is a `SimulationResults` object.

### Current solvers

    solver_name="dense"
    solver_name="sparse"

The dense solver is kept as a regression reference.

The sparse solver is preferred for practical simulations.

### Observation management

Observations can be requested through the simulation context:

    OutputSpecification(
        observation_ages=[18.0, 45.0, 69.0],
        save_full_trajectory=False,
    )

When `save_full_trajectory` is `False`, only states close to the requested stand ages are stored in `results.observations`.

In this codebase, observations are simulated model states selected for analysis. They should not be confused with empirical field observations.

## 13. Common troubleshooting

### Python points to the wrong executable

Check:

    where python
    python -c "import sys; print(sys.executable)"

If needed, use the explicit interpreter:

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe

### `ModuleNotFoundError: No module named 'simulations'`

Run scripts as modules from the repository root:

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m scripts.run_baseline_reduced_sparse

rather than:

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe scripts\run_baseline_reduced_sparse.py

### Windows encoding issue in redirected legacy outputs

Some legacy outputs may be encoded with Windows console encoding. The comparison scripts handle this by trying UTF-8 first and falling back to cp1252.

### Matplotlib / Tk issue

Plotting uses the non-interactive `Agg` backend in `pydynamicforest/plotting.py`.

This avoids errors related to missing Tk libraries when generating figures in tests or batch runs.

## 14. Recommended daily workflow

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