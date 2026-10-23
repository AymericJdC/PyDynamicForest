# Q-9F.6 - Audit of global height growth and hierarchical allocation

Q-9F.6 inspects the reference trajectory without running alternative dynamics. In the validated legacy solver, height transport uses the height-growth coefficient field as face velocity and transports the status-weighted density `S[U] U`. The status field is the normalized joint lower-tail cumulative distribution in height and DBH. It is therefore a two-dimensional state functional, not a pure DBH dominance rank.

The audit reports, by state-specific relative-DBH class and year, density share, density-weighted status, global height-growth field, effective vertical velocity `growth × status`, and the integrated height-transport divergence. The height-growth field is spatially variable. The audit therefore separates its class mean, the class mean status, their covariance, and the resulting mean effective vertical velocity.

No alternative status function, exponent or parameter is introduced in this lot. The integrated transport term is a numerical flux diagnostic and must not be interpreted as individual longitudinal height growth. The result will determine whether a later sensitivity should alter the global rate, the shape of the status allocation, or neither.
