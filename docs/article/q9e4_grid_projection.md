# Q-9E.4 - Conservative projection and regularisation

Weighted individual `(height, diameter)` states are projected to tensor-grid nodes with compact bilinear basis functions. Each tree contributes to at most four nodes. Nodal mass is converted to density using tensor trapezoidal weights, so trapezoidal integration preserves total density and first moments in height and diameter to floating-point precision.

This is a numerical regularisation, not a biological smoothing model. It does not impose second moments, basal area, quadratic mean diameter or dominant height. These quantities are reported before and after projection. Strict boundaries reject out-of-grid trees; clipping is available only as an explicit diagnostic mode.

The output NPZ files contain `height_m`, `diameter_cm`, `density_ha_per_m_per_cm` and `nodal_mass_ha`. Q-9E.4 does not launch the dynamic model or alter its parameters.
