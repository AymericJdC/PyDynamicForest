import numpy as np,pytest
from pydynamicforest.types import State
from simulations.article.parameters import build_parameters
from simulations.article.ecouves_a5.height_growth_allocation_audit import audit_state

def synthetic_state():
 p=build_parameters();U=np.zeros((p.numerics.grid.nx,p.numerics.grid.ny));U[4:16,4:16]=100.0;return p,State(0.0,45.0,U,0)
def test_audit_partitions_density_and_bounds_status():
 p,state=synthetic_state();rows,summary=audit_state(state,p,1992)
 assert sum(r.density_share for r in rows)==pytest.approx(1.0)
 assert 0<=summary['status_min']<=summary['status_max']<=1+1e-12
def test_effective_velocity_decomposition_includes_covariance():
 p,state=synthetic_state();rows,summary=audit_state(state,p,1992)
 occupied=[r for r in rows if r.density_ha>0]
 assert occupied
 for r in occupied:
  reconstructed=(
   r.mean_height_growth_field*r.mean_status
   +r.growth_status_covariance
  )
  assert r.mean_effective_height_velocity==pytest.approx(reconstructed)

def test_baseline_height_growth_field_is_spatially_variable():
 p,state=synthetic_state();_,summary=audit_state(state,p,1992)
 assert summary['height_growth_field_is_constant'] is False
 assert summary['height_growth_field_max']>summary['height_growth_field_min']
def test_status_allocation_is_not_uniform_across_occupied_classes():
 p,state=synthetic_state();rows,_=audit_state(state,p,1992);values=[r.mean_status for r in rows if r.density_ha>0]
 assert max(values)>min(values)
