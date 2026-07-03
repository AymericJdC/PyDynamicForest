# SPDX-License-Identifier: LGPL-3.0-or-later

"""
Plot comparison figures between exported PyDynamicForest observations.

This script loads exported observation NPZ files from an output directory
and generates comparison figures across stand ages.

Typical usage from the repository root:

    python -m scripts.plot_observation_comparisons

or with explicit paths:

    python -m scripts.plot_observation_comparisons ^
        --input-dir outputs/baseline_reduced_sparse ^
        --figures-dir outputs/baseline_reduced_sparse/figures/comparisons
"""

from argparse import ArgumentParser
from pathlib import Path

from pydynamicforest.io import load_observations_npz_dir
from pydynamicforest.plotting import plot_all_observation_comparison_figures


def build_parser() -> ArgumentParser:
    """
    Build command-line argument parser.
    """

    parser = ArgumentParser(
        description=(
            "Generate comparison figures from exported PyDynamicForest "
            "observations."
        )
    )

    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path("outputs/baseline_reduced_sparse"),
        help=(
            "Output directory containing the observations/ subdirectory. "
            "Default: outputs/baseline_reduced_sparse"
        ),
    )

    parser.add_argument(
        "--figures-dir",
        type=Path,
        default=None,
        help=(
            "Directory where comparison figures will be written. "
            "Default: <input-dir>/figures/comparisons"
        ),
    )

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    input_dir: Path = args.input_dir

    if args.figures_dir is None:
        figures_dir = input_dir / "figures" / "comparisons"
    else:
        figures_dir = args.figures_dir

    observations = load_observations_npz_dir(input_dir)

    figures = plot_all_observation_comparison_figures(
        observations,
        output_dir=figures_dir,
    )

    print("Plotting observation comparison figures")
    print("======================================")
    print()
    print(f"Input directory   = {input_dir}")
    print(f"Figures directory = {figures_dir}")
    print(f"Number of observations = {len(observations)}")
    print()

    print("Generated figures:")
    for name, path in figures.items():
        print(f"  {name:24s} -> {path}")

    print()
    print("Done.")


if __name__ == "__main__":
    main()