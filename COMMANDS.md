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

## 2. Editable installation

Install the project in editable mode from the repository root:

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m pip install -e .

Install with development dependencies:

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m pip install -e ".[dev]"

Check that the package imports correctly:

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -c "import pydynamicforest; print(pydynamicforest)"

## 3. Console entry points

After editable installation, the following console commands are available:

    pydf-run-baseline
    pydf-run-baseline-reduced-sparse
    pydf-compare-reduced-reference
    pydf-plot-observations
    pydf-plot-observation-comparisons
    pydf-plot-diagnostics

Example:

    pydf-run-baseline --preset short-debug --output-dir outputs\short_debug

If the `pydf-*` commands are not found on Windows, use the full path to the executable:

    C:\Users\saintemarie\.conda\envs\pydynamicforest\Scripts\pydf-run-baseline.exe --preset short-debug --output-dir outputs\short_debug

A temporary fix for the current terminal is:

    set "CONDA_ENV=C:\Users\saintemarie\.conda\envs\pydynamicforest"
    set "PATH=%CONDA_ENV%;%CONDA_ENV%\Scripts;%CONDA_ENV%\Library\bin;%PATH%"

## 4. Git workflow

### Check current branch and status

    git branch
    git status

### Stage and commit changes

    git add <file_or_directory>
    git commit -m "Commit message"

### Push the development branch

    git push origin refactor-julien

### Restore a modified file

    git restore path\to\file.py

### Show differences in a file

    git diff path\to\file.py

## 5. Tests

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

### Run tests related to model-field evaluation

Run the tests related to model-field evaluation with:

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m pytest tests\test_model_field_evaluation.py tests\test_model_field_evaluation_mode.py

These tests check:

- the state-aware model-field evaluation interface;
- context-dependent coefficient laws;
- derived-dependent coefficient laws;
- the solver-side selection between `"legacy"` and `"state"` model-field evaluation modes.

### Run all tests, including slow tests

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m pytest tests -m "slow or not slow"

### Run a specific test file

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m pytest tests\test_baseline_config.py

## 6. Baseline scenario configuration

The baseline scenario values are centralized in:

    simulations/baseline/config.py

The baseline builders can accept a custom configuration dictionary:

    config = copy_baseline_config()
    config["grid"]["nx"] = 10

    x0 = build_initial_condition(config)
    p = build_parameters(config)
    c = build_context(config)

This allows scenario variants without duplicating the baseline files.

## 7. Baseline presets

Available presets are:

    baseline
    short-debug
    dense-debug

### Default baseline preset

    pydf-run-baseline --preset baseline --max-steps 10 --output-dir outputs\preset_baseline

### Short debug preset

    pydf-run-baseline --preset short-debug --output-dir outputs\preset_short_debug

### Dense debug preset

    pydf-run-baseline --preset dense-debug --max-steps 2 --output-dir outputs\preset_dense_debug

The equivalent developer form is:

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m scripts.run_baseline --preset short-debug --output-dir outputs\preset_short_debug

## 8. Baseline CLI overrides

The configurable baseline runner accepts selected configuration overrides.

### Override grid size

    pydf-run-baseline --preset short-debug --nx 12 --ny 12 --max-steps 5 --output-dir outputs\short_debug_12x12

### Override time discretization

    pydf-run-baseline --preset baseline --n-steps 20 --max-steps 5 --output-dir outputs\cli_nsteps_override

### Override observation ages

    pydf-run-baseline --preset baseline --max-steps 5 --observation-ages 18 20 25 --output-dir outputs\cli_custom_observations

### Override time horizon

    pydf-run-baseline --preset baseline --t-end 10 --n-steps 20 --max-steps 5 --output-dir outputs\cli_time_override

### Override stand ages

    pydf-run-baseline --preset baseline --initial-age 20 --final-age 70 --max-steps 5 --output-dir outputs\cli_age_override

Available override options are:

    --nx
    --ny
    --n-steps
    --t-end
    --initial-age
    --final-age
    --observation-ages

These options modify a copy of the selected preset for the current run only.

## 9. Baseline simulations

### Run a configurable short baseline simulation

    pydf-run-baseline --preset baseline --max-steps 10 --output-dir outputs\baseline_short_cli

### Run the full reduced baseline

    pydf-run-baseline --preset baseline --full --output-dir outputs\baseline_reduced_sparse

### Override the solver explicitly

For debugging or regression checks:

    pydf-run-baseline --preset short-debug --solver-name dense --max-steps 2 --output-dir outputs\dense_override

### Run the older explicit reduced sparse baseline script

    pydf-run-baseline-reduced-sparse

or:

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m scripts.run_baseline_reduced_sparse

## 10. Legacy references

### Run the short legacy reference

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe legacy\DynamicForestModel_2D_short_reference.py > reference_outputs\legacy_short_console_output.txt

