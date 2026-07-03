# PyDynamicForest

PyDynamicForest is a Python research code for simulating size-structured forest stand dynamics.

The model describes the evolution of a tree density distribution structured by height and DBH.
The repository is currently being refactored from an initial research script into a modular, maintainable and scientifically traceable codebase.

## Current status

The current refactor introduces the API:

    results = simulate(x0, p, c, solver_name="sparse")

where `x0` is an `InitialCondition`, `p` is a `Parameters` object, `c` is a `SimulationContext`, and `results` is a `SimulationResults` object.

The sparse solver has been validated against the reduced legacy reference case up to numerical precision.

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

Main dependencies: numpy, scipy, matplotlib, pytest.

## Tests

Run fast tests with:

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m pytest tests

Run slow tests with:

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m pytest tests -m slow

Run all tests, including slow tests, with:

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m pytest tests -m "slow or not slow"

## Simulations

Run the short baseline scenario with:

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m simulations.baseline.run

Run the full reduced sparse baseline with:

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m scripts.run_baseline_reduced_sparse

## Validation against legacy references

The original implementation is preserved in the `legacy/` directory.

Compare the sparse refactored solver with the reduced legacy reference using:

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m scripts.compare_reduced_reference

The comparison checks final top height, final basal area, final legacy mass, and minimum density over the trajectory.

## Observation management

The simulation context supports observation selection by stand age.

Example: `observation_ages` can be set to 18.0, 45.0, and 69.0 with `save_full_trajectory` set to `False`.

This avoids hard-coded indices such as:

    U[5294,:,:]

In PyDynamicForest, observations are simulated model states selected for storage and analysis at requested stand ages.
They should not be confused with empirical field observations.

## Output files

Simulation outputs are written to the `outputs/` directory, which is ignored by Git.

A typical output directory contains:

    time_series.csv
    metadata.json
    summary.txt
    observations/
    figures/

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

    C:\Users\saintemarie\.conda\envs\pydynamicforest\python.exe -m scripts.plot_observations

This command reads exported observations from:

    outputs/baseline_reduced_sparse/observations/

and writes figures to:

    outputs/baseline_reduced_sparse/figures/

For each observation, the script currently generates:

- a 2D density field;
- a height distribution;
- a DBH distribution.

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

Future scientific extensions such as recruitment, alternative mortality laws, alternative growth functions and alternative status definitions remain to be implemented.

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

Please refer to the repository license file if available.