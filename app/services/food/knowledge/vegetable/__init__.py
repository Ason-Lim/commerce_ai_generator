"""
Vegetable Knowledge Domain.

Sprint 3 implementation governed by:
ADA-MA-2026-018-VEGETABLE.
"""

from app.services.food.knowledge.vegetable.attributes import (
    build_vegetable_attributes,
)
from app.services.food.knowledge.vegetable.parser import (
    VegetableParser,
    parse_vegetable,
    parse_vegetable_product,
)
from app.services.food.knowledge.vegetable.parser_models import (
    VegetableParseResult,
)
from app.services.food.knowledge.vegetable.provider import (
    VegetableKnowledgeProvider,
)
from app.services.food.knowledge.vegetable.rules import (
    build_vegetable_rules,
    evaluate_vegetable_rules,
    split_vegetable_rule_messages,
)
from app.services.food.knowledge.vegetable.scoring import (
    DEFAULT_VEGETABLE_SCORE_WEIGHTS,
    calculate_vegetable_final_score,
    calculate_vegetable_information_score,
    calculate_vegetable_scores,
)

__all__ = [
    "VegetableKnowledgeProvider",
    "VegetableParser",
    "VegetableParseResult",
    "parse_vegetable",
    "parse_vegetable_product",
    "build_vegetable_attributes",
    "calculate_vegetable_scores",
    "calculate_vegetable_final_score",
    "calculate_vegetable_information_score",
    "DEFAULT_VEGETABLE_SCORE_WEIGHTS",
    "evaluate_vegetable_rules",
    "split_vegetable_rule_messages",
    "build_vegetable_rules",
]
