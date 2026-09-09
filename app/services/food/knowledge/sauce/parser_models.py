"""Immutable parser-result contract for the Sauce knowledge domain."""

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class SauceParseResult:
    """Normalized, evidence-preserving result returned by a future parser."""

    family: str = "unknown"
    texture: str = "unknown"
    heat_level: str = "unknown"
    intended_uses: Tuple[str, ...] = ()
    matched_evidence: Tuple[str, ...] = ()
    unresolved_evidence: Tuple[str, ...] = ()
    conflicts: Tuple[str, ...] = ()
    confidence: float = 0.0
    completeness: float = 0.0

    def __post_init__(self) -> None:
        tuple_fields = (
            "intended_uses",
            "matched_evidence",
            "unresolved_evidence",
            "conflicts",
        )
        for field_name in tuple_fields:
            if not isinstance(getattr(self, field_name), tuple):
                raise TypeError(f"{field_name} must be a tuple")

        for field_name in ("confidence", "completeness"):
            value = getattr(self, field_name)
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                raise TypeError(f"{field_name} must be numeric")
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{field_name} must be between 0.0 and 1.0")
