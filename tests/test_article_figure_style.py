import matplotlib as mpl

from simulations.article.figure_style import (
    ARTICLE_FIGURE_STYLE,
    apply_article_figure_style,
)


def test_article_figure_style_uses_serif_scientific_typography():
    apply_article_figure_style()
    assert mpl.rcParams["font.family"] == ["serif"]
    assert mpl.rcParams["mathtext.fontset"] == "stix"
    assert "STIXGeneral" in mpl.rcParams["font.serif"]
    assert mpl.rcParams["pdf.fonttype"] == 42
    assert ARTICLE_FIGURE_STYLE["axes.labelsize"] == 9.0
