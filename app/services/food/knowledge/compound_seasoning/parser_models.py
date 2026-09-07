"""Normalized contracts for Compound Seasoning parsing."""

from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass(frozen=True)
class CompoundSeasoningParseResult:
    """Deterministic, evidence-preserving Compound Seasoning parse result."""

    canonical_id: Optional[str] = None
    composition_class: Optional[str] = None
    form: Optional[str] = None
    usages: Tuple[str, ...] = ()
    origins: Tuple[str, ...] = ()
    processing: Tuple[str, ...] = ()
    ingredient_roles: Tuple[str, ...] = ()
    unresolved: Tuple[str, ...] = ()
    conflicts: Tuple[str, ...] = ()
    matched_evidence: Tuple[str, ...] = ()
    confidence: float = 0.0
    completeness: float = 0.0

    def __post_init__(self) -> None:
        tuple_fields = (
            "usages",
            "origins",
            "processing",
            "ingredient_roles",
            "unresolved",
            "conflicts",
            "matched_evidence",
        )
        for field_name in tuple_fields:
            if not isinstance(getattr(self, field_name), tuple):
                raise TypeError(f"{field_name} must be a tuple")

        for field_name in ("confidence", "completeness"):
            value = getattr(self, field_name)
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise TypeError(f"{field_name} must be numeric")
            if not 0.0 <= float(value) <= 1.0:
                raise ValueError(f"{field_name} must be between 0 and 1")
            object.__setattr__(self, field_name, float(value))
