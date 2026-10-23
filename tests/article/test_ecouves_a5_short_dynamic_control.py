import numpy as np,pytest
from simulations.article.parameters import build_parameters
from simulations.article.ecouves_a5.short_dynamic_control import load_native_initial_condition,run_short_dynamic_control

def native_file(tmp_path):
 p=build_parameters();U=np.zeros((p.numerics.grid.nx,p.numerics.grid.ny));U[8:12,8:12]=1000
 path=tmp_path/'state.npz';np.savez_compressed(path,U0=U,year=1992,gis_age=45.0);return path,U

def test_loader_checks_provenance_and_copies(tmp_path):
 path,U=native_file(tmp_path);x=load_native_initial_condition(path);assert np.array_equal(x.U0,U) and x.U0 is not U
 with pytest.raises(ValueError):load_native_initial_condition(path,year=1985,age=38)
def test_short_control_advances_without_recalibration(tmp_path):
 path,_=native_file(tmp_path);x,p,c,state,rows=run_short_dynamic_control(path,n_steps=2)
 assert len(rows)==3 and state.step_index==2 and state.age==pytest.approx(45+2*p.numerics.time.dt)
 assert all(np.all(np.isfinite(list(r.record().values()))) for r in rows)
 assert min(r.minimum_density for r in rows)>=-p.numerics.positivity_tolerance
 assert all(r.status_minimum>=-1e-12 and r.status_maximum<=1+1e-12 for r in rows)
def test_initial_row_matches_loaded_density(tmp_path):
 path,_=native_file(tmp_path);_,p,_,_,rows=run_short_dynamic_control(path,n_steps=1)
 assert rows[0].step_index==0 and rows[0].age==45 and rows[0].stand_density>0
