# SPDX-License-Identifier: LGPL-3.0-or-later
from simulations.baseline.initial_condition import build_initial_condition
from simulations.baseline.parameters import build_parameters
from simulations.baseline.context import build_context

from pydynamicforest.initial_conditions import build_initial_state
from pydynamicforest.numerics import (
    compute_derived_quantities,
    check_status_field_bounds,
)


def test_initial_derived_quantities_are_valid():
    x0 = build_initial_condition()
    p = build_parameters()
    c = build_context()

    state0 = build_initial_state(x0, p, c)
    derived = compute_derived_quantities(state0, p)

    assert derived.cumulative_distribution.shape == state0.U.shape
    assert derived.status_field.shape == state0.U.shape

    assert abs(derived.total_mass - x0.mass_target) < 1e-8
    assert derived.minimum_density >= -p.numerics.positivity_tolerance

    assert check_status_field_bounds(
        derived.status_field,
        tolerance=p.numerics.positivity_tolerance,
    )