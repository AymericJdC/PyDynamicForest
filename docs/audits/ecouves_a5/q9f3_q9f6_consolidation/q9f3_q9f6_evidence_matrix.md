# Q-9F.3--Q-9F.6 manuscript evidence matrix

Branch: `feature/observation-quadrature`
HEAD: `1bc25d377ca265a7a05a407715fde7704b16e256`

## Scope

Only the four empirical Ecouves A5 result directories are used. Historical copula sensitivities, generic earlier experiments and Q-9F.7 are excluded.

## Proposed claims

### Q-9F.3

#### Q9F3-dbh_cm

The empirical initialization does not eliminate the diameter-distribution mismatch during the trajectory.

- **Evidence:** W1 range 1.097--2.727; maximum CDF distance range 0.081--0.151 across 1998, 2016, 2020.
- **Years:** 1998, 2016, 2020
- **Robustness:** moderate
- **Placement:** Supplementary results; concise mention in main discussion
- **Limit:** Only three comparison years are available.
- **Files:** `outputs/article_scenarios/ecouves_a5_distributional_diagnostics/ecouves_a5_distribution_metrics.csv`

#### Q9F3-height_m

The empirical initialization does not eliminate the height-distribution mismatch during the trajectory.

- **Evidence:** W1 range 1.730--3.680; maximum CDF distance range 0.177--0.301 across 1998, 2016, 2020.
- **Years:** 1998, 2016, 2020
- **Robustness:** moderate
- **Placement:** Supplementary results; concise mention in main discussion
- **Limit:** Height targets are deterministic reconstructions, not measured individual heights.
- **Files:** `outputs/article_scenarios/ecouves_a5_distributional_diagnostics/ecouves_a5_distribution_metrics.csv`

#### Q9F3-joint-correlation

The simulated height--diameter dependence is systematically weaker than in the reconstructed empirical targets.

- **Evidence:** Simulated correlation 0.838--0.841 versus target 0.934--0.937.
- **Years:** 1998, 2016, 2020
- **Robustness:** high within reconstructed-target framework
- **Placement:** Main results/discussion
- **Limit:** The target joint structure inherits the deterministic height--diameter reconstruction.
- **Files:** `outputs/article_scenarios/ecouves_a5_distributional_diagnostics/ecouves_a5_joint_structure_metrics.csv`

#### Q9F3-height-gap

The model overstates the vertical hierarchy measured by the dominant-minus-mean height gap.

- **Evidence:** Simulated H0-Hm 4.923--7.277 m versus target 3.731--4.037 m.
- **Years:** 1998, 2016, 2020
- **Robustness:** high within reconstructed-target framework
- **Placement:** Main results and biological discussion
- **Limit:** Dominant-height definition and reconstructed heights must remain explicit.
- **Files:** `outputs/article_scenarios/ecouves_a5_distributional_diagnostics/ecouves_a5_joint_structure_metrics.csv`

#### Q9F3-quantiles

Distributional errors are not restricted to the mean and extend across quantiles.

- **Evidence:** Simulated-minus-target quantile differences range from -9.511 to 3.005 in the native units of the dimension.
- **Years:** 1998, 2016, 2020
- **Robustness:** moderate
- **Placement:** Supplementary material
- **Limit:** Diameter and height differences should not be pooled into a single unitless effect.
- **Files:** `outputs/article_scenarios/ecouves_a5_distributional_diagnostics/ecouves_a5_distribution_quantiles.csv`

### Q-9F.4

#### Q9F4-overall-ranking

The local OAT screening reveals strongly mechanism-dependent responses rather than a uniform improvement direction.

