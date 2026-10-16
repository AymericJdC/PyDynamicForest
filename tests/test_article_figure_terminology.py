from pathlib import Path


def test_figure_scripts_use_quadrature_weighted_stem_number_terminology():
    paths = (
        Path("simulations/article/figures.py"),
        Path("simulations/article/distribution_figures.py"),
    )
    combined = "\n".join(path.read_text(encoding="utf-8") for path in paths)
    assert "cell$^{-1}$" not in combined
    assert "Stem density per grid cell" not in combined
    assert "Quadrature-weighted stem number" in combined
    assert "quadrature-weighted contribution to stand density" in combined
