import math,sys
from pathlib import Path
import numpy as np,pytest
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from simulations.article.ecouves_a5.height_types import *
from simulations.article.ecouves_a5.height_providers import ObservedHeightProvider
from simulations.article.ecouves_a5.grid_projection import *

def setup():
 c=StandContext('Ecouves','A5',1980,32,.1216,'reference','rest_chab');ts=(TreeRecord(1,1980,32,15,10),TreeRecord(2,1980,32,35,20));a=ObservedHeightProvider({(1,1980):12,(2,1980):28}).assign_heights(ts,c);return ts,a
def test_trapezoidal_weights():assert np.allclose(trapezoidal_weights([0,1,3]),[.5,1.5,1])
def test_projection_conserves_mass_and_first_moments():
 ts,a=setup();s=project_trees_to_grid(ts,a,ProjectionGrid(np.array([0,10,20,30,40]),np.array([0,10,20,30,40]))) ;d=projection_diagnostics(ts,a,s)
 assert d.mass_difference_ha==pytest.approx(0,abs=1e-12);assert d.mean_height_difference_m==pytest.approx(0,abs=1e-12);assert d.mean_diameter_difference_cm==pytest.approx(0,abs=1e-12)
def test_density_integrates_with_trapezoidal_quadrature():
 ts,a=setup();g=ProjectionGrid(np.arange(0,41,10),np.arange(0,41,10));s=project_trees_to_grid(ts,a,g);q=np.outer(trapezoidal_weights(g.height_m),trapezoidal_weights(g.diameter_cm));assert np.sum(s.density_ha_per_m_per_cm*q)==pytest.approx(30)
def test_strict_boundary_rejects_and_clip_reports():
 ts,a=setup();g=ProjectionGrid(np.array([15,20,25]),np.array([20,30,40]))
 with pytest.raises(ValueError):project_trees_to_grid(ts,a,g)
 s=project_trees_to_grid(ts,a,g,BoundaryPolicy.CLIP);assert s.clipped_tree_count==2
def test_missing_height_is_explicitly_omitted():
 ts,a=setup();h=list(a.heights);h[0]=AssignedHeight(1,1980,None,True,'missing',h[0].provider_id,h[0].provider_category);aa=HeightAssignment(a.context,a.provider,tuple(h));s=project_trees_to_grid(ts,aa,ProjectionGrid(np.arange(0,41,10),np.arange(0,41,10)));assert s.missing_height_count==1 and s.nodal_mass_ha.sum()==pytest.approx(20)
def test_dominant_height_fractional():
 c=StandContext('x','y',1,1,.1,'reference','x');ts=(TreeRecord(1,1,1,30,60),TreeRecord(2,1,1,20,60));a=ObservedHeightProvider({(1,1):30,(2,1):20}).assign_heights(ts,c);s=project_trees_to_grid(ts,a,ProjectionGrid(np.array([0,10,20,30,40]),np.array([0,10,20,30,40])));d=projection_diagnostics(ts,a,s);assert d.dominant_height_input_m==pytest.approx(26)

def _components_assignment(tree_heights):
 """Assignment with several height components per tree (residual completion)."""
 c=StandContext('Ecouves','A5',1980,32,.1216,'reference','rest_chab')
 ts=tuple(TreeRecord(i,1980,32,d,w) for i,(d,w,_) in enumerate(tree_heights,1))
 meta=HeightProviderMetadata('test-components','test','1',ProviderCategory.CALLABLE,True)
 hs=tuple(AssignedHeight(i,1980,float(h),False,None,meta.provider_id,meta.category,metadata=m)
          for i,(_,_,comps) in enumerate(tree_heights,1) for h,m in comps)
 return ts,HeightAssignment(c,meta,hs)
GRID=ProjectionGrid(np.arange(0.,41.,10.),np.arange(0.,41.,10.))
def test_all_height_components_are_projected():
 # one tree completed with three residual components, one measured tree
 ts,a=_components_assignment([(15,12,[(10,{}),(14,{}),(18,{})]),(35,20,[(28,{})])])
 s=project_trees_to_grid(ts,a,GRID);d=projection_diagnostics(ts,a,s)
 assert s.projected_tree_count==2 and s.missing_height_count==0
 assert s.nodal_mass_ha.sum()==pytest.approx(32)
 assert d.mass_input_ha==pytest.approx(32)
 assert d.mean_height_input_m==pytest.approx((12*14+20*28)/32)
 assert d.mean_height_difference_m==pytest.approx(0,abs=1e-12)
def test_components_are_not_collapsed_to_the_last_one():
 ts,a=_components_assignment([(15,12,[(10,{}),(30,{})])])
 s=project_trees_to_grid(ts,a,GRID)
 # half of the weight at height 10 and half at height 30, never all at 30
 assert s.nodal_mass_ha[1].sum()==pytest.approx(6) and s.nodal_mass_ha[3].sum()==pytest.approx(6)
def test_component_weight_fractions():
 ts,a=_components_assignment([(15,12,[(10,{'weight_fraction':3}),(30,{'weight_fraction':1})])])
 s=project_trees_to_grid(ts,a,GRID)
 assert s.nodal_mass_ha[1].sum()==pytest.approx(9) and s.nodal_mass_ha[3].sum()==pytest.approx(3)
def test_invalid_weight_fraction_is_rejected():
 ts,a=_components_assignment([(15,12,[(10,{'weight_fraction':0})])])
 with pytest.raises(ValueError):project_trees_to_grid(ts,a,GRID)
def test_clipping_counts_trees_not_components():
 ts,a=_components_assignment([(15,12,[(45,{}),(50,{})])])
 s=project_trees_to_grid(ts,a,GRID,BoundaryPolicy.CLIP);assert s.clipped_tree_count==1
def test_one_record_per_component_gives_the_same_state():
 # project_ecouves_a5_heights_to_grid.py builds one TreeRecord per CSV row, i.e. per component,
 # each with weight w/m and the same tree_id: the state must equal the one-record form.
 ts1,a1=_components_assignment([(15,12,[(10,{}),(14,{}),(18,{})])])
 c=a1.context;meta=a1.provider
 ts3=tuple(TreeRecord(1,1980,32,15,4) for _ in range(3))
 s1=project_trees_to_grid(ts1,a1,GRID);s3=project_trees_to_grid(ts3,HeightAssignment(c,meta,a1.heights),GRID)
 assert np.allclose(s1.nodal_mass_ha,s3.nodal_mass_ha)
