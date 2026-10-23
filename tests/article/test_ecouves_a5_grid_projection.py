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
