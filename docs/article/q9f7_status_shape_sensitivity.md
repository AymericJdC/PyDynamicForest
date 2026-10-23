# Q-9F.7 - Controlled sensitivity to status-allocation shape

Q-9F.7 tests `S^gamma` for gamma 0.75, 1.00 and 1.25. Within each step, the transformation is applied exclusively to the height-transport term. DBH transport and mortality use the baseline status evaluated from that step's incoming state. Across steps, however, the altered state feeds back into all state-dependent mechanisms, so full-trajectory effects are not confined to height observables.

Gamma 1 is an exact non-regression control. Gamma below 1 raises low status values proportionally more than high values; gamma above 1 sharpens the contrast. The design is a mechanistic sensitivity experiment, not a calibration. Results are compared at 1998, 2016 and 2020 using stand summaries, distribution distances and relative-DBH hierarchy diagnostics.

The alternative one-step routine remains article-specific and does not change the validated package solver. No gamma is promoted to the baseline by this lot.

## Diagnostic conclusion

The raw pointwise transformation `S -> S^gamma` is not admissible in the
current discrete transport scheme. For gamma different from one, it breaks the
zero-integral property of the native height-transport term and produces an
immediate artificial change in stand density.

At the first step, the alternative-minus-reference density change is equal,
up to numerical rounding, to minus the time step multiplied by the difference
between transformed and baseline integrated height-transport terms. Gamma below
one creates an artificial sink; gamma above one creates an artificial source.

Consequently, non-unit gamma trajectories are retained only as rejected
numerical experiments. They must not be interpreted biologically or used for
calibration. Gamma one remains the exact non-regression control.
