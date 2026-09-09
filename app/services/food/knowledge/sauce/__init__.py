"""Public contracts for the Sauce knowledge domain."""

from .attributes import EvidenceProvenance, SauceAttributes, SauceFamily, SauceHeatLevel, SauceTexture, SauceUse
from .parser import parse_sauce
from .parser_models import SauceParseResult
from .provider import SauceEvaluationResult, SauceKnowledgeProvider
from .rules import SauceRuleResult, apply_sauce_rules
from .scoring import SauceEvidenceScore, score_sauce_evidence

__all__ = [
    "EvidenceProvenance", "SauceAttributes", "SauceEvidenceScore",
    "SauceEvaluationResult", "SauceFamily", "SauceHeatLevel",
    "SauceKnowledgeProvider", "SauceParseResult", "SauceRuleResult",
    "SauceTexture", "SauceUse", "apply_sauce_rules", "parse_sauce",
    "score_sauce_evidence",
]
