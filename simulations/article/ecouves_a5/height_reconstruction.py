"""Orchestration of deterministic height reconstruction for Q-9E.3."""
from __future__ import annotations
from dataclasses import dataclass
from collections.abc import Mapping, Sequence
from .height_types import AdapterMode, HeightTargets
from .height_adapter import build_height_provider_inputs
from .height_validation import HeightValidationPolicy
from .height_diagnostics import compute_height_diagnostics, compare_height_targets
from .height_export import assignment_rows, diagnostic_row
from .savine_height_provider import SavineDouglasHeightProvider

@dataclass(frozen=True)
class AnnualHeightReconstruction:
    year:int; context:object; trees:tuple; assignment:object; validation:object
    diagnostics:object; target_comparisons:tuple; assignment_rows:tuple; n_extrapolated:int

def reconstruct_year(rows:Sequence[Mapping],year:int,provider:SavineDouglasHeightProvider,
                     adapter_mode:AdapterMode=AdapterMode.REFERENCE_STATE,
                     targets:HeightTargets|None=None)->AnnualHeightReconstruction:
    trees,context=build_height_provider_inputs(rows,year,adapter_mode)
    before=tuple((t.tree_id,t.diameter_cm,t.weight_ha,t.inclusion_rule) for t in trees)
    assignment=provider.assign_heights(trees,context)
    validation=HeightValidationPolicy(minimum_height_m=1.3,allow_missing=True,require_uncertainty=True).validate(trees,assignment)
    after=tuple((t.tree_id,t.diameter_cm,t.weight_ha,t.inclusion_rule) for t in trees)
    if before!=after: raise RuntimeError("height reconstruction modified Q-9E.1 tree inputs")
    diagnostics=compute_height_diagnostics(trees,assignment)
    comparisons=compare_height_targets(diagnostics,targets or HeightTargets())
    rows_out=assignment_rows(trees,assignment)
    by={(h.tree_id,h.year):h for h in assignment.heights}
    for row in rows_out:
        meta=by[(row["tree_id"],row["year"])].metadata
        row.update({"provider_version":assignment.provider.version,"variant":meta.get("variant"),
                    "domain_status":meta.get("domain_status"),"domain_reasons":";".join(meta.get("domain_reasons",[])),
                    "quadratic_mean_diameter_cm":meta.get("quadratic_mean_diameter_cm"),
                    "basal_area_m2_ha":meta.get("basal_area_m2_ha"),"local_effect_lambda":meta.get("local_effect_lambda")})
    n_extra=sum(r.get("domain_status") in {"extrapolated","out_of_domain"} for r in rows_out)
    return AnnualHeightReconstruction(year,context,trees,assignment,validation,diagnostics,comparisons,tuple(rows_out),n_extra)
