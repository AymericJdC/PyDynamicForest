from pathlib import Path

import pytest

from simulations.article.distribution_figures import (
    DISPLAY_DBH_MAX_CM,
    EXPLORATORY_3D_AGES,
    MAIN_AGES,
    SUPPLEMENTARY_AGES,
    generate_distribution_variants,
    load_weighted_density,
)


def test_distribution_variant_configuration():
    assert MAIN_AGES == (18.0, 28.0, 38.0, 45.0, 54.0, 69.0)
    assert EXPLORATORY_3D_AGES == (18.0, 45.0, 69.0)
    assert SUPPLEMENTARY_AGES == (18.0, 22.0, 28.0, 33.0, 38.0, 45.0, 54.0, 63.0, 69.0)
    assert DISPLAY_DBH_MAX_CM == 80.0


def test_saved_state_is_converted_to_weighted_density():
    source = Path("outputs/article_simulation")
    if not (source / "state_age_18.npz").is_file():
        pytest.skip("Canonical output is unavailable.")
    item = load_weighted_density(source, 18.0)
    assert item["weighted_density"].shape == (40, 40)
    assert item["weighted_density"].sum() == pytest.approx(1924.34, abs=1.0e-8)


def test_all_distribution_variants_are_generated(tmp_path):
    source = Path("outputs/article_simulation")
    if not (source / "state_age_69.npz").is_file():
        pytest.skip("Canonical output is unavailable.")
    result = generate_distribution_variants(source, tmp_path)
    expected = {
        "figure_A2_joint_density_six_ages.png",
        "figure_A2_joint_density_six_ages.pdf",
        "figure_A3_joint_density_3d.png",
        "figure_A3_joint_density_3d.pdf",
        "figure_A4_joint_density_nine_ages.png",
        "figure_A4_joint_density_nine_ages.pdf",
        "distribution_figure_captions.md",
        "distribution_figure_metadata.json",
    }
    names = {path.name for path in result["files"]}
    assert expected <= names
    for name in expected:
        assert (tmp_path / name).stat().st_size > 0
    captions = (tmp_path / "distribution_figure_captions.md").read_text(encoding="utf-8")
    assert "40 x 40 numerical grid" in captions
    assert "visualization only" in captions
