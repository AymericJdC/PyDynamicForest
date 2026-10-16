import pytest

from simulations.article.figures import generate_figures
from simulations.article.full_run import run_article_full


def test_figure_generation_requires_all_primary_density_ages(tmp_path):
    source = tmp_path / "simulation"
    run_article_full(source, max_steps=0, progress=False)
    with pytest.raises(ValueError, match="Expected 1600 density cells at age 45"):
        generate_figures(source, tmp_path / "figures")


def test_figure_generation_from_existing_canonical_output_if_available(tmp_path):
    from pathlib import Path
    source = Path("outputs/article_simulation")
    if not (source / "state_age_69.npz").is_file():
        pytest.skip("Canonical full-run output is not available in this test environment.")
    result = generate_figures(source, tmp_path)
    names = {path.name for path in result["files"]}
    expected = {
        "figure_A_joint_height_dbh_density.png",
        "figure_A_joint_height_dbh_density.pdf",
        "figure_B_stand_trajectories.png",
        "figure_B_stand_trajectories.pdf",
        "figure_C_size_structure_diagnostic.png",
        "figure_C_size_structure_diagnostic.pdf",
        "figure_captions.md",
    }
    assert expected <= names
    for name in expected:
        assert (tmp_path / name).stat().st_size > 0
    assert result["metadata"]["trajectory_commit"] != "unavailable"
