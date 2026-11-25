# Article data for the Ecouves numerical experiments

## Scope

This directory documents the empirical inputs expected by the numerical workflow associated with the article. The empirical Ecouves data are not included in the public repository while their redistribution conditions are being clarified with the data provider.

Do not commit source files, extracts, or derived tables containing empirical inventory values unless written authorization and the intended archival conditions have been confirmed.

## Expected input variables

The article workflow expects one row per inventory and the following information:

- stand age under the convention retained for the article;
- stand density, in trees per hectare;
- basal area, in square metres per hectare;
- arithmetic mean DBH, in centimetres;
- mean height, in metres, when available;
- reported dominant height, in metres, when available.

The workflow may derive:

- quadratic mean DBH;
- DBH standard deviation;
- dominant-minus-mean height contrast;
- quadratic mean circumference;
- chronological and biological-domain indicators.

Derived variables must be computed by the workflow rather than copied manually into version-controlled files.

## Data location

Empirical inputs must be supplied from a local or access-controlled directory outside the public Git repository. Their location should be provided through a command-line argument, environment variable, or local configuration file excluded from Git.

The code must not rely on a user-specific absolute path.

## Permitted repository contents

The following items may be versioned in this directory:

- this README;
- the `.gitignore` file;
- an input-data schema;
- documentation of variable names, units, missing-value conventions, and validation rules;
- clearly labelled synthetic examples containing no empirical observations.

## Prohibited repository contents pending authorization

Do not commit:

- externally supplied CSV, Excel, or database extracts;
- individual-tree inventories;
- derived tables reproducing empirical inventory values;
- local correspondence tables between restricted datasets;
- temporary exports created for figures or manuscript tables;
- files containing sensitive or undocumented experimental metadata.

## Reproducibility and publication

Before submission or public archival, the project must define:

1. whether a machine-readable stand-level table may be redistributed;
2. whether access must instead be requested from the data provider;
3. the citation and acknowledgement required by the data provider;
4. the repository and persistent identifier for the archived software and permitted outputs;
5. the licence and contributor rights applying to the software release.

If redistribution is authorized, the publication dataset should contain only the variables needed to reproduce the article and should be deposited through an approved archival route. If redistribution is not authorized, the Data Availability Statement must describe the validated access procedure.
