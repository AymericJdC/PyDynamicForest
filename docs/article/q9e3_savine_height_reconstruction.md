# Q-9E.3 - Provisional Douglas height reconstruction

Q-9E.3 applies the fixed-effect, even-aged *Pseudotsuga menziesii* relation reported by Savine et al. in supplementary Table S5. It uses individual DBH, weighted quadratic mean diameter and stand basal area. Units are cm, cm, m²/ha and m respectively.

The implemented equation is:

`H = 1.3 + 45.07*(1 + 0.00160*BA)*(1 - exp(-0.00718*Dg^1.45561)) / (1 + 0.39143*exp(-0.00652*BA)/(dbh/Dg)^1.74230)`.

The stand is treated as even-aged and the unobserved local effect is fixed to zero. The published residual standard deviation (1.85 m) is metadata and uncertainty information only; it is not used for random draws. The published Douglas DBH calibration range is 7.51–140.69 cm. Published Douglas-specific BA and Dg limits are unavailable, so the software does not invent them.

Permissive mode predicts and flags DBH extrapolations. Strict mode returns explicit missing heights outside the published DBH range. No target aggregate is used to recalibrate predictions.
