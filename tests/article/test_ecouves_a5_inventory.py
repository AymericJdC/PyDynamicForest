import math, sys
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from simulations.article.ecouves_a5.stand_metrics import *
from simulations.article.ecouves_a5.inventory import *

def row(t,y,c,s): return {"tree_id":t,"year":y,"circumference_cm":c,"diameter_cm":circumference_to_diameter_cm(c) if c is not None else None,"status":s,"has_measurement":c is not None,"_raw_c":c,"_plot":5}
def test_conversion(): assert circumference_to_diameter_cm(math.pi*10)==pytest.approx(10)
def test_quadratic_means_and_identity():
 c=[10,20]; d=[circumference_to_diameter_cm(x) for x in c]
 assert quadratic_circumference_cm(c)==pytest.approx(math.sqrt(250)); assert quadratic_diameter_cm(d)==pytest.approx(math.sqrt(250)/math.pi); assert quadratic_circumference_cm(c)==pytest.approx(math.pi*quadratic_diameter_cm(d))
def test_density(): assert density_ha(10,0.1)==100
def test_basal_area(): assert basal_area_m2_ha([100/math.sqrt(math.pi)],1)==pytest.approx(0.25)
def test_year_suffix(): assert [year_from_suffix(x) for x in ("98","00","01","20")]==[1998,2000,2001,2020]
def test_series(): assert series_status(1992)=="reference" and series_status(1990)=="audit"
def test_aa_excluded(tmp_path):
 from openpyxl import Workbook
 p=tmp_path/"x.xlsx"; w=Workbook(); s=w.active;s.title="Inventaires"; heads=["Plac","Arbre","AA"]
 for y in YEARS: q=str(y)[-2:]; heads += ["c"+q,"st"+q]
 s.append(heads); s.append([5,1,999]+sum(([10,"rest"] for _ in YEARS),[])); w.save(p)
 rows,meta=read_individual_inventory(p); assert all("AA" not in r for r in rows)
def test_rule_ranking_1980_general():
 rows=[]
 for t,c,s in [(1,10,"rest"),(2,20,"chab"),(3,30,"sec")]: rows.append(row(t,1980,c,s))
 for y in YEARS:
  if y!=1980:
   rows.append(row(1000+y,y,10,"rest"))
 ref={1980:{"age":32,"surface_reported_ha":1,"Cg_reference_cm":math.sqrt(250),"N_reference_ha":2}}
 c=candidate_rules(rows,ref,1); sel=[x for x in c if x["year"]==1980 and x["is_selected_rule"]][0]; assert sel["candidate_rule"]=="rest_chab"
def test_decrease_and_terminal_and_unknown():
 rows=[row(1,2010,50,"sec"),row(1,2013,49,"rest"),row(2,2010,10,"weird")]
 meta={"raw_records":[{"Arbre":1,"Plac":5},{"Arbre":2,"Plac":5}]}; a=detect_anomalies(rows,meta); kinds={x["anomaly_type"] for x in a}; assert {"circumference_decrease","measurement_after_terminal_status","unknown_status"}<=kinds
def test_missing_reference_year():
 rows=[]
 for y in YEARS: rows.append(row(y,y,10,"rest"))
 c=candidate_rules(rows,{},1); x=[z for z in c if z["year"]==1990 and z["is_selected_rule"]][0]; assert x["match_status"]=="audit_year_not_in_reference_series"
def test_real_files_when_present():
 i=ROOT/"data/article/ecouves_a5/raw/Ecouves-A5.xlsx"; r=ROOT/"data/article/ecouves_a5/reference/Douglas2021(116obs).xlsx"
 if not (i.exists() and r.exists()): pytest.skip("confidential workbooks not present")
 rows,_=read_individual_inventory(i); ref,_=read_reference(r); assert len({x["tree_id"] for x in rows})==234 and set(ref)==REFERENCE_YEARS
