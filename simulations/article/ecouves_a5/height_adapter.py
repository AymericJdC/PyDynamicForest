"""Adapt Q-9E.1 long-table rows to typed height-provider inputs."""
from __future__ import annotations
from collections.abc import Iterable, Mapping
from .height_types import *

def _bool(value):
    if isinstance(value,bool): return value
    return str(value).strip().lower() in {"1","true","yes"}

def build_height_provider_inputs(rows:Iterable[Mapping],year:int,mode:AdapterMode=AdapterMode.REFERENCE_STATE):
    selected=[r for r in rows if int(r["year"])==year]
    if not selected: raise ValueError(f"year {year} is absent")
    series={str(r["series_status"]) for r in selected};
    if len(series)!=1: raise ValueError("mixed series_status values")
    if mode is AdapterMode.REFERENCE_STATE:
        selected=[r for r in selected if _bool(r["included_in_reference_state"])]
        if not selected: raise ValueError("no trees are included in the requested reference state")
    else:
        selected=[r for r in selected if _bool(r["has_measurement"])]
    for field in ("site","plot","age","plot_area_ha","inclusion_rule"):
        vals={str(r[field]) for r in selected}
        if len(vals)!=1: raise ValueError(f"inconsistent {field}")
    rules={str(r["inclusion_rule"]) for r in selected}
    trees=[]
    for r in selected:
        d=float(r["diameter_cm"]); c=float(r["circumference_cm"]) if r.get("circumference_cm") not in (None,"") else None
        trees.append(TreeRecord(r["tree_id"],year,int(r["age"]) if r.get("age") not in (None,"") else None,d,float(r["expansion_factor_ha"]),c,r.get("status"),r.get("series_status"),r.get("inclusion_rule"),r.get("site"),r.get("plot")))
    first=selected[0]
    context=StandContext(str(first["site"]),str(first["plot"]),year,int(first["age"]) if first.get("age") not in (None,"") else None,float(first["plot_area_ha"]),str(first["series_status"]),next(iter(rules)),mode)
    return tuple(trees),context
