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

## Snapshot management

The simulation context supports snapshot selection by stand age.

Example: `snapshot_ages` can be set to 18.0, 45.0, and 69.0 with `save_full_trajectory` set to `False`.

This avoids hard-coded indices such as:

    U[5294,:,:]

## Output files

Simulation outputs are written to the `outputs/` directory, which is ignored by Git.

A typical output directory contains:

    time_series.csv
    metadata.json
    summary.txt

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

The distinction between legacy mass, trapezoidal mass, and scientific diagnostic mass still needs to be clarified.

Quadrature conventions should be harmonized across diagnostics.

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