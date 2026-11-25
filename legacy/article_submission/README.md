# Article submission legacy script

This directory contains the legacy Python script associated with the numerical simulations reported in the manuscript initially submitted to the Journal of Mathematical Biology.

The file:

    Modele2DImpliciteV3.py

is kept for traceability. It is not part of the refactored `pydynamicforest` package.

The script contains the numerical parameter values reported in the submitted manuscript, including the initial stand density, Gaussian initial condition parameters, growth coefficients, mortality coefficient, diffusion coefficient, grid size and simulation time horizon.

The current refactored implementation is maintained separately. It is a modular technical reimplementation intended to improve maintainability, testing and future extensibility while preserving the behavior of selected validated legacy reference cases.

This archived script should not be modified directly. If a cleaned or executable version is needed later, it should be created as a separate file.