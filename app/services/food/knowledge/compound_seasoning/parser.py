"""Deterministic Foundation parser for Compound Seasonings."""

from .parser_models import CompoundSeasoningParseResult


_SINGLE_HERB_OR_SPICE = frozenset({"basil", "rosemary", "black pepper"})
_EXISTING_DOMAIN_PHRASES = frozenset(
    {"sea salt", "soy sauce", "doenjang", "gochujang", "rice vinegar"}
)
_WET_OR_SAUCE_MARKERS = (
    "wet seasoning paste",
    "liquid marinade",
    "dipping sauce",
)


def _normalize(text: str) -> str:
    return " ".join(text.casefold().strip().split())


def _unknown(reason: str = "unrecognized_compound_seasoning") -> CompoundSeasoningParseResult:
    return CompoundSeasoningParseResult(unresolved=(reason,))


def parse_compound_seasoning(text: str) -> CompoundSeasoningParseResult:
    """Parse bounded dry Compound Seasoning evidence without stealing ownership."""

    if not isinstance(text, str):
        raise TypeError("text must be a string")

    normalized = _normalize(text)
    if not normalized:
        return CompoundSeasoningParseResult()

    if normalized in _SINGLE_HERB_OR_SPICE:
        return CompoundSeasoningParseResult(
            matched_evidence=("delegated:herb_spice",)
        )

    if normalized in _EXISTING_DOMAIN_PHRASES:
        return CompoundSeasoningParseResult(
            matched_evidence=("delegated:existing_domain",)
        )

    if any(marker in normalized for marker in _WET_OR_SAUCE_MARKERS):
        return CompoundSeasoningParseResult(
            unresolved=("wet_or_sauce_boundary",),
            conflicts=("sauce_boundary",),
            matched_evidence=("boundary:sauce",),
        )

    if "curry powder" in normalized:
        return CompoundSeasoningParseResult(
            canonical_id="curry_powder",
            composition_class="curry_blend",
            form="powder",
            usages=("general_seasoning",),
            processing=("ground", "blended"),
            ingredient_roles=("spice",),
            matched_evidence=("composition:curry_blend", "form:powder"),
            confidence=0.9,
            completeness=0.75,
        )

    if "dry rub" in normalized:
        processing = ("blended",)
        if "smoked" in normalized:
            processing = ("smoked", "blended")
        return CompoundSeasoningParseResult(
            canonical_id="dry_rub",
            composition_class="dry_rub",
            form="powder",
            usages=("rub",),
            processing=processing,
            ingredient_roles=("spice", "salt"),
            matched_evidence=("composition:dry_rub",),
            confidence=0.85,
            completeness=0.7,
        )

    if "seasoning mix" in normalized or "seasoning blend" in normalized:
        return CompoundSeasoningParseResult(
            composition_class="seasoning_blend",
            form="dry_mix",
            usages=("general_seasoning",),
            processing=("blended",),
            ingredient_roles=("spice",),
            matched_evidence=("composition:seasoning_blend",),
            confidence=0.6,
            completeness=0.4,
        )

    return _unknown()
