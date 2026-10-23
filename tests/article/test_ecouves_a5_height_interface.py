import csv, math, sys
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT))
from simulations.article.ecouves_a5.height_types import *
from simulations.article.ecouves_a5.height_providers import *
from simulations.article.ecouves_a5.height_validation import *
from simulations.article.ecouves_a5.height_diagnostics import *
from simulations.article.ecouves_a5.height_adapter import *
from simulations.article.ecouves_a5.height_export import *

def trees(weights=(50,50,50),diameters=(10,20,30)):
 return tuple(TreeRecord(i+1,2013,65,d,w,d*math.pi,"rest","audit","all_measured","Ecouves","Ecouves A5") for i,(w,d) in enumerate(zip(weights,diameters)))
def context(mode=AdapterMode.MEASURED_INVENTORY): return StandContext("Ecouves","Ecouves A5",2013,65,0.1216,"audit","all_measured",mode)

def test_types_are_immutable_and_validate_units():
 t=trees()[0]
 with pytest.raises(Exception): t.diameter_cm=12
 with pytest.raises(ValueError): TreeRecord(1,2013,65,-1,1)
 assert HeightUncertainty(UncertaintyKind.UNKNOWN)!=HeightUncertainty(UncertaintyKind.STANDARD_DEVIATION,0.0)

def test_observed_missing_and_duplicate():
 p=ObservedHeightProvider({(1,2013):12}); a=p.assign_heights(trees()[:2],context())
 assert a.heights[0].height_m==12 and a.heights[1].is_missing
 with pytest.raises(ValueError): ObservedHeightProvider([(1,2013,12),(1,2013,13)])

def test_fixed_callable_missing_and_composite_priority():
 ts=trees()[:2]; fixed=FixedHeightProvider(20); assert all(h.height_m==20 for h in fixed.assign_heights(ts,context()).heights)
 called=CallableHeightProvider(lambda t,c:t.diameter_cm/2); assert called.assign_heights(ts,context()).heights[1].height_m==10
 assert all(h.is_missing for h in MissingHeightProvider().assign_heights(ts,context()).heights)
 comp=CompositeHeightProvider([ObservedHeightProvider({(1,2013):12}),fixed]); hs=comp.assign_heights(ts,context()).heights
 assert [h.height_m for h in hs]==[12,20] and hs[0].provider_category is ProviderCategory.OBSERVED

def test_validation_does_not_modify():
 ts=trees()[:1]; a=FixedHeightProvider(20).assign_heights(ts,context()); before=a.heights[0]
 r=HeightValidationPolicy(maximum_height_m=15).validate(ts,a)
 assert not r.is_valid and r.n_invalid==1 and a.heights[0]==before

def test_weighted_diagnostics_and_slenderness():
 ts=trees((1,3),(10,30)); a=CallableHeightProvider(lambda t,c:t.diameter_cm).assign_heights(ts,context())
 d=compute_height_diagnostics(ts,a,target_density_ha=3)
 assert d.mean_height_m==pytest.approx(25); assert d.quadratic_mean_height_m==pytest.approx(math.sqrt(700)); assert d.height_diameter_correlation==pytest.approx(1); assert d.mean_slenderness==pytest.approx(100)

def test_dominant_fractional_last_tree():
 ts=trees((60,60,60),(30,20,10)); a=CallableHeightProvider(lambda t,c:{30:30,20:20,10:10}[t.diameter_cm]).assign_heights(ts,context())
 d=dominant_height(ts,a,100); assert d.status=="ok" and d.selected_density_ha==pytest.approx(100) and d.height_m==pytest.approx(26)

def test_dominant_ties_are_order_invariant():
 ts=(TreeRecord(1,2013,65,30,60),TreeRecord(2,2013,65,20,60),TreeRecord(3,2013,65,20,60))
 obs={(1,2013):30,(2,2013):20,(3,2013):10}; p=ObservedHeightProvider(obs)
 values=[]
 for order in (ts,(ts[0],ts[2],ts[1])): values.append(dominant_height(order,p.assign_heights(order,context()),100).height_m)
 assert values[0]==pytest.approx(values[1])==pytest.approx(24)

def test_dominant_insufficient_density():
 ts=trees((20,20,20)); a=FixedHeightProvider(10).assign_heights(ts,context()); d=dominant_height(ts,a)
 assert d.height_m is None and d.status=="insufficient_density"

def test_target_comparison_is_diagnostic_only():
 ts=trees(); a=FixedHeightProvider(15).assign_heights(ts,context()); d=compute_height_diagnostics(ts,a); h0=a.heights
 c=compare_height_targets(d,HeightTargets(mean_height_m=16)); assert c[0].difference==-1 and a.heights==h0

def synthetic_rows():
 rows=[]
 for y,status in ((1992,"reference"),(2013,"audit")):
  for i in (1,2): rows.append({"site":"Ecouves","plot":"Ecouves A5","tree_id":i,"year":y,"age":y-1948,"series_status":status,"circumference_cm":31.4*i,"diameter_cm":10*i,"status":"rest","has_measurement":True,"included_in_reference_state":status=="reference","inclusion_rule":"rest_only" if status=="reference" else "all_measured","plot_area_ha":0.1216,"expansion_factor_ha":1/0.1216})
 return rows

def test_adapter_respects_reference_and_2013_audit():
 rows=synthetic_rows(); ts,c=build_height_provider_inputs(rows,1992); assert len(ts)==2 and c.adapter_mode is AdapterMode.REFERENCE_STATE
 with pytest.raises(ValueError): build_height_provider_inputs(rows,2013)
 ts,c=build_height_provider_inputs(rows,2013,AdapterMode.MEASURED_INVENTORY); assert c.series_status=="audit" and len(ts)==2

def test_export_roundtrip(tmp_path):
 ts=trees()[:2]; a=CompositeHeightProvider([ObservedHeightProvider({(1,2013):12}),MissingHeightProvider()]).assign_heights(ts,context())
 p=tmp_path/"heights.csv"; write_rows(p,assignment_rows(ts,a),ASSIGNMENT_COLUMNS); rows=list(csv.DictReader(p.open(encoding="utf-8")))
 assert list(rows[0])==list(ASSIGNMENT_COLUMNS); assert rows[1]["height_m"]=="" and rows[1]["is_missing"]=="True"
