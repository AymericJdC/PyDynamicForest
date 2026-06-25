import numpy as np

from simulations.baseline.parameters import build_parameters
from pydynamicforest.model import (
    evaluate_model_fields,
    check_model_fields_are_finite,
    check_model_fields_shapes,
)


def test_model_fields_are_valid_on_baseline_grid():
    p = build_parameters()

    fields = evaluate_model_fields(p, time=0.0)

    expected_shape = (p.numerics.grid.nx, p.numerics.grid.ny)

    assert set(fields.keys()) == {
        "diffusion",
        "mortality",
        "height_growth",
        "dbh_growth",
    }

    assert check_model_fields_shapes(fields, expected_shape)
    assert check_model_fields_are_finite(fields)

    for values in fields.values():
        assert isinstance(values, np.ndarray)
        assert values.shape == expected_shape


def test_baseline_model_fields_have_expected_ranges():
    p = build_parameters()
    fields = evaluate_model_fields(p, time=0.0)

    diffusion = fields["diffusion"]
    mortality = fields["mortality"]
    height_growth = fields["height_growth"]
    dbh_growth = fields["dbh_growth"]

    assert np.all(diffusion >= 0.0)
    assert np.all(mortality >= 0.0)

    assert np.min(height_growth) >= 0.0
    assert np.max(height_growth) <= 1.78 / p.model.physical_scales.height_scale

    assert np.min(dbh_growth) >= 0.0
    assert np.max(dbh_growth) <= 0.0135 / p.model.physical_scales.dbh_scale