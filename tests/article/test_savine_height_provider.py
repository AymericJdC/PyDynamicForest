import math,sys
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from simulations.article.ecouves_a5.height_types import *
from simulations.article.ecouves_a5.savine_height_provider import *

def ctx():return StandContext("Ecouves","Ecouves A5",1980,32,0.1216,"reference","rest_chab")
def tr(i,d,w=10):return TreeRecord(i,1980,32,d,w,d*math.pi,"rest","reference","rest_chab","Ecouves","Ecouves A5")
def test_table_s5_coefficients_exact():
 p=SavineDouglasParameters(); assert (p.asymptote_intercept,p.asymptote_basal_area,p.asymptote_dg_rate,p.asymptote_dg_power)==(45.07,0.00160,0.00718,1.45561); assert (p.shape_intercept,p.shape_basal_area,p.relative_dbh_power,p.residual_sd_m)==(0.39143,0.00652,1.74230,1.85)
def test_manual_equation():
 p=SavineDouglasParameters(); d,dg,ba=30,25,40
 expected=1.3+45.07*(1+0.00160*ba)*(1-math.exp(-0.00718*dg**1.45561))/(1+0.39143*math.exp(-0.00652*ba)/(d/dg)**1.74230)
 assert predict_savine_douglas_height_m(d,dg,ba,p)==pytest.approx(expected)
def test_weighted_stand_metrics():
 m=compute_savine_stand_metrics((tr(1,10,1),tr(2,30,3))); assert m.quadratic_mean_diameter_cm==pytest.approx(math.sqrt(700)); assert m.density_ha==4
def test_provider_deterministic_and_uncertainty():
 ts=(tr(1,20),tr(2,30));p=SavineDouglasHeightProvider();a=p.assign_heights(ts,ctx());b=p.assign_heights(ts,ctx()); assert a.heights==b.heights and all(h.uncertainty.standard_deviation_m==1.85 for h in a.heights)
def test_permissive_and_strict_domains():
 ts=(tr(1,5),tr(2,20)); permissive=SavineDouglasHeightProvider().assign_heights(ts,ctx()); assert not permissive.heights[0].is_missing and permissive.heights[0].metadata["domain_status"]=="extrapolated"
 strict=SavineDouglasHeightProvider(domain_policy=DomainPolicy.STRICT).assign_heights(ts,ctx()); assert strict.heights[0].is_missing and not strict.heights[1].is_missing
def test_inputs_unchanged():
 ts=(tr(1,20),tr(2,30)); before=ts; SavineDouglasHeightProvider().assign_heights(ts,ctx()); assert ts==before
def test_lambda_must_remain_zero():
 with pytest.raises(ValueError): SavineDouglasParameters(local_effect_lambda=0.1)
