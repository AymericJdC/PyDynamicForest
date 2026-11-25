# Notes on Modele2DImpliciteV3.py

This file records factual information about the archived legacy script:

    Modele2DImpliciteV3.py

The script is associated with the numerical simulations reported in the manuscript initially submitted to the Journal of Mathematical Biology.

It is kept for traceability and should not be modified directly.

## Numerical domain

The script uses normalized computational variables on:

    (0, 1) x (0, 1)

with physical scales:

    Hphys = 50.0
    Dphys = 1.0

## Time discretization

The simulation horizon is:

    T = 51

The numerical discretization is:

    Nx = 40
    Ny = 40
    Nt = 10000

## Initial condition

The initial number of trees per hectare is:

    N0 = 1924.34

The Gaussian initial condition is centered at:

    h0 = 9.61 m
    d0 = 0.1169 m

with standard deviations:

    sigma_h = 1.3 m
    sigma_d = 0.025 m

## Model coefficients

The diffusion coefficient is constant:

    D = 1e-5

The mortality coefficient is constant:

    K = 0.033

The growth coefficients are:

    height growth coefficient = 1.66 m / yr
    DBH growth coefficient = 0.0155 m / yr

In normalized coordinates, the script uses:

    rh = 1.66 / Hphys
    rd = 0.0155 / Dphys

## Diagnostics and data comparison

The script computes or plots:

- height distributions;
- DBH distributions;
- total number of trees per hectare;
- dominant height;
- basal area;
- minimum density value for positivity checks.

The empirical data arrays included in the script correspond to the stand-level data used in the submitted manuscript.

## Relation to the refactored code

This archived script is not part of the refactored `pydynamicforest` package.

The refactored implementation is maintained separately and is intended to improve modularity, testing and extensibility while preserving selected validated legacy behaviors.

A cleaned or refactored reproduction of this scenario, if needed later, should be created as a separate scenario rather than by modifying this archived script.