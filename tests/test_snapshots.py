from dataclasses import replace

import numpy as np

from simulations.baseline.initial_condition import build_initial_condition
from simulations.baseline.parameters import build_parameters
from simulations.baseline.context import build_context

from pydynamicforest.solver import simulate, should_save_snapshot
from pydynamicforest.types import OutputSpecification, State


def test_should_save_snapshot_detects_requested_age():
    c = build_context()

    state = State(
        time=0.0,
        age=18.0,
        U=np.zeros((2, 2)),
        step_index=0,
    )

    assert should_save_snapshot(
        state,
        c,
        age_tolerance=1e-12,
    )


def test_should_save_snapshot_rejects_unrequested_age():
    c = build_context()

    state = State(
        time=0.123,
        age=18.123,
        U=np.zeros((2, 2)),
        step_index=1,
    )

    assert not should_save_snapshot(
        state,
        c,
        age_tolerance=1e-12,
    )


def test_simulate_saves_only_requested_snapshot_ages():
    """
    With dt = 0.051 and max_steps = 10, the simulated ages are:

        18.000
        18.051
        ...
        18.255  at step 5
        ...
        18.510  at step 10

    We request snapshots at steps 0, 5 and 10, and disable full trajectory
    storage. We therefore expect exactly 3 snapshots.
    """

    x0 = build_initial_condition()
    p = build_parameters()
    c = build_context()

    output = OutputSpecification(
        snapshot_ages=[18.0, 18.255, 18.51],
        save_full_trajectory=False,
        compute_time_series=True,
        save_figures=False,
        save_tables=False,
    )

    c = replace(c, output=output)

    results = simulate(
        x0,
        p,
        c,
        max_steps=10,
        solver_name="sparse",
    )

    snapshot_ages = [snapshot.age for snapshot in results.snapshots]
    snapshot_steps = [snapshot.step_index for snapshot in results.snapshots]

    assert len(results.snapshots) == 3

    assert snapshot_steps == [0, 5, 10]

    assert np.allclose(
        snapshot_ages,
        [18.0, 18.255, 18.51],
        rtol=1e-12,
        atol=1e-12,
    )


def test_simulate_saves_full_trajectory_when_requested():
    x0 = build_initial_condition()
    p = build_parameters()
    c = build_context()

    output = OutputSpecification(
        snapshot_ages=[],
        save_full_trajectory=True,
        compute_time_series=True,
        save_figures=False,
        save_tables=False,
    )

    c = replace(c, output=output)

    results = simulate(
        x0,
        p,
        c,
        max_steps=10,
        solver_name="sparse",
    )

    # Initial state + 10 time steps
    assert len(results.snapshots) == 11

    assert results.snapshots[0].step_index == 0
    assert results.snapshots[-1].step_index == 10