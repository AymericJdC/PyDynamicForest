# SPDX-License-Identifier: LGPL-3.0-or-later

import numpy as np
import pytest

from pydynamicforest.solver import get_model_field, model_fields_to_legacy_dict
from pydynamicforest.types import ModelFields


def test_get_model_field_from_legacy_dict():
    fields = {
        "diffusion": np.ones((2, 3)) * 0.1,
        "mortality": np.ones((2, 3)) * 0.2,
    }

    assert np.allclose(
        get_model_field(fields, "diffusion"),
        np.ones((2, 3)) * 0.1,
    )

    assert np.allclose(
        get_model_field(fields, "mortality"),
        np.ones((2, 3)) * 0.2,
    )


def test_get_model_field_from_model_fields():
    fields = ModelFields(
        diffusion=np.ones((2, 3)) * 0.1,
        mortality=np.ones((2, 3)) * 0.2,
        height_growth=np.ones((2, 3)) * 0.3,
        dbh_growth=np.ones((2, 3)) * 0.4,
        status=np.ones((2, 3)) * 0.5,
    )

    assert np.allclose(
        get_model_field(fields, "diffusion"),
        np.ones((2, 3)) * 0.1,
    )

    assert np.allclose(
        get_model_field(fields, "height_growth"),
        np.ones((2, 3)) * 0.3,
    )

    assert np.allclose(
        get_model_field(fields, "status"),
        np.ones((2, 3)) * 0.5,
    )


def test_get_model_field_unknown_field_raises():
    fields = ModelFields(
        diffusion=np.ones((2, 2)),
        mortality=np.ones((2, 2)),
        height_growth=np.ones((2, 2)),
        dbh_growth=np.ones((2, 2)),
    )

    with pytest.raises(KeyError, match="Unknown model field"):
        get_model_field(fields, "unknown")


def test_model_fields_to_legacy_dict_accepts_legacy_dict():
    fields = {
        "diffusion": np.ones((2, 2)) * 0.1,
        "mortality": np.ones((2, 2)) * 0.2,
        "height_growth": np.ones((2, 2)) * 0.3,
        "dbh_growth": np.ones((2, 2)) * 0.4,
        "status": None,
    }

    converted = model_fields_to_legacy_dict(fields)

    assert converted is fields


def test_model_fields_to_legacy_dict_converts_model_fields():
    fields = ModelFields(
        diffusion=np.ones((2, 2)) * 0.1,
        mortality=np.ones((2, 2)) * 0.2,
        height_growth=np.ones((2, 2)) * 0.3,
        dbh_growth=np.ones((2, 2)) * 0.4,
        status=np.ones((2, 2)) * 0.5,
    )

    converted = model_fields_to_legacy_dict(fields)

    assert isinstance(converted, dict)
    assert np.allclose(converted["diffusion"], fields.diffusion)
    assert np.allclose(converted["mortality"], fields.mortality)
    assert np.allclose(converted["height_growth"], fields.height_growth)
    assert np.allclose(converted["dbh_growth"], fields.dbh_growth)
    assert np.allclose(converted["status"], fields.status)