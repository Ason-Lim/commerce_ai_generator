"""
Seafood Knowledge Domain.

Sprint 3 implementation governed by:
ADA-MA-2026-019-SEAFOOD.
"""

from app.services.food.knowledge.seafood.attributes import (
    build_seafood_attributes,
)
from app.services.food.knowledge.seafood.parser import (
    SeafoodParser,
    parse_seafood,
    parse_seafood_product,
)
from app.services.food.knowledge.seafood.parser_models import (
    SeafoodParseResult,
)
from app.services.food.knowledge.seafood.provider import (
    SeafoodKnowledgeProvider,
)
from app.services.food.knowledge.seafood.rules import (
    build_seafood_rules,
    evaluate_seafood_rules,
    split_seafood_rule_messages,
)
from app.services.food.knowledge.seafood.scoring import (
    DEFAULT_SEAFOOD_SCORE_WEIGHTS,
    calculate_seafood_final_score,
    calculate_seafood_information_score,
    calculate_seafood_scores,
)


__all__ = [
    "SeafoodKnowledgeProvider",
    "SeafoodParser",
    "SeafoodParseResult",
    "parse_seafood",
    "parse_seafood_product",
    "build_seafood_attributes",
    "calculate_seafood_scores",
    "calculate_seafood_final_score",
    "calculate_seafood_information_score",
    "DEFAULT_SEAFOOD_SCORE_WEIGHTS",
    "evaluate_seafood_rules",
    "split_seafood_rule_messages",
    "build_seafood_rules",
]
