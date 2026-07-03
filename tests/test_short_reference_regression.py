# SPDX-License-Identifier: LGPL-3.0-or-later
import re
from pathlib import Path

import numpy as np

from simulations.baseline.initial_condition import build_initial_condition
from simulations.baseline.parameters import build_parameters
from simulations.baseline.context import build_context

from pydynamicforest.diagnostics import legacy_mass
from pydynamicforest.solver import simulate
from pydynamicforest.diagnostics import (
    top_height,
    basal_area,
    minimum_density,
)


LEGACY_OUTPUT_PATH = Path("reference_outputs/legacy_short_console_output.txt")


def parse_legacy_short_outputs(path: Path) -> dict[str, float]:
    """
    Parse scalar outputs from legacy_short_console_output.txt.
    """

    if not path.exists():
        raise FileNotFoundError(f"Legacy output file not found: {path}")

    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = path.read_text(encoding="cp1252")


    patterns = {
        "top_height_final": r"Simulated top height at final short age\s*=\s*([0-9eE+\-.]+)",
        "basal_area_final": r"Simulated basal area at final short age\s*=\s*([0-9eE+\-.]+)",
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


def test_refactored_short_run_matches_legacy_short_reference():
    legacy = parse_legacy_short_outputs(LEGACY_OUTPUT_PATH)

    x0 = build_initial_condition()
    p = build_parameters()
    c = build_context()

    results = simulate(x0, p, c, max_steps=10)

    U_final = results.final_state.U
    grid = p.numerics.grid

    refactored = {
        "top_height_final": top_height(U_final, p),
        "basal_area_final": basal_area(U_final, p),
        "final_mass": legacy_mass(U_final, p),
        "minimum_U": minimum_density(U_final),
    }

    assert results.final_state.step_index == 10
    assert np.isclose(results.final_state.time, 0.51)
    assert np.isclose(results.final_state.age, 18.51)

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
        atol=1e-10,
    )