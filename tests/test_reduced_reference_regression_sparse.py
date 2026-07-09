# SPDX-License-Identifier: LGPL-3.0-or-later
import re
from pathlib import Path

import numpy as np
import pytest

from simulations.baseline.initial_condition import build_initial_condition
from simulations.baseline.parameters import build_parameters
from simulations.baseline.context import build_context

from pydynamicforest.diagnostics import legacy_mass
from pydynamicforest.solver import simulate
from pydynamicforest.diagnostics import top_height, basal_area


LEGACY_OUTPUT_PATH = Path("reference_outputs/legacy_reduced_console_output.txt")


def read_text_windows_safe(path: Path) -> str:
    """
    Read a text file that may have been produced by Windows console redirection.
    """

    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="cp1252")


def parse_legacy_reduced_outputs(path: Path) -> dict[str, float]:
    """
    Parse scalar outputs from the reduced legacy console output.
    """

    if not path.exists():
        raise FileNotFoundError(
            f"Legacy reduced output file not found: {path}. "
            "Run legacy/DynamicForestModel_2D_reduced_reference.py first."
        )

    text = read_text_windows_safe(path)

    patterns = {
        "top_height_final": (
            r"Simulated top height at stand age 69\s*=\s*([0-9eE+\-.]+)"
        ),
        "basal_area_final": (
            r"Simulated basal area at stand age 69\s*=\s*([0-9eE+\-.]+)"
        ),
        "initial_mass": r"Initial mass\s*=\s*([0-9eE+\-.]+)",
        "final_mass": r"Final mass\s*=\s*([0-9eE+\-.]+)",
        "minimum_U": r"Minimum U\s*=\s*([0-9eE+\-.]+)",
    }

    values = {}

    for key, pattern in patterns.items():
        match = re.search(pattern, text)

        if match is None:
            raise ValueError(f"Could not parse '{key}' from {path}")

        values[key] = float(match.group(1))

    return values


@pytest.mark.slow
def test_sparse_reduced_run_matches_legacy_reduced_reference():
    """
    Run the full reduced baseline case with the sparse refactored solver
    and compare key scalar outputs against the reduced legacy reference.

    This test is marked as slow because it runs the full reduced simulation:

        Nx = 20
        Ny = 20
        Nt = 1000
    """

    legacy = parse_legacy_reduced_outputs(LEGACY_OUTPUT_PATH)

    x0 = build_initial_condition()
    p = build_parameters()
    c = build_context()

    results = simulate(
        x0,
        p,
        c,
        max_steps=None,
        solver_name="sparse",
    )

    U_final = results.final_state.U
    grid = p.numerics.grid

    refactored = {
        "top_height_final": top_height(U_final, p),
        "basal_area_final": basal_area(U_final, p),
        "final_mass": legacy_mass(U_final, p),
        "minimum_U": min(results.time_series.minimum_density),
    }

    assert results.final_state.step_index == p.numerics.time.n_steps
    assert np.isclose(results.final_state.time, p.numerics.time.t_end)
    assert np.isclose(results.final_state.age, c.final_age)

    assert np.isclose(
        refactored["top_height_final"],
        legacy["top_height_final"],
        rtol=1e-10,
        atol=1e-10,
    )

    assert np.isclose(
        refactored["basal_area_final"],
        legacy["basal_area_final"],
        rtol=1e-10,
        atol=1e-10,
    )

    assert np.isclose(
        refactored["final_mass"],
        legacy["final_mass"],
        rtol=1e-10,
        atol=1e-10,
    )

    assert np.isclose(
        refactored["minimum_U"],
        legacy["minimum_U"],
        rtol=1e-10,
        atol=1e-240,
    )