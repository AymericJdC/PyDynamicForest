# SPDX-License-Identifier: LGPL-3.0-or-later
import numpy as np

from simulations.baseline.initial_condition import build_initial_condition
from simulations.baseline.parameters import build_parameters
from simulations.baseline.context import build_context

from pydynamicforest.initial_conditions import build_initial_state
from pydynamicforest.diagnostics import (
    trapezoidal_mass,
    legacy_mass,
    total_mass,
    mass_diagnostics,
)


def test_initial_mass_conventions_are_explicit():
    x0 = build_initial_condition()
    p = build_parameters()
    c = build_context()

    state0 = build_initial_state(x0, p, c)

    trap_mass = trapezoidal_mass(state0.U, p)
    leg_mass = legacy_mass(state0.U, p)
    default_mass = total_mass(state0.U, p)

    assert np.isclose(trap_mass, x0.mass_target)
    assert np.isclose(default_mass, trap_mass)

    assert leg_mass > 0.0
    assert not np.isnan(leg_mass)


def test_mass_diagnostics_contains_expected_keys():
    x0 = build_initial_condition()
    p = build_parameters()
    c = build_context()

    state0 = build_initial_state(x0, p, c)

    diagnostics = mass_diagnostics(state0.U, p)

    assert set(diagnostics.keys()) == {
        "trapezoidal_mass",
        "legacy_mass",
        "absolute_difference",
    }

    assert diagnostics["trapezoidal_mass"] > 0.0
    assert diagnostics["legacy_mass"] > 0.0
    assert diagnostics["absolute_difference"] >= 0.0