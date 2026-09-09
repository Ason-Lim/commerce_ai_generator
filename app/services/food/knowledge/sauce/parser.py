"""Deterministic, evidence-preserving parser for Sauce product identity."""

import re
from typing import Iterable, Tuple

from .parser_models import SauceParseResult


_ALIASES = {"catsup": "ketchup"}
_NOISE = {"recommended please"}


def _normalize(text: str) -> str:
    value = re.sub(r"[_\-]+", " ", text.casefold())
    value = re.sub(r"[^a-z0-9/ ]+", " ", value)
    value = " ".join(value.split())
    return _ALIASES.get(value, value)


def _contains(text: str, terms: Iterable[str]) -> Tuple[str, ...]:
    return tuple(term for term in terms if term in text)


def parse_sauce(text: str) -> SauceParseResult:
    """Parse Sauce evidence without promoting ingredient-only identities."""

    normalized = _normalize(text)
    if not normalized or normalized in _NOISE:
        return SauceParseResult(unresolved_evidence=(normalized or "empty input",))

    excluded = (
        "raw wasabi root", "prepared karashi condiment", "yuzu kosho paste",
        "dry shichimi powder", "shio kombu", "seasoned solid kelp",
        "tsuyu broth", "tare", "ume paste", "nori tsukudani preserve",
        "salt", "vinegar", "generic condiment paste",
    )
    formulated = any(term in normalized for term in (
        "wasabi sauce", "karashi mustard sauce", "horseradish cream sauce",
        "yuzu kosho sauce", "shio kombu sauce", "shio kombu dipping sauce",
        "ponzu shoyu dipping sauce", "rayu chili oil sauce",
    ))
    conflict = (
        "sauce" in normalized
        and "paste" in normalized
        and "paste like" not in normalized
    )
    if conflict:
        return SauceParseResult(
            unresolved_evidence=("product form unresolved",),
            conflicts=("sauce identity", "paste identity"),
        )
    if not formulated and normalized in excluded:
        return SauceParseResult(unresolved_evidence=(normalized,))

    family = "unknown"
    if "soy sauce" in normalized or "ponzu" in normalized:
        family = "fermented-liquid"
    elif "doenjang sauce" in normalized:
        family = "fermented-paste"
    elif "mayonnaise" in normalized or "horseradish cream sauce" in normalized:
        family = "emulsified"
    elif "ketchup" in normalized:
        family = "tomato/produce"
    elif any(term in normalized for term in ("chili sauce", "hot sauce", "rayu chili oil sauce")):
        family = "chili/hot"
    elif "demi glace sauce" in normalized:
        family = "savory/reduction"
    elif any(term in normalized for term in ("vinaigrette dressing", "salad dressing", "marinade sauce")):
        family = "dressing/marinade"
    elif "chocolate dessert sauce" in normalized:
        family = "sweet/dessert"
    elif "table sauce" in normalized or formulated or normalized.endswith(" sauce"):
        family = "other"

    texture = "unknown"
    for term, value in (
        ("thin liquid", "liquid"), ("thick viscous", "viscous"),
        ("creamy", "creamy"), ("paste like", "paste-like"), ("chunky", "chunky"),
    ):
        if term in normalized:
            texture = value
            break

    heat_level = "unknown"
    for term, value in (
        ("very hot", "very-hot"), ("medium hot", "medium"),
        ("mild chili", "mild"), ("hot sauce", "hot"), ("mayonnaise", "none"),
    ):
        if term in normalized:
            heat_level = value
            break

    uses = []
    for term, value in (
        ("dipping", "dipping"), ("dressing", "dressing"),
        ("cooking", "cooking"), ("glaze", "glazing"),
        ("marinade", "marinating"), ("spread", "spreading"),
        ("finishing", "finishing"),
    ):
        if term in normalized and value not in uses:
            uses.append(value)

    matched = () if family == "unknown" else (normalized,)
    unresolved = () if family != "unknown" else (normalized,)
    dimensions = sum((family != "unknown", texture != "unknown", heat_level != "unknown", bool(uses)))
    return SauceParseResult(
        family=family,
        texture=texture,
        heat_level=heat_level,
        intended_uses=tuple(uses),
        matched_evidence=matched,
        unresolved_evidence=unresolved,
        confidence=0.0 if family == "unknown" else min(1.0, 0.5 + dimensions * 0.1),
        completeness=dimensions / 4.0,
    )
