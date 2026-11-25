# Q-9E.2 - Generic height-provider interface

Q-9E.2 defines an allometry-independent API. It does not select, fit, calibrate or randomize any height-diameter relationship.

## Contract

A `HeightProvider` receives immutable `TreeRecord` objects and a `StandContext`, then returns exactly one `AssignedHeight` per tree. Missing values are explicit. Providers may not alter Q-9E.1 diameters, weights or inclusion rules.

Available providers are `ObservedHeightProvider`, `FixedHeightProvider` (tests only), `CallableHeightProvider`, `MissingHeightProvider`, and `CompositeHeightProvider`. The composite uses ordered fallback: the first valid height wins.

## Units and uncertainty

Diameters and circumferences use centimetres, heights use metres, plot area uses hectares, and weights use trees per hectare. Unknown uncertainty differs from zero uncertainty. Supported representations are unknown, not applicable, standard deviation, and interval.

## Diagnostics

Diagnostics use only valid heights and always report weighted coverage. The quadratic mean is `sqrt(sum(w * H^2) / sum(w))`. Slenderness is `100 * H_m / D_cm`. Weighted height-diameter correlation is undefined when either variance is zero.

Dominant height is the weighted mean height of the 100 largest-diameter trees per hectare. The last included weight is fractional. If the threshold crosses a diameter tie, the residual weight is allocated proportionally across the tied group. If valid-height density is below 100 trees/ha, dominant height is missing with status `insufficient_density`.

Target comparison is diagnostic only and never changes assigned heights.

## Q-9E.1 adapter

`reference_state` is the default mode and consumes only rows marked `included_in_reference_state`. `measured_inventory` must be requested explicitly for audit years. Thus 2013 remains an audit year and is never silently promoted to a reference state.

## Out of scope

Savine et al., Douglas-specific allometries, parameter fitting, stochastic draws, copulas, grid projection and dynamic simulations remain outside Q-9E.2.
