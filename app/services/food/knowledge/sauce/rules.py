"""Deterministic inclusion rules for Sauce product identities."""

import re
from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class SauceRuleResult:
    normalized_identity: str
    status: str
    included: bool
    reasons: Tuple[str, ...] = ()
    conflicts: Tuple[str, ...] = ()


def _normalize(text: str) -> str:
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    value = re.sub(r"[_-]+", " ", text.casefold())
    return " ".join(value.split())


def apply_sauce_rules(text: str) -> SauceRuleResult:
    """Resolve only explicit product-form evidence; ambiguity remains visible."""

    normalized = _normalize(text)
    if "sauce" in normalized and "paste" in normalized and "paste like" not in normalized:
        return SauceRuleResult(normalized, "unresolved", False, ("conflicting product form",), ("sauce", "paste"))

    excluded = {
        "raw wasabi root", "horseradish root", "dry shichimi powder",
        "shio kombu", "seasoned solid kelp", "tsuyu broth", "ume paste",
        "nori tsukudani preserve",
    }
    unresolved = {
        "prepared karashi condiment", "momiji oroshi condiment", "yuzu kosho paste",
        "pure citrus ponzu", "tare", "rayu chili oil condiment", "generic condiment",
    }
    if normalized in excluded:
        return SauceRuleResult(normalized, "excluded", False, ("non-sauce product identity",))
    if normalized in unresolved:
        return SauceRuleResult(normalized, "unresolved", False, ("insufficient formulation evidence",))

    included_terms = (
        "wasabi sauce", "mustard sauce", "karashi mustard sauce",
        "horseradish cream sauce", "yuzu kosho sauce", "shio kombu sauce",
        "ponzu shoyu", "ponzu sauce", "tsuyu dipping sauce", "tsuyu cooking sauce",
    )
    if any(term in normalized for term in included_terms) or normalized.endswith(" sauce"):
        return SauceRuleResult(normalized, "included", True, ("qualified sauce identity",))
    return SauceRuleResult(normalized, "unresolved", False, ("product identity unresolved",))
