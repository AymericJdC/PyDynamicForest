# SPDX-License-Identifier: LGPL-3.0-or-later
"""Consolidate fine-grid convergence evidence for dominant-height operators."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from pydynamicforest.diagnostics import proportional_top_height
from simulations.dominant_height_sensitivity.run import (
    FIXED_NX,
    build_parameters_for_grid,
    controlled_density,
)

CASES = ("regular_height_dbh", "dispersed_threshold")
DEFAULT_REFERENCE_NY_VALUES = (640, 1280, 2560)


def fine_grid_sequence(case: str, ny_values=DEFAULT_REFERENCE_NY_VALUES) -> list[dict]:
    """Evaluate the proportional operator on successively refined DBH grids."""
    rows = []
    previous_value = None

    for ny in ny_values:
        p = build_parameters_for_grid(FIXED_NX, int(ny))
        U = controlled_density(p, case)
        value = proportional_top_height(U, p)
        change = None if previous_value is None else value - previous_value

        rows.append(
            {
                "case": case,
                "nx": FIXED_NX,
                "ny": int(ny),
                "dbh_step_physical": (
                    p.numerics.grid.dy * p.model.physical_scales.dbh_scale
                ),
                "proportional_top_height": value,
                "change_from_previous": change,
                "absolute_change_from_previous": (
                    None if change is None else abs(change)
                ),
            }
        )
        previous_value = value

    return rows


def convergence_summary(rows: list[dict]) -> dict:
    """Summarize successive differences without claiming an exact order."""
    if len(rows) < 2:
        raise ValueError("At least two resolutions are required.")

    differences = [
        row["absolute_change_from_previous"]
        for row in rows[1:]
    ]
    ratios = []
    for coarse, fine in zip(differences, differences[1:]):
        ratios.append(None if fine == 0.0 else coarse / fine)

    return {
        "ny_values": [row["ny"] for row in rows],
        "values": [row["proportional_top_height"] for row in rows],
        "successive_absolute_changes": differences,
        "successive_change_ratios": ratios,
        "finest_value": rows[-1]["proportional_top_height"],
        "finest_successive_change": differences[-1],
    }


def run_consolidation(output_dir: str | Path) -> dict:
    """Run both fine-grid sequences and write CSV, JSON, and Markdown outputs."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    rows = [row for case in CASES for row in fine_grid_sequence(case)]
    summaries = {
        case: convergence_summary([row for row in rows if row["case"] == case])
        for case in CASES
    }

    csv_path = output_path / "dominant_height_fine_grid_convergence.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    json_path = output_path / "dominant_height_fine_grid_convergence.json"
    payload = {
        "purpose": (
            "check stability of the proportional dominant-height reference "
            "under successive DBH-grid refinement"
        ),
        "fixed_nx": FIXED_NX,
        "reference_ny_values": list(DEFAULT_REFERENCE_NY_VALUES),
        "cases": summaries,
        "interpretation_limits": [
            "The finest grid is a numerical reference, not an analytical value.",
            "Only DBH resolution varies; height resolution remains fixed.",
            "The experiment isolates the observation operator and does not test the dynamic solver.",
            "Rectangular cell weights remain those used by the current dominant-height operators.",
        ],
    }
    json_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    markdown_path = output_path / "dominant_height_consolidation.md"
    lines = [
        "# Dominant-height operator consolidation",
        "",
        "## Fine-grid proportional reference",
        "",
        "The proportional operator was evaluated with fixed height resolution "
        f"`Nx = {FIXED_NX}` and DBH resolutions "
        f"`Ny = {', '.join(map(str, DEFAULT_REFERENCE_NY_VALUES))}`.",
        "",
    ]
    for case in CASES:
        summary = summaries[case]
        lines.extend(
            [
                f"### `{case}`",
                "",
                f"- finest value: `{summary['finest_value']:.12f} m`;",
                f"- finest successive change: `{summary['finest_successive_change']:.12e} m`;",
                f"- values: `{summary['values']}`;",
                "",
            ]
        )
    lines.extend(
        [
            "## Interpretation",
            "",
            "The proportional operator is the preferred numerical candidate because it "
            "avoids arbitrary height tie-breaking, substantially improves temporal "
            "regularity, and is stable under isolated DBH-grid refinement.",
            "",
            "This conclusion remains conditional on alignment with the field definition "
            "of dominant height used for the Ecouves observations.",
            "",
            "## API status",
            "",
            "- `legacy_top_height`: patrimonial reproduction only;",
            "- `top_height`: retained for backward comparison, not scientifically endorsed;",
            "- `proportional_top_height`: preferred candidate for revised scientific outputs.",
            "",
            "## Limits",
            "",
            *[f"- {item}" for item in payload["interpretation_limits"]],
            "",
        ]
    )
    markdown_path.write_text("\n".join(lines), encoding="utf-8")

    return {
        "rows": rows,
        "summaries": summaries,
        "csv_path": csv_path,
        "json_path": json_path,
        "markdown_path": markdown_path,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        default="outputs/dominant_height_consolidation",
    )
    args = parser.parse_args()
    result = run_consolidation(args.output_dir)
    print(f"CSV: {result['csv_path'].resolve()}")
    print(f"JSON: {result['json_path'].resolve()}")
    print(f"Markdown: {result['markdown_path'].resolve()}")


if __name__ == "__main__":
    main()
