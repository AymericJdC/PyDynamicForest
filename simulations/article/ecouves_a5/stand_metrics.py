"""Dendrometric metrics with explicit units.

Circumferences and diameters are centimetres; area is hectares; basal area is m2/ha.
"""
from __future__ import annotations
import math
from collections.abc import Iterable

def circumference_to_diameter_cm(circumference_cm: float) -> float:
    return float(circumference_cm) / math.pi

def quadratic_mean(values: Iterable[float]) -> float:
    vals=[float(v) for v in values]
    if not vals: raise ValueError("quadratic mean requires at least one value")
    return math.sqrt(sum(v*v for v in vals)/len(vals))

def quadratic_circumference_cm(circumferences_cm: Iterable[float]) -> float:
    return quadratic_mean(circumferences_cm)

def quadratic_diameter_cm(diameters_cm: Iterable[float]) -> float:
    return quadratic_mean(diameters_cm)

def density_ha(n_trees: int, plot_area_ha: float) -> float:
    if plot_area_ha <= 0: raise ValueError("plot_area_ha must be positive")
    return n_trees / plot_area_ha

def basal_area_m2_ha(diameters_cm: Iterable[float], plot_area_ha: float) -> float:
    if plot_area_ha <= 0: raise ValueError("plot_area_ha must be positive")
    return sum(math.pi*(float(d)/100.0)**2/4.0 for d in diameters_cm)/plot_area_ha
