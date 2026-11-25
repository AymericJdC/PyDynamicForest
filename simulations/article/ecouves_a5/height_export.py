"""Stable CSV exports for Q-9E.2 height assignments and diagnostics."""
from __future__ import annotations
import csv
from pathlib import Path
from .height_types import *
from .height_diagnostics import HeightDiagnostics, TargetComparison

ASSIGNMENT_COLUMNS=("site","plot","year","age","tree_id","diameter_cm","circumference_cm","weight_ha","status","series_status","inclusion_rule","height_m","is_missing","missing_reason","provider_id","provider_category","source","uncertainty_kind","uncertainty_standard_deviation_m","uncertainty_lower_m","uncertainty_upper_m","uncertainty_confidence_level")
DIAGNOSTIC_COLUMNS=("site","plot","year","age","n_trees","n_with_valid_height","total_density_ha","valid_height_density_ha","weighted_coverage","mean_height_m","quadratic_mean_height_m","height_diameter_correlation","mean_slenderness","quadratic_mean_slenderness","minimum_slenderness","maximum_slenderness","dominant_height_m","dominant_height_status","dominant_selected_density_ha")

def assignment_rows(trees,assignment):
    by={(h.tree_id,h.year):h for h in assignment.heights}; out=[]
    for t in trees:
        h=by[(t.tree_id,t.year)]; u=h.uncertainty
        out.append({"site":t.site,"plot":t.plot,"year":t.year,"age":t.age,"tree_id":t.tree_id,"diameter_cm":t.diameter_cm,"circumference_cm":t.circumference_cm,"weight_ha":t.weight_ha,"status":t.status,"series_status":t.series_status,"inclusion_rule":t.inclusion_rule,"height_m":h.height_m,"is_missing":h.is_missing,"missing_reason":h.missing_reason,"provider_id":h.provider_id,"provider_category":h.provider_category.value,"source":h.source,"uncertainty_kind":u.kind.value,"uncertainty_standard_deviation_m":u.standard_deviation_m,"uncertainty_lower_m":u.lower_m,"uncertainty_upper_m":u.upper_m,"uncertainty_confidence_level":u.confidence_level})
    return out

def diagnostic_row(context,diag): return {"site":context.site,"plot":context.plot,"year":context.year,"age":context.age,**diag.__dict__}
def write_rows(path,rows,columns):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=columns,extrasaction="ignore"); w.writeheader(); w.writerows(rows)
