# Q-9E.5 - Native PyDynamicForest state integration

Q-9E.5 converts Q-9E.4 nodal stem masses to the native PyDynamicForest state convention. The native array order is height then DBH, with shape `(nx, ny)`. Grid coordinates are normalized; physical nodes are obtained with the configured height and DBH scales. `U` is density per normalized coordinate area and is integrated with native tensor-product trapezoidal weights.

Conversion uses nodal masses rather than physical density interpolation. Each source node is conservatively redistributed to at most four native nodes. Native density is then `nodal_mass / native_quadrature_weight`. Total density and first physical moments are conserved when the source support lies inside the native domain. Strict domain handling is the default. Explicit clipping is diagnostic only.

The main candidate is inventory year 1992, corresponding to GIS Coop age 45. Other scientific-series years remain available for diagnostics. The adapter records the height-provider identifier and does not depend on Savine-specific code, so observed or institutional heights can replace the provisional provider upstream without changing the native-state contract.

Q-9E.5 does not advance the solver, recalibrate dynamic parameters, alter the numerical grid, or correct second moments. Dg, basal area and dominant height are compared before and after conversion.
