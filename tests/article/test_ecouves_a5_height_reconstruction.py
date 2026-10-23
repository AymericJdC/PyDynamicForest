import sys
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from simulations.article.ecouves_a5.height_types import AdapterMode
from simulations.article.ecouves_a5.savine_height_provider import SavineDouglasHeightProvider
from simulations.article.ecouves_a5.height_reconstruction import reconstruct_year

def rows():
 out=[]
 for year,status,rule in ((1980,"reference","rest_chab"),(2013,"audit","all_measured")):
  for i,d in enumerate((10,20,30),1):out.append({"site":"Ecouves","plot":"Ecouves A5","tree_id":i,"year":year,"age":year-1948,"series_status":status,"circumference_cm":d*3.14159,"diameter_cm":d,"status":"rest","has_measurement":True,"included_in_reference_state":status=="reference","inclusion_rule":rule,"plot_area_ha":0.1216,"expansion_factor_ha":1/0.1216})
 return out
def test_reference_reconstruction_preserves_rule():
 r=reconstruct_year(rows(),1980,SavineDouglasHeightProvider()); assert r.context.selected_inclusion_rule=="rest_chab" and r.validation.is_valid and r.diagnostics.weighted_coverage==1
def test_2013_requires_explicit_audit_mode():
 with pytest.raises(ValueError):reconstruct_year(rows(),2013,SavineDouglasHeightProvider())
 r=reconstruct_year(rows(),2013,SavineDouglasHeightProvider(),AdapterMode.MEASURED_INVENTORY); assert r.context.series_status=="audit"
def test_no_target_recalibration():
 r=reconstruct_year(rows(),1980,SavineDouglasHeightProvider()); assert all(c.status=="target_not_available" for c in r.target_comparisons)
