# SPDX-License-Identifier: LGPL-3.0-or-later
import re
from pathlib import Path
from time import perf_counter

import numpy as np

from simulations.baseline.initial_condition import build_initial_condition
from simulations.baseline.parameters import build_parameters
from simulations.baseline.context import build_context

from pydynamicforest.solver import simulate
from pydynamicforest.diagnostics import (
    top_height,
    basal_area,
    minimum_density,
    legacy_mass,
)



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
            f"Legacy reduced output file not found: {path}\n"
            "Run the reduced legacy reference first."
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



def relative_difference(a: float, b: float) -> float:
    """
    Compute relative difference safely.
    """

    denominator = max(abs(a), abs(b), 1.0)
    return abs(a - b) / denominator


def main() -> None:
    legacy = parse_legacy_reduced_outputs(LEGACY_OUTPUT_PATH)

    x0 = build_initial_condition()
    p = build_parameters()
    c = build_context()

    start = perf_counter()

    results = simulate(
        x0,
        p,
        c,
        max_steps=None,
    )

    elapsed = perf_counter() - start

    U_final = results.final_state.U

    refactored = {
        "top_height_final": top_height(U_final, p),
        "basal_area_final": basal_area(U_final, p),
        "final_mass": legacy_mass(U_final, p),
        "minimum_U": min(results.time_series.minimum_density),
    }


    print("Reduced reference comparison")
    print("============================")
    print()
    print(f"Legacy output file: {LEGACY_OUTPUT_PATH}")
    print(f"Refactored solver : {results.metadata['solver']}")
    print(f"Elapsed time      : {elapsed:.2f} seconds")
    print()
    print("Final state")
    print("-----------")
    print(f"step_index = {results.final_state.step_index}")
    print(f"time       = {results.final_state.time}")
    print(f"age        = {results.final_state.age}")
    print()
    print("Scalar comparison")
    print("-----------------")

    keys = [
        "top_height_final",
        "basal_area_final",
        "final_mass",
        "minimum_U",
    ]

    for key in keys:
        legacy_value = legacy[key]
        refactored_value = refactored[key]
        abs_diff = abs(refactored_value - legacy_value)
        rel_diff = relative_difference(refactored_value, legacy_value)

        print(f"{key}")
        print(f"  legacy     = {legacy_value}")
        print(f"  refactored = {refactored_value}")
        print(f"  abs diff   = {abs_diff}")
        print(f"  rel diff   = {rel_diff}")
        print()

    print("Note")
    print("----")
    print(
        "The final mass is compared using the legacy mass formula, not the "
        "trapezoidal diagnostic mass."
    )


if __name__ == "__main__":
    main()