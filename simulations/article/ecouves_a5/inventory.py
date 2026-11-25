"""Read, normalize, reconcile and audit Ecouves A5 inventories."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any
import csv, math
from openpyxl import load_workbook
from .stand_metrics import circumference_to_diameter_cm, quadratic_circumference_cm, quadratic_diameter_cm, density_ha, basal_area_m2_ha

YEARS=(1965,1969,1975,1980,1985,1990,1992,1998,2000,2001,2004,2007,2010,2013,2016,2020)
REFERENCE_YEARS={1965,1969,1975,1980,1985,1992,1998,2016,2020}
AUDIT_YEARS=set(YEARS)-REFERENCE_YEARS
KNOWN_STATUSES={"rest","sec","chab"}
RULES={"all_measured":None,"rest_only":{"rest"},"rest_chab":{"rest","chab"},"rest_sec":{"rest","sec"},"all_statuses":KNOWN_STATUSES}
PARSIMONY={"all_measured":0,"rest_only":1,"rest_chab":2,"rest_sec":3,"all_statuses":4}
TERMINAL_STATUSES={"sec","chab"}

def year_from_suffix(suffix: str) -> int:
    x=int(suffix)
    return 1900+x if x>=50 else 2000+x

def series_status(year:int)->str: return "reference" if year in REFERENCE_YEARS else "audit"

def _norm_status(value:Any)->str|None:
    if value is None or str(value).strip()=="": return None
    return str(value).strip().lower()

def read_individual_inventory(path:Path, plot_area_ha:float=0.1216)->tuple[list[dict],dict]:
    wb=load_workbook(path,read_only=True,data_only=True)
    if "Inventaires" not in wb.sheetnames: raise ValueError("missing sheet: Inventaires")
    ws=wb["Inventaires"]; rows=ws.iter_rows(values_only=True); headers=[str(x) if x is not None else "" for x in next(rows)]
    for col in ("Plac","Arbre"):
        if col not in headers: raise ValueError(f"missing column: {col}")
    pairs={}
    for h in headers:
        if h.startswith("c") and len(h)==3:
            y=year_from_suffix(h[1:]); sh="st"+h[1:]
            if sh not in headers: raise ValueError(f"missing status column: {sh}")
            pairs[y]=(headers.index(h),headers.index(sh))
    if set(pairs)!=set(YEARS): raise ValueError(f"unexpected inventory years: {sorted(pairs)}")
    out=[]; raw=[]
    for rno,row in enumerate(rows,start=2):
        record={headers[i]:row[i] for i in range(len(headers))}; raw.append(record)
        for year,(ci,si) in sorted(pairs.items()):
            c0=row[ci]; st=_norm_status(row[si]); numeric=None
            if c0 is not None and str(c0).strip()!="":
                try: numeric=float(c0)
                except (TypeError,ValueError): numeric=None
            out.append({"site":"Ecouves","plot":"Ecouves A5","tree_id":record["Arbre"],"year":year,"age":year-1948,
                "series_status":series_status(year),"circumference_cm":numeric,"diameter_cm":circumference_to_diameter_cm(numeric) if numeric is not None else None,
                "status":st,"has_measurement":numeric is not None,"included_in_reference_state":False,"inclusion_rule":"",
                "plot_area_ha":plot_area_ha,"expansion_factor_ha":1.0/plot_area_ha,"_raw_c":c0,"_plot":record["Plac"],"_row":rno})
    return out,{"sheet":"Inventaires","headers":headers,"raw_records":raw,"workbook_sheets":wb.sheetnames}

def read_reference(path:Path)->tuple[dict[int,dict],dict]:
    wb=load_workbook(path,read_only=True,data_only=True); sheet="Douglas2021 (116 obs)"
    if sheet not in wb.sheetnames: raise ValueError(f"missing sheet: {sheet}")
    ws=wb[sheet]; rows=ws.iter_rows(values_only=True); headers=[str(x) for x in next(rows)]
    required={"site","pla","surface","annee","age","Cg","N"}
    if not required.issubset(headers): raise ValueError(f"missing reference columns: {sorted(required-set(headers))}")
    selected={}
    for row in rows:
        d=dict(zip(headers,row))
        if str(d["site"]).strip().lower()=="ecouves" and str(d["pla"]).strip().lower()=="ecouves a5":
            y=int(d["annee"]); selected[y]={"age":int(d["age"]),"surface_reported_ha":float(d["surface"]),"Cg_reference_cm":float(d["Cg"]),"N_reference_ha":float(d["N"])}
    if not selected: raise ValueError("no Ecouves A5 rows found in reference workbook")
    return selected,{"sheet":sheet,"headers":headers,"workbook_sheets":wb.sheetnames}

def _included(row:dict,rule:str)->bool:
    if not row["has_measurement"]: return False
    statuses=RULES[rule]
    return True if statuses is None else row["status"] in statuses

def candidate_rules(long_rows:list[dict], reference:dict[int,dict], area:float)->list[dict]:
    out=[]
    for year in YEARS:
        yr=[r for r in long_rows if r["year"]==year]; ref=reference.get(year)
        counts={s:sum(r["status"]==s for r in yr) for s in KNOWN_STATUSES}
        for rule in RULES:
            inc=[r for r in yr if _included(r,rule)]; cs=[r["circumference_cm"] for r in inc]; ds=[r["diameter_cm"] for r in inc]
            n=len(inc); N=density_ha(n,area); cg=quadratic_circumference_cm(cs) if cs else None; dg=quadratic_diameter_cm(ds) if ds else None; G=basal_area_m2_ha(ds,area) if ds else 0.0
            nr=ref["N_reference_ha"] if ref else None; cr=ref["Cg_reference_cm"] if ref else None
            nd=N-nr if ref else None; cd=cg-cr if ref and cg is not None else None
            score=(abs(nd)/max(abs(nr),1e-12)+abs(cd)/max(abs(cr),1e-12)) if ref and cg is not None else None
            if not ref: match="reference_not_available" if year in REFERENCE_YEARS else "audit_year_not_in_reference_series"
            elif abs(nd)<=0.02 and abs(cd)<=0.005: match="exact"
            elif abs(nd)<=0.5 and abs(cd)<=0.05: match="rounding_match"
            elif abs(nd)<=0.5 or abs(cd)<=0.05: match="partial_match"
            else: match="mismatch"
            out.append({"year":year,"age":ref["age"] if ref else year-1948,"series_status":series_status(year),"candidate_rule":rule,"n_included":n,
                "N_computed_ha":N,"N_reference_ha":nr,"N_difference_ha":nd,"N_absolute_difference_ha":abs(nd) if nd is not None else None,
                "Cg_computed_cm":cg,"Cg_reference_cm":cr,"Cg_difference_cm":cd,"Cg_absolute_difference_cm":abs(cd) if cd is not None else None,
                "Dg_computed_cm":dg,"G_computed_m2_ha":G,"n_rest":counts["rest"],"n_sec":counts["sec"],"n_chab":counts["chab"],
                "match_status":match,"selection_score":score,"is_selected_rule":False})
    for year in YEARS:
        group=[x for x in out if x["year"]==year]
        if year in reference: best=min(group,key=lambda x:(round(x["selection_score"],12),PARSIMONY[x["candidate_rule"]]))
        else: best=next(x for x in group if x["candidate_rule"]=="all_measured")
        best["is_selected_rule"]=True
    return out

def reconcile(long_rows:list[dict], candidates:list[dict], reference:dict[int,dict])->list[dict]:
    selected={x["year"]:x for x in candidates if x["is_selected_rule"]}
    for r in long_rows:
        rule=selected[r["year"]]["candidate_rule"]; r["inclusion_rule"]=rule
        r["included_in_reference_state"]=bool(r["year"] in reference and _included(r,rule))
    out=[]
    for y in YEARS:
        x=selected[y]; ref=reference.get(y)
        if ref: comment=f"Selected by minimum combined relative error on N and Cg; reference surface reported as {ref['surface_reported_ha']:.4f} ha."
        elif y in REFERENCE_YEARS: comment="Reference year expected scientifically, but no aggregate row was available."
        else: comment="Audit inventory absent from the selected aggregate reference series; all_measured retained descriptively, not as a reconciled reference state."
        out.append({k:x[k] for k in ("year","age","series_status")}|{"selected_rule":x["candidate_rule"],"n_included":x["n_included"],"N_computed_ha":x["N_computed_ha"],"N_reference_ha":x["N_reference_ha"],"N_difference_ha":x["N_difference_ha"],"Cg_computed_cm":x["Cg_computed_cm"],"Cg_reference_cm":x["Cg_reference_cm"],"Cg_difference_cm":x["Cg_difference_cm"],"Dg_computed_cm":x["Dg_computed_cm"],"G_computed_m2_ha":x["G_computed_m2_ha"],"match_status":x["match_status"],"reconciliation_comment":comment})
    return out

def detect_anomalies(rows:list[dict], meta:dict)->list[dict]:
    a=[]
    def add(tree,year,typ,prevy=None,prev=None,cur=None,status=None,severity="warning",comment=""):
        a.append({"tree_id":tree,"year":year,"anomaly_type":typ,"previous_year":prevy,"previous_value":prev,"current_value":cur,"status":status,"severity":severity,"comment":comment})
    raw=meta["raw_records"]; ids=[x.get("Arbre") for x in raw]
    for d in raw:
        if d.get("Arbre") is None: add(None,None,"missing_tree_id",severity="error",comment="Tree identifier is missing.")
        if d.get("Plac")!=5: add(d.get("Arbre"),None,"unexpected_plot_id",cur=d.get("Plac"),severity="error",comment="Expected plot identifier 5.")
    for t in set(ids):
        if t is not None and ids.count(t)>1: add(t,None,"duplicate_tree_id",severity="error",comment="Tree identifier occurs more than once.")
    by={}
    for r in rows:
        t=r["tree_id"]
        if r["_raw_c"] is not None and str(r["_raw_c"]).strip()!="" and r["circumference_cm"] is None: add(t,r["year"],"non_numeric_circumference",cur=r["_raw_c"],status=r["status"],severity="error")
        if r["circumference_cm"]==0: add(t,r["year"],"zero_circumference",cur=0,status=r["status"],severity="error")
        if r["circumference_cm"] is not None and r["circumference_cm"]<0: add(t,r["year"],"negative_circumference",cur=r["circumference_cm"],status=r["status"],severity="error")
        if r["status"] is not None and r["status"] not in KNOWN_STATUSES: add(t,r["year"],"unknown_status",cur=r["status"],status=r["status"],severity="error")
        if r["has_measurement"] and r["status"] is None: add(t,r["year"],"measurement_without_status",cur=r["circumference_cm"],severity="warning")
        if not r["has_measurement"] and r["status"] is not None: add(t,r["year"],"status_without_measurement",status=r["status"],severity="warning")
        by.setdefault(t,[]).append(r)
    for t,seq in by.items():
        seq=sorted(seq,key=lambda x:x["year"]); terminal=None; prev_meas=None; absent=False
        for r in seq:
            if r["has_measurement"]:
                if terminal and r["year"]>terminal[0]: add(t,r["year"],"measurement_after_terminal_status",terminal[0],terminal[1],r["circumference_cm"],r["status"],"error","Measurement follows an earlier sec/chab status.")
                if absent: add(t,r["year"],"reappearance_after_absence",prev_meas[0] if prev_meas else None,prev_meas[1] if prev_meas else None,r["circumference_cm"],r["status"],"warning")
                if prev_meas and r["circumference_cm"]<prev_meas[1]: add(t,r["year"],"circumference_decrease",prev_meas[0],prev_meas[1],r["circumference_cm"],r["status"],"warning","Observed value retained unchanged.")
                prev_meas=(r["year"],r["circumference_cm"]); absent=False
                if r["status"] in TERMINAL_STATUSES: terminal=(r["year"],r["status"])
            elif prev_meas:
                if not terminal and not absent: add(t,r["year"],"disappearance_without_explicit_status",prev_meas[0],prev_meas[1],None,r["status"],"warning")
                absent=True
    return a

def write_csv(path:Path,rows:list[dict],fields:list[str]|None=None)->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    if fields is None: fields=list(rows[0]) if rows else []
    with path.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore",delimiter=","); w.writeheader(); w.writerows(rows)
