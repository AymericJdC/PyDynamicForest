"""Fixed-effect Douglas height provider based on Savine et al., Table S5.

Inputs are individual DBH and quadratic mean diameter in centimetres, plus
stand basal area in square metres per hectare. Predicted total height is metres.
No local random effect is estimated: lambda is fixed to zero for Q-9E.3.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
import math
from collections.abc import Sequence
from .height_types import (
    AssignedHeight, HeightAssignment, HeightProviderMetadata, HeightUncertainty,
    ProviderCategory, StandContext, TreeRecord, UncertaintyKind,
)
from .height_providers import HeightProvider

DOUGLAS_DBH_MIN_CM = 7.51
DOUGLAS_DBH_MAX_CM = 140.69
DOUGLAS_RESIDUAL_SD_M = 1.85
REFERENCE = "Savine et al. (2025 preprint), supplementary material, Table S5"

class DomainPolicy(str, Enum):
    PERMISSIVE = "permissive"
    STRICT = "strict"

@dataclass(frozen=True)
class SavineDouglasParameters:
    """Published fixed-effect coefficients for Pseudotsuga menziesii."""
    asymptote_intercept: float = 45.07          # a_s1
    asymptote_basal_area: float = 0.00160       # a_s2
    asymptote_dg_rate: float = 0.00718          # a_s3
    asymptote_dg_power: float = 1.45561         # a_s4
    shape_intercept: float = 0.39143             # b_s1
    shape_basal_area: float = 0.00652            # b_s2
    relative_dbh_power: float = 1.74230          # c_s
    residual_sd_m: float = DOUGLAS_RESIDUAL_SD_M
    local_effect_lambda: float = 0.0
    variant: str = "Pseudotsuga menziesii; even-aged; fixed effects"
    source: str = REFERENCE
    def __post_init__(self):
        vals=(self.asymptote_intercept,self.asymptote_dg_rate,self.asymptote_dg_power,
              self.shape_intercept,self.relative_dbh_power,self.residual_sd_m)
        if any(not math.isfinite(v) or v<=0 for v in vals):
            raise ValueError("positive finite Savine parameters are required")
        if self.local_effect_lambda != 0.0:
            raise ValueError("Q-9E.3 requires local_effect_lambda = 0")

@dataclass(frozen=True)
class SavineStandMetrics:
    quadratic_mean_diameter_cm: float
    basal_area_m2_ha: float
    density_ha: float

def compute_savine_stand_metrics(trees: Sequence[TreeRecord]) -> SavineStandMetrics:
    if not trees: raise ValueError("at least one tree is required")
    density=sum(t.weight_ha for t in trees)
    if density<=0: raise ValueError("positive stand density is required")
    dg=math.sqrt(sum(t.weight_ha*t.diameter_cm**2 for t in trees)/density)
    ba=sum(t.weight_ha*math.pi*(t.diameter_cm/100.0)**2/4.0 for t in trees)
    return SavineStandMetrics(dg,ba,density)

def predict_savine_douglas_height_m(dbh_cm: float, dg_cm: float, basal_area_m2_ha: float,
                                     parameters: SavineDouglasParameters | None=None) -> float:
    """Predict total height from the published even-aged fixed-effect equation."""
    p=parameters or SavineDouglasParameters()
    for name,value in (("dbh_cm",dbh_cm),("dg_cm",dg_cm),("basal_area_m2_ha",basal_area_m2_ha)):
        if not math.isfinite(value) or value<=0: raise ValueError(f"{name} must be finite and positive")
    asymptote=(p.asymptote_intercept*(1.0+p.asymptote_basal_area*basal_area_m2_ha)
               *(1.0-math.exp(-p.asymptote_dg_rate*dg_cm**p.asymptote_dg_power)))
    shape=p.shape_intercept*math.exp(-p.shape_basal_area*basal_area_m2_ha)
    denominator=1.0+shape/(dbh_cm/dg_cm)**p.relative_dbh_power
    height=1.3+(1.0+p.local_effect_lambda)*asymptote/denominator
    if not math.isfinite(height) or height<=1.3: raise ValueError("Savine equation produced an invalid height")
    return height

class SavineDouglasHeightProvider(HeightProvider):
    """Deterministic even-aged Douglas provider with explicit domain signalling."""
    def __init__(self, parameters: SavineDouglasParameters|None=None,
                 domain_policy: DomainPolicy=DomainPolicy.PERMISSIVE):
        self.parameters=parameters or SavineDouglasParameters()
        self.domain_policy=DomainPolicy(domain_policy)
        metadata=HeightProviderMetadata(
            provider_id="savine-douglas-fixed-effects",
            name="Savine Douglas height provider",
            version="table-s5",
            category=ProviderCategory.CALLABLE,
            deterministic=True,
            description="National fixed-effect Hossfeld II relation; even-aged structure; lambda=0",
            source=self.parameters.source,
            metadata={"variant":self.parameters.variant,"dbh_domain_cm":[DOUGLAS_DBH_MIN_CM,DOUGLAS_DBH_MAX_CM],
                      "stand_covariate_domain":"unknown","residual_sd_m":self.parameters.residual_sd_m},
        )
        super().__init__(metadata)
    def assign_heights(self, trees: Sequence[TreeRecord], context: StandContext) -> HeightAssignment:
        metrics=compute_savine_stand_metrics(trees); out=[]; n_extra=0
        uncertainty=HeightUncertainty(UncertaintyKind.STANDARD_DEVIATION,
                                      standard_deviation_m=self.parameters.residual_sd_m,
                                      comment="Global calibration residual SD; not a tree-specific conditional uncertainty.")
        for tree in trees:
            extrapolated=not (DOUGLAS_DBH_MIN_CM<=tree.diameter_cm<=DOUGLAS_DBH_MAX_CM)
            if extrapolated: n_extra+=1
            reasons=[]
            if tree.diameter_cm<DOUGLAS_DBH_MIN_CM: reasons.append("dbh_below_published_domain")
            if tree.diameter_cm>DOUGLAS_DBH_MAX_CM: reasons.append("dbh_above_published_domain")
            if extrapolated and self.domain_policy is DomainPolicy.STRICT:
                out.append(AssignedHeight(tree.tree_id,tree.year,None,True,";".join(reasons),
                    self.metadata.provider_id,self.metadata.category,self.metadata.source,uncertainty,
                    {"domain_status":"out_of_domain","domain_reasons":reasons,
                     "quadratic_mean_diameter_cm":metrics.quadratic_mean_diameter_cm,
                     "basal_area_m2_ha":metrics.basal_area_m2_ha}))
                continue
            height=predict_savine_douglas_height_m(tree.diameter_cm,metrics.quadratic_mean_diameter_cm,
                                                   metrics.basal_area_m2_ha,self.parameters)
            out.append(AssignedHeight(tree.tree_id,tree.year,height,False,None,
                self.metadata.provider_id,self.metadata.category,self.metadata.source,uncertainty,
                {"domain_status":"extrapolated" if extrapolated else "within_published_dbh_domain",
                 "domain_reasons":reasons,"stand_covariate_domain":"unknown",
                 "quadratic_mean_diameter_cm":metrics.quadratic_mean_diameter_cm,
                 "basal_area_m2_ha":metrics.basal_area_m2_ha,"density_ha":metrics.density_ha,
                 "variant":self.parameters.variant,"local_effect_lambda":0.0}))
        warnings=("Published Douglas ranges for basal area and Dg are unavailable; only DBH domain is checked.",)
        if n_extra: warnings += (f"{n_extra} tree(s) fall outside the published DBH range.",)
        return self._finish(trees,context,out,warnings)
