"""Local composition provider for Sauce domain evidence."""

import re
from dataclasses import dataclass

from .parser import parse_sauce
from .rules import SauceRuleResult, apply_sauce_rules
from .scoring import SauceEvidenceScore, score_sauce_evidence
from .parser_models import SauceParseResult


@dataclass(frozen=True)
class SauceEvaluationResult:
    canonical_text: str
    parse_result: SauceParseResult
    rule_result: SauceRuleResult
    score_result: SauceEvidenceScore


class SauceKnowledgeProvider:
    """Compose established local Sauce contracts without global registration."""

    def canonicalize(self, text: str) -> str:
        if not isinstance(text, str):
            raise TypeError("text must be a string")
        value = re.sub(r"[_-]+", " ", text.casefold())
        value = " ".join(value.split())
        return {"catsup": "ketchup"}.get(value, value)

    def evaluate(self, text: str) -> SauceEvaluationResult:
        canonical = self.canonicalize(text)
        parsed = parse_sauce(canonical)
        ruled = apply_sauce_rules(canonical)
        conflicts = tuple(name for name in parsed.conflicts if name in {"family", "texture", "heat_level", "intended_use", "provenance"})
        scored = score_sauce_evidence(
            family=float(parsed.family != "unknown"),
            texture=float(parsed.texture != "unknown"),
            heat_level=float(parsed.heat_level != "unknown"),
            intended_use=float(bool(parsed.intended_uses)),
            provenance=float(bool(parsed.matched_evidence)),
            conflicts=conflicts,
        )
        return SauceEvaluationResult(canonical, parsed, ruled, scored)
