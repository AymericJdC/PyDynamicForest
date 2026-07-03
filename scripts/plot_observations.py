"""
Plot exported PyDynamicForest observations.

This script loads exported observation NPZ files from an output directory
and generates standard figures for each observation.

Typical usage from the repository root:

    python -m scripts.plot_observations

or with explicit paths:

    python -m scripts.plot_observations ^
        --input-dir outputs/baseline_reduced_sparse ^
        --figures-dir outputs/baseline_reduced_sparse/figures
"""

from argparse import ArgumentParser
from pathlib import Path

from pydynamicforest.io import load_observations_npz_dir
from pydynamicforest.plotting import plot_all_observation_figures


def build_parser() -> ArgumentParser:
    """
    Build command-line argument parser.
    """

    parser = ArgumentParser(
        description="Generate figures from exported PyDynamicForest observations."
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
            "Directory where figures will be written. "
            "Default: <input-dir>/figures"
        ),
    )

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    input_dir: Path = args.input_dir

    if args.figures_dir is None:
        figures_dir = input_dir / "figures"
    else:
        figures_dir = args.figures_dir

    observations = load_observations_npz_dir(input_dir)

    print("Plotting exported observations")
    print("==============================")
    print()
    print(f"Input directory  = {input_dir}")
    print(f"Figures directory = {figures_dir}")
    print(f"Number of observations = {len(observations)}")
    print()

    for observation in observations:
        age = observation["age"]
        step_index = observation["step_index"]

        observation_figures_dir = figures_dir / (
            f"observation_step_{step_index:04d}_age_{age:.3f}"
        )

        figures = plot_all_observation_figures(
            observation,
            output_dir=observation_figures_dir,
        )

        print(f"Observation step={step_index}, age={age:.3f}")
        for figure_name, figure_path in figures.items():
            print(f"  {figure_name:22s} -> {figure_path}")
        print()

    print("Done.")


if __name__ == "__main__":
    main()