import numpy as np,pytest
from pydynamicforest.solver import advance_one_step_sparse_legacy
from pydynamicforest.types import State
from simulations.article.parameters import build_parameters
from simulations.article.ecouves_a5.status_shape_sensitivity import *

def state():
 p=build_parameters();U=np.zeros((p.numerics.grid.nx,p.numerics.grid.ny));U[6:14,6:14]=100.0;return p,State(0.0,45.0,U,0)
def test_status_transform_identity_and_order():
 s=np.array([0.0,0.1,0.5,1.0]);assert np.allclose(transformed_status(s,1.0),s);assert np.all(transformed_status(s,0.75)>=s);assert np.all(transformed_status(s,1.25)<=s)
def test_gamma_one_exactly_uses_reference_step():
 p,s=state();expected=advance_one_step_sparse_legacy(s,p);actual=advance_one_step_height_status_shape(s,p,1.0);assert np.array_equal(actual.U,expected.U) and actual.age==expected.age
def test_nonunit_gamma_changes_height_only_pathway_result():
 p,s=state();low=advance_one_step_height_status_shape(s,p,0.75);high=advance_one_step_height_status_shape(s,p,1.25);assert not np.allclose(low.U,high.U)
def test_cases_are_small_fixed_design():
 assert [c.gamma for c in selected_cases()]==[0.75,1.0,1.25]
