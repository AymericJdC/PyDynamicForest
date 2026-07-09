# SPDX-License-Identifier: LGPL-3.0-or-later
from simulations.baseline.initial_condition import build_initial_condition
from simulations.baseline.parameters import build_parameters
from simulations.baseline.context import build_context

from pydynamicforest.initial_conditions import build_initial_state
from pydynamicforest.diagnostics import (
    total_mass,
    basal_area,
    top_height,
    minimum_density,
)


def test_initial_state_diagnostics_are_valid():
    x0 = build_initial_condition()
    p = build_parameters()
    c = build_context()

    state0 = build_initial_state(x0, p, c)

    mass = total_mass(state0.U, p)
    ba = basal_area(state0.U, p)
    htop = top_height(state0.U, p)
    min_u = minimum_density(state0.U)

    assert abs(mass - x0.mass_target) < 1e-8
    assert ba >= 0.0
    assert 0.0 <= htop <= p.model.physical_scales.height_scale
    assert min_u >= -p.numerics.positivity_tolerance