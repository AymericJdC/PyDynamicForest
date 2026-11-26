# SPDX-License-Identifier: LGPL-3.0-or-later
"""Export of the Écouves A5 dataset published with the JoMB article.

The dataset holds the two input tables of the pipeline, extracted from the
source files used for the article:

``ecouves_a5_tree_inventories.csv``
    Individual-tree records of plot A5 for the inventory years of the study.
``ecouves_measured_heights.csv``
    Measured circumference--total height pairs of plots A1, A2 and A5 used to
    fit the height--DBH allometries.

Running the pipeline with ``[data] trees`` and ``[data] measured_heights``
pointing to these files reproduces the results obtained from the source files.

Usage::

    python -m studies.ecouves_a5.dataset --config CONFIG.toml --output-dir DIR
"""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

import pandas as pd

from . import heights as heights_mod
from .settings import DEFAULT_CONFIG, load_config

TREE_FILE = "ecouves_a5_tree_inventories.csv"
HEIGHT_FILE = "ecouves_measured_heights.csv"
TREE_COLUMNS = (
    "site", "plot", "tree_id", "year", "age", "circumference_cm", "diameter_cm", "status",
    "included_in_reference_state", "plot_area_ha", "expansion_factor_ha",
)


def tree_inventories(inventory_long: Path, years) -> pd.DataFrame:
    """Measured trees of plot A5 in the given inventory years."""

    # read as text so that every value is copied verbatim (no float re-formatting)
    inv = pd.read_csv(inventory_long, encoding="utf-8-sig", dtype=str, keep_default_na=False)
    measured = inv["has_measurement"].str.strip().str.lower().isin({"true", "1", "yes"})
    keep = (inv["plot"] == "Ecouves A5") & measured & inv["year"].astype(int).isin([int(y) for y in years])
    out = inv.loc[keep, list(TREE_COLUMNS)].copy()
    # the source order (by tree, then year) is kept: the completed sample follows it
    return out.reset_index(drop=True)


def measured_heights(gis: Path, francois: Path, plot_codes) -> pd.DataFrame:
    """Measured height pairs, in the order used by the pipeline."""

    m = pd.concat([
        heights_mod.read_gis_measured_heights(gis, plot_codes),
        heights_mod.read_francois_measured_heights(francois, list(plot_codes)),
    ], ignore_index=True)
    return m[list(heights_mod.MEASURED_HEIGHT_COLUMNS)]


def sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def export_dataset(config, output_dir: Path) -> dict[str, str]:
    """Write the two tables and return their SHA-256 checksums."""

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    paths = {k: config.data_path(k) for k in ("inventory_long", "gis", "francois")}
    for k, p in paths.items():
        if p is None or not p.is_file():
            raise FileNotFoundError(f"[data] {k}: {p}")
    trees = tree_inventories(paths["inventory_long"], config.years)
    heights = measured_heights(paths["gis"], paths["francois"], config.section("heights")["plot_codes"])
    trees.to_csv(out / TREE_FILE, index=False, lineterminator="\n")
    heights.to_csv(out / HEIGHT_FILE, index=False, lineterminator="\n")
    return {name: sha256(out / name) for name in (TREE_FILE, HEIGHT_FILE)}


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    ap.add_argument("--data-dir", type=Path, default=None)
    ap.add_argument("--output-dir", type=Path, required=True)
    args = ap.parse_args(argv)
    config = load_config(args.config, data_dir=args.data_dir)
    for name, digest in export_dataset(config, args.output_dir).items():
        print(f"{digest}  {name}")


if __name__ == "__main__":
    main()
