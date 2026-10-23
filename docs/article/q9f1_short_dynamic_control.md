# Q-9F.1 - Short dynamic control from the reconstructed 1992 state

The control loads the native Q-9E.5 state for inventory year 1992, uses GIS Coop simulation age 45, and advances the unchanged article model for a small configurable number of sparse legacy time steps. It verifies initial-state copying, finite values, positivity within the configured tolerance, status-field bounds, age and step progression, and the evolution of native observation operators.

This is a numerical integration check, not biological validation. It does not recalibrate growth, mortality or diffusion, does not change the numerical grid, and does not make the provisional height provider permanent. The full age-45 to age-73 comparison belongs to Q-9F.2.