### Run the reduced legacy reference

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe legacy\DynamicForestModel_2D_reduced_reference.py > reference_outputs\legacy_reduced_console_output.txt

Warning: the reduced legacy reference uses the dense legacy solver and may be slower than the refactored sparse solver.

## 11. Comparisons and validation

### Compare sparse refactor with reduced legacy reference

Recommended entry point:

    pydf-compare-reduced-reference

Equivalent developer command:

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m scripts.compare_reduced_reference

This compares:

- final top height;
- final basal area;
- final legacy mass;
- minimum density over the trajectory.

## 12. Observation exports

Selected model observations are exported as `.npz` files under:

    outputs/<run_name>/observations/

Each observation file can be loaded in Python with:

    import numpy as np

    data = np.load("path/to/observation_file.npz")
    U = data["U"]
    age = data["age"]
    height_grid_physical = data["height_grid_physical"]
    dbh_grid_physical = data["dbh_grid_physical"]

## 13. Plotting exported observations

Recommended entry point:

    pydf-plot-observations --input-dir outputs\baseline_reduced_sparse

Equivalent developer command:

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m scripts.plot_observations --input-dir outputs\baseline_reduced_sparse

## 14. Plotting observation comparisons

Recommended entry point:

    pydf-plot-observation-comparisons --input-dir outputs\baseline_reduced_sparse

Equivalent developer command:

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m scripts.plot_observation_comparisons --input-dir outputs\baseline_reduced_sparse

## 15. Plotting diagnostic time series

Recommended entry point:

    pydf-plot-diagnostics --input-file outputs\baseline_reduced_sparse\time_series.csv

Equivalent developer command:

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m scripts.plot_diagnostics --input-file outputs\baseline_reduced_sparse\time_series.csv

Use simulation time instead of stand age on the x-axis with:

    pydf-plot-diagnostics --x-key time

## 16. Syntax checks

### Compile a single Python file

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m py_compile pydynamicforest\solver.py

### Compile all package files

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m compileall pydynamicforest

## 17. Outputs

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

## 18. Development notes

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

### Model-field evaluation mode

The solver now uses an intermediate model-field evaluation wrapper:

    evaluate_model_fields_for_solver(state, p, context=None)

The behavior is controlled by:

    p.numerics.model_field_evaluation

Currently supported values are:

    model_field_evaluation="legacy"
    model_field_evaluation="state"

The default baseline configuration uses:

    model_field_evaluation="legacy"

This means that the solver still uses the validated legacy time-based model-field evaluation pathway.

The `"state"` mode is preparatory. It calls the state-aware interface:

    evaluate_state_model_fields(
        p,
        state,
        derived=None,
        context=None,
    )

This is intended for future model laws depending on:

- the current state `U`;
- derived quantities;
- the simulation context.

At this stage, the `"state"` mode is not the default production pathway.

## 19. Common troubleshooting

### Python points to the wrong executable

Check:

    where python
    python -c "import sys; print(sys.executable)"

If needed, use the explicit interpreter:

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe

### Console entry points are not found

If commands such as `pydf-run-baseline` are not found, check whether the environment `Scripts` directory is in the `PATH`.

Expected directory:

    C:\Users\saintemarie\.conda\envs\pydynamicforest\Scripts

Use the full executable path if needed:

    C:\Users\saintemarie\.conda\envs\pydynamicforest\Scripts\pydf-run-baseline.exe --preset short-debug --output-dir outputs\short_debug

Temporarily update the current terminal:

    set "CONDA_ENV=C:\Users\saintemarie\.conda\envs\pydynamicforest"
    set "PATH=%CONDA_ENV%;%CONDA_ENV%\Scripts;%CONDA_ENV%\Library\bin;%PATH%"

### `ModuleNotFoundError: No module named 'simulations'`

Run scripts as modules from the repository root:

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m scripts.run_baseline

rather than:

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe scripts\run_baseline.py

### Matplotlib / Tk issue

Plotting uses the non-interactive `Agg` backend in `pydynamicforest/plotting.py`.

This avoids errors related to missing Tk libraries when generating figures in tests or batch runs.

## 20. Recommended daily workflow

A typical development cycle is:

    git status
    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m pytest tests
    pydf-run-baseline --preset short-debug --output-dir outputs\short_debug
    git add <modified_files>
    git commit -m "Meaningful commit message"
    git push origin refactor-julien

If the `pydf-*` commands are not available, use the explicit Python module form:

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m scripts.run_baseline --preset short-debug --output-dir outputs\short_debug

For model-field interface checks, run:

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m pytest tests\test_model_field_evaluation.py tests\test_model_field_evaluation_mode.py

For deeper validation, run:

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m pytest tests -m slow
    pydf-compare-reduced-reference

For end-to-end CLI validation, run:

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m pytest tests\test_end_to_end_cli.py -m e2e