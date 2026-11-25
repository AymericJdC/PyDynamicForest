# Ecouves A5: temporal-domain decision

## Purpose

This note records the temporal-domain choices used to prepare the numerical experiments for the article. It contains no empirical inventory values and does not replace the restricted source data or the machine-readable outputs generated locally from them.

## Age convention

The numerical workflow retains the age convention used in the GIS Coop dataset supplied for the article workflow. For matched Ecouves A5 inventories, this convention is systematically one year greater than the convention used in the independent chronology file consulted during the audit.

The alternative chronology is retained only to document provenance and correspondence between inventory years and reported ages. The article calculations continue to use the GIS Coop convention so that the revised experiments remain consistent with the existing observation operators, numerical workflow, and previous calculations.

## Objective biological-domain criterion

The temporal domain is selected from the size-density analysis reported by Ningre et al. (2016). For the density group containing Ecouves A5, the published criterion identifies the quadratic mean circumference at which maximum relative density is reached.

Applying this criterion to the available GIS Coop inventories leads to three distinct numerical experiments:

1. **Main simulation**: start at the first available inventory clearly located beyond the published group threshold, using GIS Coop age 45.
2. **Transition sensitivity**: start at the preceding inventory, using GIS Coop age 38, to examine a stand state close to the transition into the maximum-density regime.
3. **Historical out-of-domain experiment**: retain the age-18 start as a diagnostic of model behaviour before the biological assumptions of strong competition and active self-thinning are expected to hold.

## Modelling consequences

For the first comparison, the dynamic laws, dynamic parameters, normalized status function, observation operators, spatial discretization, and time-stepping scheme remain unchanged. Only the following elements change:

- initial age;
- reconstructed initial distribution;
- simulation duration;
- set of subsequent inventories used for comparison.

The purpose is to isolate the effect of applying the reduced model within, near, or before its intended biological domain. Dynamic parameters must not be recalibrated before this comparison has been completed.

## Initial-state reconstruction

Individual-tree data are not yet used in this revision. The initial height and DBH marginal distributions will therefore be reconstructed separately and assembled with a Gaussian copula. This construction is a provisional modelling assumption, not a statistical estimate of the empirical joint distribution.

If the dependence parameter is not identifiable from the available stand-level observables, several plausible dependence values and compatible height dispersions will be examined. The reconstruction must report the extent to which it reproduces stand density, basal area, arithmetic and quadratic mean DBH, DBH dispersion, mean height, dominant height, and the dominant-minus-mean height contrast.

## Data governance

The empirical source files and derived tables containing inventory values are not stored in the public version-controlled repository while redistribution conditions are being clarified with the data provider. Local paths and restricted filenames must not be embedded in the scientific code or documentation.

The repository may contain:

- code that reads an externally supplied input table;
- a documented input schema;
- synthetic example data;
- this decision note;
- reproducible numerical methods and tests that do not redistribute restricted observations.

## Status

This is the current working decision for the numerical revision. The terminology and empirical interpretation will be updated if the data provider supplies additional documentation or individual-tree inventories.