- **Evidence:** height_growth: mean |E|=0.160, max |E|=0.896; dbh_growth: mean |E|=0.141, max |E|=0.749; mortality: mean |E|=0.129, max |E|=0.541; diffusion: mean |E|=0.011, max |E|=0.046
- **Years:** 1998, 2016, 2020
- **Robustness:** moderate
- **Placement:** Supplementary results; mechanism summary in discussion
- **Limit:** Local +/-20% OAT screening only. It is not calibration, global sensitivity analysis or identifiability analysis.
- **Files:** `outputs/article_scenarios/ecouves_a5_mechanistic_sensitivity/ecouves_a5_mechanistic_elasticities.csv | outputs/article_scenarios/ecouves_a5_mechanistic_sensitivity/ecouves_a5_mechanistic_sensitivity_cases.csv | outputs/article_scenarios/ecouves_a5_mechanistic_sensitivity/ecouves_a5_mechanistic_sensitivity_metadata.json`

#### Q9F4-N

For N, the largest local response among the screened mechanisms is associated with mortality.

- **Evidence:** Maximum |elasticity|=0.541 at year 2020; signed elasticity=-0.541.
- **Years:** 2020
- **Robustness:** exploratory
- **Placement:** Supplementary evidence matrix
- **Limit:** Ranking may depend on perturbation size, initial state and year; do not interpret as parameter identifiability.
- **Files:** `outputs/article_scenarios/ecouves_a5_mechanistic_sensitivity/ecouves_a5_mechanistic_elasticities.csv`

#### Q9F4-G

For G, the largest local response among the screened mechanisms is associated with dbh_growth.

- **Evidence:** Maximum |elasticity|=0.529 at year 2020; signed elasticity=0.529.
- **Years:** 2020
- **Robustness:** exploratory
- **Placement:** Supplementary evidence matrix
- **Limit:** Ranking may depend on perturbation size, initial state and year; do not interpret as parameter identifiability.
- **Files:** `outputs/article_scenarios/ecouves_a5_mechanistic_sensitivity/ecouves_a5_mechanistic_elasticities.csv`

#### Q9F4-Hm

For Hm, the largest local response among the screened mechanisms is associated with height_growth.

- **Evidence:** Maximum |elasticity|=0.182 at year 2020; signed elasticity=0.182.
- **Years:** 2020
- **Robustness:** exploratory
- **Placement:** Supplementary evidence matrix
- **Limit:** Ranking may depend on perturbation size, initial state and year; do not interpret as parameter identifiability.
- **Files:** `outputs/article_scenarios/ecouves_a5_mechanistic_sensitivity/ecouves_a5_mechanistic_elasticities.csv`

#### Q9F4-H0

For H0, the largest local response among the screened mechanisms is associated with height_growth.

- **Evidence:** Maximum |elasticity|=0.200 at year 2020; signed elasticity=0.200.
- **Years:** 2020
- **Robustness:** exploratory
- **Placement:** Supplementary evidence matrix
- **Limit:** Ranking may depend on perturbation size, initial state and year; do not interpret as parameter identifiability.
- **Files:** `outputs/article_scenarios/ecouves_a5_mechanistic_sensitivity/ecouves_a5_mechanistic_elasticities.csv`

#### Q9F4-rho_HD

For rho_HD, the largest local response among the screened mechanisms is associated with dbh_growth.

- **Evidence:** Maximum |elasticity|=0.031 at year 2020; signed elasticity=0.031.
- **Years:** 2020
- **Robustness:** exploratory
- **Placement:** Supplementary evidence matrix
- **Limit:** Ranking may depend on perturbation size, initial state and year; do not interpret as parameter identifiability.
- **Files:** `outputs/article_scenarios/ecouves_a5_mechanistic_sensitivity/ecouves_a5_mechanistic_elasticities.csv`

#### Q9F4-W1_dbh_cm

For W1_dbh_cm, the largest local response among the screened mechanisms is associated with dbh_growth.

- **Evidence:** Maximum |elasticity|=0.412 at year 1998; signed elasticity=-0.412.
- **Years:** 1998
- **Robustness:** exploratory
- **Placement:** Supplementary evidence matrix
- **Limit:** Ranking may depend on perturbation size, initial state and year; do not interpret as parameter identifiability.
- **Files:** `outputs/article_scenarios/ecouves_a5_mechanistic_sensitivity/ecouves_a5_mechanistic_elasticities.csv`

#### Q9F4-W1_height_m

