# Dominant-height sensitivity studies

This directory contains controlled experiments that isolate the numerical
behaviour of dominant-height observation operators from the forest-dynamics
solver.

## Operator status

- `legacy_top_height` reproduces the convention used by the manuscript-associated
  script: decreasing DBH, then decreasing height within DBH ties.
- `top_height` is retained for backward comparison. Its tie-breaking depends on
  array traversal order and is not a scientifically endorsed definition.
- `proportional_top_height` is the preferred candidate for revised scientific
  outputs. It applies a uniform fraction to all heights in the threshold DBH
  class.

## Established evidence

On the 10,000-step manuscript-associated trajectory, the proportional operator
reduced the maximum one-step change from 0.022224 m for the legacy convention
and 0.024423 m for the current convention to 0.007350 m. It also reduced the
RMS increment and total variation.

In controlled DBH-grid experiments (`Ny = 20, 40, 80, 160`), the proportional
operator approached a fine proportional reference much more closely than the
two height tie-breaking conventions, especially when the threshold DBH class
contained a dispersed or bimodal height distribution.

## Commands

Run the isolated mesh study:

```bash
python -m simulations.dominant_height_sensitivity.run \
  --output-dir outputs/dominant_height_mesh_sensitivity
```

Consolidate the fine-grid reference using `Ny = 640, 1280, 2560`:

```bash
python -m simulations.dominant_height_sensitivity.consolidate \
  --output-dir outputs/dominant_height_consolidation
```

## Interpretation limits

- The finest grid is a numerical reference, not an analytical solution.
- Height resolution remains fixed while DBH resolution is refined.
- These experiments test observation operators, not convergence of the dynamic
  solver.
- The current operators retain rectangular cell weights.
- Final adoption still requires alignment with the dominant-height definition
  used for the Ecouves field observations.
