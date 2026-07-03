# PyDynamicForest command reference

This file summarizes the main commands used during the refactor and development of PyDynamicForest.

The examples below assume that commands are run from the root directory of the repository.

---

## 1. Environment

### Activate the conda environment

```bat
conda activate pydynamicforest
```

### Use the explicit Python interpreter

If the conda activation does not correctly select the Python interpreter, use:

```bat
C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe
```

### Recreate the conda environment

```bat
conda env create -f environment.yml
conda activate pydynamicforest
```

### Install dependencies from requirements.txt

```bat
C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m pip install -r requirements.txt
```

---

## 2. Git workflow

### Check current branch and status

```bat
git branch
git status
```

### Stage and commit changes

```bat
git add <file_or_directory>
git commit -m "Commit message"
```

### Push the refactor branch

```bat
git push origin refactor-julien
```

### Restore a modified file

```bat
git restore path\to\file.py
```

### Show differences in a file

```bat
git diff path\to\file.py
```

---

## 3. Tests

### Run the fast test suite

By default, slow tests are excluded through `pytest.ini`.

```bat
C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m pytest tests
```

### Run only slow tests

```bat
C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m pytest tests -m slow
```

### Run all tests, including slow tests

```bat
C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m pytest tests -m "slow or not slow"
```

### Run a specific test file

```bat
C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m pytest tests\test_observations.py
```

### Run a specific test by name

```bat
C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m pytest tests -k "observation"
```

---

## 4. Baseline simulations

### Run the short baseline scenario

```bat
C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m simulations.baseline.run
```

This runs a short sparse simulation, typically with:

```python
max_steps=10
solver_name="sparse"
```

### Run the full reduced sparse baseline

```bat
C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m scripts.run_baseline_reduced_sparse
```

This runs the reduced baseline case:

```text
Nx = 20
Ny = 20
Nt = 1000
solver = sparse
```

Outputs are written to:

```text
outputs/baseline_reduced_sparse/
```

---

## 5. Legacy references

### Run the short legacy reference

```bat
C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe legacy\DynamicForestModel_2D_short_reference.py > reference_outputs\legacy_short_console_output.txt
```

### Run the reduced legacy reference

```bat
C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe legacy\DynamicForestModel_2D_reduced_reference.py > reference_outputs\legacy_reduced_console_output.txt
```

Warning: the reduced legacy reference uses the dense legacy solver and may be slower than the refactored sparse solver.

---

## 6. Comparisons and validation

### Compare sparse refactor with reduced legacy reference

```bat
C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m scripts.compare_reduced_reference
```

This compares:

- final top height;
- final basal area;
- final legacy mass;
- minimum density over the trajectory.

### Expected validation status

For the reduced reference case, the sparse refactored solver should match the legacy reduced reference up to numerical precision.

Typical discrepancies are expected to be close to machine precision.

---

## 7. Syntax checks

### Compile a single Python file

```bat
C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m py_compile pydynamicforest\solver.py
```

### Compile all package files

```bat
C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m compileall pydynamicforest
```

---

## 8. Outputs

Simulation outputs are currently written under:

```text
outputs/
```

This directory is ignored by Git.

Example:

```text
outputs/baseline_reduced_sparse/
├── time_series.csv
├── metadata.json
└── summary.txt
```
### Observation files

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
---

## 9. Development notes

### Main conceptual API

```python
results = simulate(x0, p, c, solver_name="sparse")
```

where:

- `x0` is an `InitialCondition`;
- `p` is a `Parameters` object;
- `c` is a `SimulationContext`;
- `results` is a `SimulationResults` object.

### Current solvers

```python
solver_name="dense"
solver_name="sparse"
```

The dense solver is kept as a regression reference.

The sparse solver is preferred for practical simulations.

### Observation management

Observations can be requested through the simulation context:

```python
OutputSpecification(
    observation_ages=[18.0, 45.0, 69.0],
    save_full_trajectory=False,
)
```

When `save_full_trajectory` is `False`, only states close to the requested stand ages are stored in `results.observations`.

---

## 10. Common troubleshooting

### Python points to the wrong executable

Check:

```bat
where python
python -c "import sys; print(sys.executable)"
```

If needed, use the explicit interpreter:

```bat
C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe
```

### `ModuleNotFoundError: No module named 'simulations'`

Run scripts as modules from the repository root:

```bat
C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m scripts.run_baseline_reduced_sparse
```

rather than:

```bat
C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe scripts\run_baseline_reduced_sparse.py
```

### Windows encoding issue in redirected legacy outputs

Some legacy outputs may be encoded with Windows console encoding. The comparison scripts handle this by trying UTF-8 first and falling back to cp1252.

---

## 11. Recommended daily workflow

A typical development cycle is:

```bat
git status
C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m pytest tests
C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m simulations.baseline.run
git add <modified_files>
git commit -m "Meaningful commit message"
git push origin refactor-julien
```

For deeper validation, run:

```bat
C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m pytest tests -m slow
C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m scripts.compare_reduced_reference
```
