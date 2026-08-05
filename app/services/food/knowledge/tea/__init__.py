"""Tea knowledge domain package.

This package contains Tea-specific registries, parsing, attribute construction,
scoring, rules, and provider orchestration.

Shared food knowledge contracts must not be modified from this package.
"""

from app.services.food.knowledge.tea.parser_models import (
    TeaParseResult,
)

from app.services.food.knowledge.tea.parser import (
    TeaParser,
)

__all__ = [
    "TeaKnowledgeProvider",
    "deduplicate_strings",
    "apply_tea_rules",
    "safe_float",
    "extract_registry_scores",
    "clamp_score",
    "calculate_tea_scores",
    "calculate_tea_knowledge_score",
    "calculate_tea_final_score",
    "calculate_available_weighted_score",
    "calculate_available_average",
    "TEA_KNOWLEDGE_WEIGHTS",
    "TEA_FINAL_SCORE_WEIGHTS",
    "extract_tea_flavor_notes",
    "extract_tea_certifications",
    "extract_tea_caffeine_status",
    "build_tea_attributes",
    "TeaParseResult",
    "TeaParser",
]

from app.services.food.knowledge.tea.attributes import (
    build_tea_attributes,
    extract_tea_caffeine_status,
    extract_tea_certifications,
    extract_tea_flavor_notes,
)

from app.services.food.knowledge.tea.scoring import (
    TEA_FINAL_SCORE_WEIGHTS,
    TEA_KNOWLEDGE_WEIGHTS,
    calculate_available_average,
    calculate_available_weighted_score,
    calculate_tea_final_score,
    calculate_tea_knowledge_score,
    calculate_tea_scores,
    clamp_score,
    extract_registry_scores,
    safe_float,
)

from app.services.food.knowledge.tea.rules import (
    apply_tea_rules,
    deduplicate_strings,
)

from app.services.food.knowledge.tea.provider import (
    TeaKnowledgeProvider,
)
