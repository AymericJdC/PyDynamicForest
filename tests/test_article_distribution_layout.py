from pathlib import Path

import matplotlib.pyplot as plt
import pytest

from simulations.article.distribution_figures import generate_distribution_variants


def test_distribution_layout_generation_closes_figures(tmp_path):
    source = Path("outputs/article_simulation")
    if not (source / "state_age_69.npz").is_file():
        pytest.skip("Canonical output is unavailable.")
    generate_distribution_variants(source, tmp_path)
    assert plt.get_fignums() == []
    assert (tmp_path / "figure_A2_joint_density_six_ages.pdf").stat().st_size > 0
    assert (tmp_path / "figure_A3_joint_density_3d.pdf").stat().st_size > 0
    assert (tmp_path / "figure_A4_joint_density_nine_ages.pdf").stat().st_size > 0