For W1_height_m, the largest local response among the screened mechanisms is associated with height_growth.

- **Evidence:** Maximum |elasticity|=0.657 at year 2020; signed elasticity=-0.657.
- **Years:** 2020
- **Robustness:** exploratory
- **Placement:** Supplementary evidence matrix
- **Limit:** Ranking may depend on perturbation size, initial state and year; do not interpret as parameter identifiability.
- **Files:** `outputs/article_scenarios/ecouves_a5_mechanistic_sensitivity/ecouves_a5_mechanistic_elasticities.csv`

#### Q9F4-no-recalibration

The mechanistic screening was performed without recalibrating dynamic parameters.

- **Evidence:** Eight cases; multipliers [0.8, 1.2]; dynamic_parameters_recalibrated=false.
- **Years:** 1998, 2016, 2020
- **Robustness:** high
- **Placement:** Methods/supplement
- **Limit:** This documents the design, not model performance.
- **Files:** `outputs/article_scenarios/ecouves_a5_mechanistic_sensitivity/ecouves_a5_mechanistic_sensitivity_metadata.json`

### Q-9F.5

#### Q9F5-1992

In 1992, the hierarchy comparison is exactly aligned by construction and provides the zero-discrepancy baseline for subsequent diagnostics.

- **Evidence:** Mean-height differences range 0.000 to 0.000 m; density-share differences 0.000 to 0.000; height-contribution differences 0.000 to 0.000. Largest height deficit: very_suppressed (0.000 m).
- **Years:** 1992
- **Robustness:** high within reconstructed-target framework
- **Placement:** Methods or supplementary validation
- **Limit:** This is an initialization control, not evidence of predictive performance.
- **Files:** `outputs/article_scenarios/ecouves_a5_height_hierarchy/ecouves_a5_height_hierarchy_comparison.csv`

#### Q9F5-1998

In 1998, the model redistributes density and height contributions across hierarchy classes and underestimates class mean height in the most affected class.

- **Evidence:** Mean-height differences range -2.280 to -0.513 m; density-share differences -0.136 to 0.093; height-contribution differences -3.966 to 2.383. Largest height deficit: very_suppressed (-2.280 m).
- **Years:** 1998
- **Robustness:** high within reconstructed-target framework
- **Placement:** Main results/discussion
- **Limit:** Target heights are reconstructed deterministically; class boundaries are defined by relative DBH.
- **Files:** `outputs/article_scenarios/ecouves_a5_height_hierarchy/ecouves_a5_height_hierarchy_comparison.csv`

#### Q9F5-2016

In 2016, the model redistributes density and height contributions across hierarchy classes and underestimates class mean height in the most affected class.

- **Evidence:** Mean-height differences range -4.250 to 0.094 m; density-share differences -0.083 to 0.150; height-contribution differences -3.138 to 3.074. Largest height deficit: very_suppressed (-4.250 m).
- **Years:** 2016
- **Robustness:** high within reconstructed-target framework
- **Placement:** Main results/discussion
- **Limit:** Target heights are reconstructed deterministically; class boundaries are defined by relative DBH.
- **Files:** `outputs/article_scenarios/ecouves_a5_height_hierarchy/ecouves_a5_height_hierarchy_comparison.csv`

#### Q9F5-2020

In 2020, the model redistributes density and height contributions across hierarchy classes and underestimates class mean height in the most affected class.

- **Evidence:** Mean-height differences range -4.379 to 0.407 m; density-share differences -0.134 to 0.144; height-contribution differences -4.926 to 3.000. Largest height deficit: very_suppressed (-4.379 m).
- **Years:** 2020
- **Robustness:** high within reconstructed-target framework
- **Placement:** Main results/discussion
- **Limit:** Target heights are reconstructed deterministically; class boundaries are defined by relative DBH.
- **Files:** `outputs/article_scenarios/ecouves_a5_height_hierarchy/ecouves_a5_height_hierarchy_comparison.csv`

#### Q9F5-overall

The hierarchy mismatch is class-specific, not a simple stand-wide vertical offset.

