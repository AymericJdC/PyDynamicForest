from pathlib import Path
from simulations.article.figures import JOINT_DENSITY_DBH_MAX_CM, PANEL_LABELS, generate_figures

def test_revised_figure_constants_are_explicit():
    assert JOINT_DENSITY_DBH_MAX_CM == 80.0
    assert PANEL_LABELS == ("(a)", "(b)", "(c)", "(d)", "(e)", "(f)")

def test_revised_captions_and_figures_from_canonical_output(tmp_path):
    source = Path("outputs/article_simulation")
    if not (source / "state_age_69.npz").is_file():
        return
    result = generate_figures(source, tmp_path)
    captions = (tmp_path / "figure_captions.md").read_text(encoding="utf-8")
    assert "common logarithmic colour scale" in captions
    assert "numerical diameter domain extends beyond" in captions
    assert "Diameter standard deviation is derived" in captions
    assert result["metadata"]["style"]["png_dpi"] == 300


def test_figure_module_uses_non_interactive_backend():
    import matplotlib

    assert matplotlib.get_backend().lower() == "agg"

