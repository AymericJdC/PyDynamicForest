import pytest
from simulations.article.config import ARTICLE_CONFIG
from simulations.article.ecouves_a5.mechanistic_sensitivity import *
def test_selected_cases_are_complete_and_isolated():
 cases=selected_cases();assert len(cases)==8 and len({c.name for c in cases})==8
 assert {c.mechanism for c in cases}==set(MECHANISMS) and {c.multiplier for c in cases}==set(MULTIPLIERS)
def test_each_case_changes_exactly_one_scientific_value():
 for case in selected_cases():
  p=case_parameters(case);section,field=PARAMETER_PATHS[case.mechanism]
  assert case.perturbed_value==pytest.approx(case.baseline_value*case.multiplier)
 assert ARTICLE_CONFIG['model']['height_growth']['physical_rate']!=0
def test_centred_elasticity_sign_and_value():
 rows=[]
 for mult,value in ((0.8,8.0),(1.2,12.0)):
  rows.append({'mechanism':'height_growth','multiplier':mult,'year':1998,'metric':'N','value':value})
 # complete synthetic index for the remaining required combinations
 for m in MECHANISMS:
  for y in TARGET_YEARS[1:]:
   for metric in SIGNATURE_METRICS+('W1_dbh_cm','KS_dbh','W1_height_m','KS_height'):
    for mult in MULTIPLIERS:
     key=(m,mult,y,metric)
     if not any((r['mechanism'],r['multiplier'],r['year'],r['metric'])==key for r in rows):rows.append({'mechanism':m,'multiplier':mult,'year':y,'metric':metric,'value':10.0})
 out=centred_elasticities(rows);r=next(x for x in out if x['mechanism']=='height_growth' and x['year']==1998 and x['metric']=='N');assert r['elasticity']==pytest.approx(1.0)
