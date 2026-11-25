# SPDX-License-Identifier: LGPL-3.0-or-later

import numpy as np

from pydynamicforest.types import ModelFields


def test_model_fields_stores_expected_arrays():
    diffusion = np.ones((3, 4)) * 0.1
    mortality = np.ones((3, 4)) * 0.2
    height_growth = np.ones((3, 4)) * 0.3
    dbh_growth = np.ones((3, 4)) * 0.4
    status = np.ones((3, 4)) * 0.5

    fields = ModelFields(
        diffusion=diffusion,
        mortality=mortality,
        height_growth=height_growth,
        dbh_growth=dbh_growth,
        status=status,
        description="test model fields",
    )

    assert fields.diffusion.shape == (3, 4)
    assert fields.mortality.shape == (3, 4)
    assert fields.height_growth.shape == (3, 4)
    assert fields.dbh_growth.shape == (3, 4)
    assert fields.status.shape == (3, 4)

    assert np.allclose(fields.diffusion, diffusion)
    assert np.allclose(fields.mortality, mortality)
    assert np.allclose(fields.height_growth, height_growth)
    assert np.allclose(fields.dbh_growth, dbh_growth)
    assert np.allclose(fields.status, status)

    assert fields.description == "test model fields"


def test_model_fields_accepts_no_status():
    diffusion = np.ones((2, 2))
    mortality = np.ones((2, 2))
    height_growth = np.ones((2, 2))
    dbh_growth = np.ones((2, 2))

    fields = ModelFields(
        diffusion=diffusion,
        mortality=mortality,
        height_growth=height_growth,
        dbh_growth=dbh_growth,
    )

    assert fields.status is None
    assert fields.description is None