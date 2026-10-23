import numpy as np,pytest
from simulations.article.parameters import build_parameters
from simulations.article.ecouves_a5.pydynamicforest_adapter import *
from simulations.article.ecouves_a5.state_compatibility import diagnose_native_compatibility
from pydynamicforest.observation_operators import stand_density,mean_height,mean_dbh

def source():
    h=np.array([0.,10.,20.,30.,40.,50.]);d=np.array([0.,20.,40.,60.,80.,100.]);m=np.zeros((6,6));m[1,1]=100;m[2,2]=200;m[3,3]=300
    return Q9E4GridState(h,d,m)

def test_native_axis_shape_units_and_conservation():
    p=build_parameters();c=convert_q9e4_to_native(source(),p)
    assert c.U0.shape==(p.numerics.grid.nx,p.numerics.grid.ny)
    assert stand_density(c.U0,p)==pytest.approx(600,abs=1e-10)
    assert mean_height(c.U0,p)==pytest.approx((1000+4000+9000)/600,abs=1e-12)
    assert mean_dbh(c.U0,p,unit='cm')==pytest.approx((2000+8000+18000)/600,abs=1e-12)

def test_density_is_per_normalized_area_not_physical_area():
    p=build_parameters();c=convert_q9e4_to_native(source(),p)
    assert np.sum(c.native_nodal_mass_ha)==pytest.approx(stand_density(c.U0,p))
    assert not np.allclose(c.U0,c.native_nodal_mass_ha)

def test_strict_domain_and_explicit_clip():
    p=build_parameters();s=Q9E4GridState(np.array([0.,50.]),np.array([0.,120.]),np.array([[0.,0.],[0.,1.]]))
    with pytest.raises(ValueError,match='outside native domain'):convert_q9e4_to_native(s,p)
    c=convert_q9e4_to_native(s,p,allow_clip=True);assert c.clipped_source_nodes==1

def test_native_diagnostics_are_compatible():
    p=build_parameters();s=source();c=convert_q9e4_to_native(s,p);d=diagnose_native_compatibility(s,c,p)
    assert d.status=='compatible' and d.axis_order=='height_dbh' and d.density_coordinates=='normalized'

def test_initial_condition_keeps_provider_provenance():
    c=convert_q9e4_to_native(source(),build_parameters());x=native_initial_condition(c,age=45,year=1992,provider_id='savine-douglas-fixed-effects')
    assert x.initial_age==45 and x.distribution_parameters['height_provider_id']=='savine-douglas-fixed-effects' and x.U0 is not None
