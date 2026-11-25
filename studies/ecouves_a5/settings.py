# SPDX-License-Identifier: LGPL-3.0-or-later
"""Configuration of the Écouves A5 study and construction of model parameters."""

from __future__ import annotations

import copy
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from simulations.article.config import ARTICLE_CONFIG
from simulations.article.parameters import build_parameters as build_article_parameters

DEFAULT_CONFIG = Path(__file__).with_name("config.toml")
METRICS = ("N", "G", "Dm", "Dg", "sigma_D", "Hm", "H0", "H0_minus_Hm", "rho_HD")


@dataclass(frozen=True)
class StudyConfig:
    raw: dict
    path: Path
    data_dir: Path | None = None
    years: tuple[int, ...] = field(init=False)
    ages: dict[int, float] = field(init=False)

    def __post_init__(self):
        inv = self.raw["inventories"]
        years = tuple(int(y) for y in inv["years"])
        ages = [float(a) for a in inv["ages"]]
        if len(years) != len(ages) or list(years) != sorted(years):
            raise ValueError("inventories.years must be increasing and match inventories.ages")
        object.__setattr__(self, "years", years)
        object.__setattr__(self, "ages", dict(zip(years, ages)))

    def section(self, name: str) -> dict:
        return self.raw[name]

    def data_path(self, key: str) -> Path | None:
        value = self.raw["data"].get(key, "")
        if not value:
            return None
        path = Path(value)
        if not path.is_absolute() and self.data_dir is not None:
            path = self.data_dir / path
        return path

    @property
    def initial_year(self) -> int:
        return self.years[0]

    @property
    def model(self) -> dict:
        return self.raw["model"]


def load_config(path: Path | str = DEFAULT_CONFIG, data_dir: Path | str | None = None, overrides: dict | None = None) -> StudyConfig:
    """Load the TOML configuration; ``overrides`` replaces values per section."""

    path = Path(path)
    raw = tomllib.loads(path.read_text(encoding="utf-8"))
    for section, values in (overrides or {}).items():
        raw.setdefault(section, {}).update(values)
    return StudyConfig(raw=raw, path=path, data_dir=Path(data_dir) if data_dir else None)


def build_parameters(
    grid_nodes: int,
    mortality: float,
    dbh_growth_rate: float,
    height_growth_rate: float,
    diffusion_scale: float = 1.0,
):
    """Article parameters (time step, domain, laws) with the study's values."""

    cfg = copy.deepcopy(ARTICLE_CONFIG)
    cfg["grid"]["nx"] = int(grid_nodes)
    cfg["grid"]["ny"] = int(grid_nodes)
    cfg["model"]["mortality"]["value"] = float(mortality)
    cfg["model"]["dbh_growth"]["physical_rate"] = float(dbh_growth_rate)
    cfg["model"]["height_growth"]["physical_rate"] = float(height_growth_rate)
    cfg["model"]["diffusion"]["value"] = cfg["model"]["diffusion"]["value"] * float(diffusion_scale)
    return build_article_parameters(cfg)


def parameters_from_config(config: StudyConfig, grid_nodes: int | None = None, **changes):
    m = {**config.model, **changes}
    return build_parameters(
        grid_nodes or m["grid_nodes"],
        m["mortality"],
        m["dbh_growth_rate"],
        m["height_growth_rate"],
        m.get("diffusion_scale", 1.0),
    )