- **Evidence:** Across 24 class-year comparisons, mean-height differences range from -4.379 to 0.407 m while density-share differences sum to approximately zero within each year.
- **Years:** 1992, 1998, 2016, 2020
- **Robustness:** high within reconstructed-target framework
- **Placement:** Main biological discussion
- **Limit:** This establishes redistribution across classes, but not the causal mechanism by itself.
- **Files:** `outputs/article_scenarios/ecouves_a5_height_hierarchy/ecouves_a5_height_hierarchy_comparison.csv`

### Q-9F.6

#### Q9F6-allocation-gradient

The baseline model allocates effective vertical growth strongly along the hierarchy encoded by status.

- **Evidence:** Class mean status ranges 0.034--0.932; mean effective height velocity 7.084e-04--0.0140; mean height-growth field 0.0066--0.0213.
- **Years:** 1992, 1998, 2016, 2020
- **Robustness:** high
- **Placement:** Main mechanistic results/discussion
- **Limit:** This is a diagnostic of the implemented baseline mechanism, not evidence that the allocation is biologically correct.
- **Files:** `outputs/article_scenarios/ecouves_a5_height_growth_allocation_audit/ecouves_a5_height_growth_allocation_by_class.csv`

#### Q9F6-covariance

The growth-field/status covariance is consistently negative within hierarchy classes.

- **Evidence:** Covariance range -2.982e-04 to -1.453e-05 across 24 class-year combinations.
- **Years:** 1992, 1998, 2016, 2020
- **Robustness:** high numerically, interpretation pending
- **Placement:** Main discussion or supplement
- **Limit:** The covariance is descriptive and depends on the joint lower-tail cumulative status definition.
- **Files:** `outputs/article_scenarios/ecouves_a5_height_growth_allocation_audit/ecouves_a5_height_growth_allocation_by_class.csv`

#### Q9F6-audit-only

Q-9F.6 audits the existing allocation mechanism without modifying parameters or simulating an alternative status function.

- **Evidence:** alternative_status_function_simulated=false; dynamic_parameters_modified=false.
- **Years:** 1992, 1998, 2016, 2020
- **Robustness:** high
- **Placement:** Methods/supplement
- **Limit:** Alternative transformed trajectories from Q-9F.7 remain excluded.
- **Files:** `outputs/article_scenarios/ecouves_a5_height_growth_allocation_audit/ecouves_a5_height_growth_allocation_metadata.json | outputs/article_scenarios/ecouves_a5_height_growth_allocation_audit/ecouves_a5_height_growth_allocation_summary.csv`

## Editorial recommendation

Main text: retain the persistent joint-structure mismatch, the overestimated H0-Hm gap, the class-specific hierarchy mismatch, and the diagnosis of status-dependent vertical allocation.

Supplement: retain full distributional metrics, quantiles, the local OAT evidence matrix and detailed class-year diagnostics.

Do not make calibration or identifiability claims from Q-9F.4. Do not describe reconstructed individual heights as measurements. Keep GIS Coop aggregates and Francois Ningre inventories explicitly separated by source.

## Scientific review decisions

### Retained for the main text

- Q9F3-joint-correlation: weaker simulated height--diameter dependence than in reconstructed targets.
- Q9F3-height-gap: overestimated dominant-minus-mean height gap.
- Q9F5-overall: class-specific hierarchy mismatch rather than a uniform vertical offset.
- Q9F6-allocation-gradient: strong status-dependent allocation gradient in the baseline mechanism.

### Retained for the supplement

Full marginal and quantile diagnostics, the local OAT screening, year-specific hierarchy profiles and the descriptive covariance diagnostic.

### Interpretation constraints

- The 1992 hierarchy match is an initialization control, not predictive validation.
- Q-9F.4 is a local +/-20% OAT screening, not calibration, global sensitivity analysis or identifiability analysis.
- Height-based targets inherit the deterministic provisional height reconstruction.
- GIS Coop aggregates and Francois Ningre inventories remain distinct sources; small discrepancies are not silently reconciled.
- Q-9F.7 remains excluded from biological interpretation.
