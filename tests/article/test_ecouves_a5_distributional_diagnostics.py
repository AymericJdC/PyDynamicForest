import numpy as np,pytest
from simulations.article.parameters import build_parameters
from simulations.article.ecouves_a5.distributional_diagnostics import *

def masses():
 p=build_parameters();shape=(p.numerics.grid.nx,p.numerics.grid.ny);a=np.zeros(shape);b=np.zeros(shape);a[5,5]=10;a[10,10]=20;b[5,5]=10;b[10,10]=20;return p,a,b
def test_identical_distributions_have_zero_distances():
 p,a,b=masses();comps,joint,qs,sm,tm=diagnose_year(a,b,p,1998)
 assert all(c.wasserstein_1==pytest.approx(0) and c.cdf_max_distance==pytest.approx(0) for c in comps)
 assert joint.correlation_simulated==pytest.approx(joint.correlation_target)
def test_shift_is_detected_in_correct_dimension():
 p,a,b=masses();b=np.roll(b,1,axis=1);comps,_,_,_,_=diagnose_year(a,b,p,1998);by={c.dimension:c for c in comps}
 assert by['dbh_cm'].wasserstein_1>0 and by['height_m'].wasserstein_1==pytest.approx(0)
def test_quantiles_are_ordered_and_finite():
 p,a,b=masses();_,_,qs,_,_=diagnose_year(a,b,p,1998)
 for dim in ('dbh_cm','height_m'):
  vals=[q['simulated_value'] for q in qs if q['dimension']==dim];assert np.all(np.isfinite(vals)) and vals==sorted(vals)
def test_joint_mass_excess_balances_deficit_when_totals_match():
 p,a,b=masses();b=np.roll(b,1,axis=0);_,j,_,_,_=diagnose_year(a,b,p,1998)
 assert j.positive_mass_excess==pytest.approx(j.negative_mass_deficit)
