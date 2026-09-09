"""Immutable attributes and canonical taxonomy for the Sauce domain."""

from dataclasses import dataclass
from enum import Enum
from typing import Tuple


class SauceFamily(Enum):
    """Canonical formulation family for a sauce product."""

    FERMENTED_LIQUID = "fermented-liquid"
    FERMENTED_PASTE = "fermented-paste"
    EMULSIFIED = "emulsified"
    TOMATO_PRODUCE = "tomato/produce"
    CHILI_HOT = "chili/hot"
    SAVORY_REDUCTION = "savory/reduction"
    DRESSING_MARINADE = "dressing/marinade"
    SWEET_DESSERT = "sweet/dessert"
    OTHER = "other"


class SauceTexture(Enum):
    """Observable texture of a sauce product."""

    LIQUID = "liquid"
    VISCOUS = "viscous"
    CREAMY = "creamy"
    PASTE_LIKE = "paste-like"
    CHUNKY = "chunky"
    UNKNOWN = "unknown"


class SauceHeatLevel(Enum):
    """Declared or evidenced heat intensity."""

    NONE = "none"
    MILD = "mild"
    MEDIUM = "medium"
    HOT = "hot"
    VERY_HOT = "very-hot"
    UNKNOWN = "unknown"


class SauceUse(Enum):
    """Intended culinary use of a sauce product."""

    DIPPING = "dipping"
    DRESSING = "dressing"
    COOKING = "cooking"
    GLAZING = "glazing"
    MARINATING = "marinating"
    SPREADING = "spreading"
    FINISHING = "finishing"
    MULTIPURPOSE = "multipurpose"
    UNKNOWN = "unknown"


class EvidenceProvenance(Enum):
    """Provenance of the evidence supporting the attributes."""

    EXPLICIT_TEXT = "explicit-text"
    NORMALIZED_ALIAS = "normalized-alias"
    DERIVED_RULE = "derived-rule"
    UNRESOLVED = "unresolved"


@dataclass(frozen=True)
class SauceAttributes:
    """Immutable five-axis Sauce taxonomy with supporting evidence."""

    family: SauceFamily = SauceFamily.OTHER
    texture: SauceTexture = SauceTexture.UNKNOWN
    heat_level: SauceHeatLevel = SauceHeatLevel.UNKNOWN
    intended_uses: Tuple[SauceUse, ...] = ()
    provenance: EvidenceProvenance = EvidenceProvenance.UNRESOLVED
    matched_evidence: Tuple[str, ...] = ()
    conflicting_evidence: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "intended_uses", tuple(self.intended_uses))
        object.__setattr__(self, "matched_evidence", tuple(self.matched_evidence))
        object.__setattr__(self, "conflicting_evidence", tuple(self.conflicting_evidence))
