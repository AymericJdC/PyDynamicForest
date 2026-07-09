# SPDX-License-Identifier: LGPL-3.0-or-later
"""
Plot PyDynamicForest time series diagnostics.

This script reads a time_series.csv file produced by save_simulation_results
and generates standard diagnostic figures.

Typical usage from the repository root:

    python -m scripts.plot_diagnostics

or with explicit paths:

    python -m scripts.plot_diagnostics ^
        --input-file outputs/baseline_reduced_sparse/time_series.csv ^
        --figures-dir outputs/baseline_reduced_sparse/figures/time_series
"""

import csv
from argparse import ArgumentParser
from pathlib import Path

from pydynamicforest.plotting import plot_standard_time_series


def load_time_series_csv(path: str | Path) -> dict[str, list[float]]:
    """
    Load a time_series.csv file as a dictionary of float lists.
    """

    file_path = Path(path)

    if not file_path.exists():
        raise FileNotFoundError(f"Time series file not found: {file_path}")

    data: dict[str, list[float]] = {}

    with file_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)

        if reader.fieldnames is None:
            raise ValueError(f"No header found in {file_path}")

        for field in reader.fieldnames:
            data[field] = []

        for row in reader:
            for field in reader.fieldnames:
                data[field].append(float(row[field]))

    return data


def build_parser() -> ArgumentParser:
    """
    Build command-line argument parser.
    """

    parser = ArgumentParser(
        description="Generate diagnostic figures from a PyDynamicForest time_series.csv file."
    )

    parser.add_argument(
        "--input-file",
        type=Path,
        default=Path("outputs/baseline_reduced_sparse/time_series.csv"),
        help=(
            "Path to the time_series.csv file. "
            "Default: outputs/baseline_reduced_sparse/time_series.csv"
        ),
    )

    parser.add_argument(
        "--figures-dir",
        type=Path,
        default=None,
        help=(
            "Directory where figures will be written. "
            "Default: <input-file parent>/figures/time_series"
        ),
    )

    parser.add_argument(
        "--x-key",
        type=str,
        default="age",
        choices=["age", "time"],
        help="Variable used on the x-axis. Default: age.",
    )

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    input_file: Path = args.input_file

    if args.figures_dir is None:
        figures_dir = input_file.parent / "figures" / "time_series"
    else:
        figures_dir = args.figures_dir

    time_series = load_time_series_csv(input_file)

    figures = plot_standard_time_series(
        time_series,
        output_dir=figures_dir,
        x_key=args.x_key,
    )

    print("Plotting time series diagnostics")
    print("===============================")
    print()
    print(f"Input file        = {input_file}")
    print(f"Figures directory = {figures_dir}")
    print(f"X axis            = {args.x_key}")
    print()

    for name, path in figures.items():
        print(f"  {name:18s} -> {path}")

    print()
    print("Done.")


if __name__ == "__main__":
    main()