import numpy as np,pytest
from pydynamicforest.types import State
from simulations.article.parameters import build_parameters
from simulations.article.ecouves_a5.status_shape_mass_balance import diagnostic_terms

def state():
 p=build_parameters();U=np.zeros((p.numerics.grid.nx,p.numerics.grid.ny));U[6:14,6:14]=100.0;return p,State(0.0,45.0,U,0)
def test_gamma_one_has_identical_height_transport_integrals():
 p,s=state();t=diagnostic_terms(s,p,1.0);assert t['height_transport_integral_transformed']==pytest.approx(t['height_transport_integral_baseline'])
def test_lower_gamma_raises_transformed_status_and_changes_height_transport():
 p,s=state();low=diagnostic_terms(s,p,0.75);high=diagnostic_terms(s,p,1.25);assert low['transformed_status_max']>=high['transformed_status_max'];assert low['height_transport_integral_transformed']!=pytest.approx(high['height_transport_integral_transformed'])
def test_diagnostic_terms_are_finite_and_status_bounded():
 p,s=state();t=diagnostic_terms(s,p,0.75);assert all(np.isfinite(v) for v in t.values());assert 0<=t['status_min']<=t['status_max']<=1+1e-12
