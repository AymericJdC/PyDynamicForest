import numpy as np,pytest
from simulations.article.parameters import build_parameters
from simulations.article.ecouves_a5.main_dynamic_trajectory import *

def make_states(tmp_path):
 p=build_parameters();paths={}
 for year,age in YEAR_TO_AGE.items():
  U=np.zeros((p.numerics.grid.nx,p.numerics.grid.ny));U[8:12,8:12]=1000-(year-1992)
  path=tmp_path/f'ecouves_a5_native_initial_state_{year}.npz';np.savez_compressed(path,U0=U,year=year,gis_age=age);paths[year]=path
 return paths

def test_target_mapping_and_steps():
 p=build_parameters();s=nearest_target_steps(p.numerics.time.dt);assert s[1992]==0 and s[2020]>s[2016]>s[1998]
def test_empirical_targets_require_provenance(tmp_path):
 paths=make_states(tmp_path);p=build_parameters();targets=load_empirical_targets(tmp_path,p);assert set(targets)==set(TARGET_YEARS) and all(x.N>0 for x in targets.values())
 with np.load(paths[1998]) as z:U=z['U0']
 np.savez_compressed(paths[1998],U0=U,year=1998,gis_age=52)
 with pytest.raises(ValueError):load_empirical_targets(tmp_path,p)
def test_summary_is_finite(tmp_path):
 make_states(tmp_path);p=build_parameters();targets=load_empirical_targets(tmp_path,p)
 assert all(np.isfinite(list(v.record().values())).all() for v in targets.values())
