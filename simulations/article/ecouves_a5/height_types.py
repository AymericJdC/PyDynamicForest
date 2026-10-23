"""Typed domain objects for generic height assignment (Q-9E.2)."""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping
import math

class ProviderCategory(str, Enum):
    OBSERVED="observed"; FIXED_TEST="fixed_test"; CALLABLE="callable"; MISSING="missing"; COMPOSITE="composite"
class UncertaintyKind(str, Enum):
    NOT_APPLICABLE="not_applicable"; UNKNOWN="unknown"; STANDARD_DEVIATION="standard_deviation"; INTERVAL="interval"
class AdapterMode(str, Enum):
    REFERENCE_STATE="reference_state"; MEASURED_INVENTORY="measured_inventory"

def _frozen_mapping(value: Mapping[str, Any] | None) -> Mapping[str, Any]:
    return MappingProxyType(dict(value or {}))

@dataclass(frozen=True)
class TreeRecord:
    tree_id: str | int
    year: int
    age: int | None
    diameter_cm: float
    weight_ha: float
    circumference_cm: float | None=None
    status: str | None=None
    series_status: str | None=None
    inclusion_rule: str | None=None
    site: str | None=None
    plot: str | None=None
    def __post_init__(self):
        if not math.isfinite(self.diameter_cm) or self.diameter_cm <= 0: raise ValueError("diameter_cm must be finite and positive")
        if not math.isfinite(self.weight_ha) or self.weight_ha <= 0: raise ValueError("weight_ha must be finite and positive")

@dataclass(frozen=True)
class StandContext:
    site: str; plot: str; year: int; age: int | None; plot_area_ha: float
    series_status: str; selected_inclusion_rule: str; adapter_mode: AdapterMode=AdapterMode.REFERENCE_STATE
    metadata: Mapping[str, Any]=field(default_factory=dict)
    def __post_init__(self):
        if not math.isfinite(self.plot_area_ha) or self.plot_area_ha <= 0: raise ValueError("plot_area_ha must be finite and positive")
        object.__setattr__(self,"metadata",_frozen_mapping(self.metadata))

@dataclass(frozen=True)
class HeightProviderMetadata:
    provider_id: str; name: str; version: str; category: ProviderCategory; deterministic: bool
    description: str=""; source: str | None=None; metadata: Mapping[str, Any]=field(default_factory=dict)
    def __post_init__(self): object.__setattr__(self,"metadata",_frozen_mapping(self.metadata))

@dataclass(frozen=True)
class HeightUncertainty:
    kind: UncertaintyKind=UncertaintyKind.UNKNOWN
    standard_deviation_m: float | None=None; lower_m: float | None=None; upper_m: float | None=None
    confidence_level: float | None=None; comment: str=""
    def __post_init__(self):
        for name in ("standard_deviation_m","lower_m","upper_m"):
            v=getattr(self,name)
            if v is not None and (not math.isfinite(v) or (name=="standard_deviation_m" and v<0)): raise ValueError(f"invalid {name}")
        if self.kind is UncertaintyKind.STANDARD_DEVIATION and self.standard_deviation_m is None: raise ValueError("standard deviation is required")
        if self.kind is UncertaintyKind.INTERVAL:
            if self.lower_m is None or self.upper_m is None or self.lower_m>self.upper_m: raise ValueError("valid interval bounds are required")

@dataclass(frozen=True)
class AssignedHeight:
    tree_id: str | int; year: int; height_m: float | None; is_missing: bool
    missing_reason: str | None; provider_id: str; provider_category: ProviderCategory
    source: str | None=None; uncertainty: HeightUncertainty=field(default_factory=HeightUncertainty)
    metadata: Mapping[str, Any]=field(default_factory=dict)
    def __post_init__(self):
        if self.is_missing:
            if self.height_m is not None or not self.missing_reason: raise ValueError("missing height requires no value and a reason")
        else:
            if self.height_m is None or not math.isfinite(self.height_m): raise ValueError("assigned height must be finite")
            if self.missing_reason is not None: raise ValueError("non-missing height cannot have a missing reason")
        object.__setattr__(self,"metadata",_frozen_mapping(self.metadata))

@dataclass(frozen=True)
class HeightAssignment:
    context: StandContext; provider: HeightProviderMetadata; heights: tuple[AssignedHeight,...]
    warnings: tuple[str,...]=(); metadata: Mapping[str, Any]=field(default_factory=dict)
    def __post_init__(self): object.__setattr__(self,"metadata",_frozen_mapping(self.metadata))

@dataclass(frozen=True)
class HeightTargets:
    mean_height_m: float | None=None; quadratic_mean_height_m: float | None=None
    dominant_height_m: float | None=None; height_diameter_correlation: float | None=None
    mean_slenderness: float | None=None
