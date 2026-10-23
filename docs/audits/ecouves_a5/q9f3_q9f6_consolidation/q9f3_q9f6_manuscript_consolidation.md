# Scientific consolidation Q-9F.3 to Q-9F.6 - Ecouves A5

Branch: `feature/observation-quadrature`
HEAD: `1bc25d377ca265a7a05a407715fde7704b16e256`

## Scope

Read-only consolidation of existing outputs. No simulation, recalibration or test was run. Q-9F.7 is deliberately excluded.

## Git status at extraction

```text
?? consolidate_q9f3_q9f6_results.py
?? q9f3_q9f6_scientific_results.csv
```

## Inventory

- **Q-9F.3**: 8 files.
- **Q-9F.4**: 83 files.
- **Q-9F.5**: 3 files.
- **Q-9F.6**: 4 files.

Detailed machine-readable inventory: `q9f3_q9f6_scientific_results.csv`.

## Q-9F.3 - Distributional diagnosis

### Intended scientific use

Assess whether the empirical initialization improves the representation of diameter and height distributions, and identify which mismatches persist dynamically. Distinguish marginal agreement from joint-structure agreement.

### Manuscript rule

Use only diagnostics directly supported by reconstructed empirical states. Do not present deterministic reconstructed heights as measured height distributions.

## Q-9F.4 - Local mechanistic screening

### Intended scientific use

Report local response to controlled perturbations of growth, diffusion and mortality mechanisms. This is a screening analysis, not parameter calibration, uncertainty quantification or identifiability analysis.

### Manuscript rule

Prefer robust signs, rankings and mechanism-specific patterns. Avoid interpreting correlated parameter effects as independently estimable contributions.

## Q-9F.5 - Height hierarchy

### Intended scientific use

Determine whether discrepancies in dominant and mean height arise from the empirical initial state, global height-growth activation, or the hierarchy encoded by the status function.

### Manuscript rule

Keep separate the global activation of height growth and its hierarchical allocation among size classes.

## Q-9F.6 - Vertical growth allocation

### Intended scientific use

Assess how the model allocates vertical growth across the stand distribution and whether the status-dependent mechanism reproduces the observed hierarchy without violating conservation.

### Manuscript rule

Discuss this as a structural diagnostic. Do not reuse the rejected non-conservative status transformations of Q-9F.7.

## Extracted summary statements requiring scientific verification

### Q-9F.3

- No summary bullet was automatically extracted; inspect the detailed CSV and source outputs.

### Q-9F.4

- No summary bullet was automatically extracted; inspect the detailed CSV and source outputs.

### Q-9F.5

- No summary bullet was automatically extracted; inspect the detailed CSV and source outputs.

### Q-9F.6

- No summary bullet was automatically extracted; inspect the detailed CSV and source outputs.

## Decisions to make before manuscript drafting

1. Select the few diagnostics that support claims robustly across observation years.
2. Separate findings caused by empirical initialization from findings caused by the dynamic model.
3. Record all comparisons against GIS Coop aggregates and Francois Ningre inventories by source; do not silently reconcile small discrepancies.
4. Mark all height-distribution findings that depend on deterministic reconstructed heights.
5. Decide which results belong in the main text and which belong in the supplement.
6. Exclude Q-9F.7 transformed trajectories from biological interpretation.

## Next review

Review the generated CSV and this report, then produce an evidence matrix linking each proposed manuscript claim to exact output files, variables, years and numerical values.
