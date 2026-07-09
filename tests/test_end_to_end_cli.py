# SPDX-License-Identifier: LGPL-3.0-or-later

import subprocess
import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def run_module(module_name: str, *args: str) -> subprocess.CompletedProcess:
    """
    Run a Python module from the repository root.

    This tests the actual command-line workflow used by users.
    """

    command = [
        sys.executable,
        "-m",
        module_name,
        *args,
    ]

    result = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, (
        f"Command failed:\n"
        f"{' '.join(command)}\n\n"
        f"STDOUT:\n{result.stdout}\n\n"
        f"STDERR:\n{result.stderr}"
    )

    return result


@pytest.mark.slow
@pytest.mark.e2e
def test_end_to_end_baseline_cli_workflow(tmp_path):
    """
    End-to-end CLI workflow test.

    This test runs the complete user-facing workflow:

        1. run a short baseline simulation;
        2. export time series, metadata, summary and observations;
        3. plot individual observations;
        4. plot observation comparisons;
        5. plot diagnostic time series.

    Outputs are written to pytest's temporary directory.
    """

    output_dir = tmp_path / "baseline_e2e"
    figures_dir = output_dir / "figures"

    # ------------------------------------------------------------------
    # 1. Run configurable baseline script
    # ------------------------------------------------------------------

    run_module(
        "scripts.run_baseline",
        "--max-steps",
        "10",
        "--output-dir",
        str(output_dir),
    )

    assert output_dir.exists()
    assert (output_dir / "time_series.csv").exists()
    assert (output_dir / "metadata.json").exists()
    assert (output_dir / "summary.txt").exists()

    observations_dir = output_dir / "observations"

    assert observations_dir.exists()
    assert observations_dir.is_dir()

    observation_files = list(observations_dir.glob("*.npz"))

    assert len(observation_files) > 0

    # ------------------------------------------------------------------
    # 2. Plot individual observations
    # ------------------------------------------------------------------

    observation_figures_dir = figures_dir / "observations"

    run_module(
        "scripts.plot_observations",
        "--input-dir",
        str(output_dir),
        "--figures-dir",
        str(observation_figures_dir),
    )

    assert observation_figures_dir.exists()
    assert observation_figures_dir.is_dir()

    individual_figure_files = list(observation_figures_dir.rglob("*.png"))

    assert len(individual_figure_files) > 0

    # ------------------------------------------------------------------
    # 3. Plot observation comparisons
    # ------------------------------------------------------------------

    comparison_figures_dir = figures_dir / "comparisons"

    run_module(
        "scripts.plot_observation_comparisons",
        "--input-dir",
        str(output_dir),
        "--figures-dir",
        str(comparison_figures_dir),
    )

    assert comparison_figures_dir.exists()
    assert comparison_figures_dir.is_dir()

    comparison_figure_files = list(comparison_figures_dir.glob("*.png"))

    assert len(comparison_figure_files) > 0

    produced_comparison_names = {
        path.name
        for path in comparison_figure_files
    }

    assert "height_distributions_comparison.png" in produced_comparison_names
    assert "dbh_distributions_comparison.png" in produced_comparison_names

    # The density comparison filename may evolve as heatmap plotting improves.
    # We only require at least one density comparison figure.
    assert any(
        name.startswith("density_fields_comparison")
        and name.endswith(".png")
        for name in produced_comparison_names
    )

    # ------------------------------------------------------------------
    # 4. Plot diagnostic time series
    # ------------------------------------------------------------------

    time_series_figures_dir = figures_dir / "time_series"

    run_module(
        "scripts.plot_diagnostics",
        "--input-file",
        str(output_dir / "time_series.csv"),
        "--figures-dir",
        str(time_series_figures_dir),
    )

    assert time_series_figures_dir.exists()
    assert time_series_figures_dir.is_dir()

    expected_time_series_figures = {
        "total_mass_vs_age.png",
        "legacy_mass_vs_age.png",
        "minimum_density_vs_age.png",
        "top_height_vs_age.png",
        "basal_area_vs_age.png",
    }

    produced_time_series_figures = {
        path.name
        for path in time_series_figures_dir.glob("*.png")
    }

    assert expected_time_series_figures.issubset(produced_time_series_figures)