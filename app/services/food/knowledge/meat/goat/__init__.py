from __future__ import annotations

from .attributes import (
    build_goat_attributes,
    extract_goat_bone_status,
    extract_goat_certifications,
    extract_goat_country_code,
    extract_goat_country_text,
    extract_goat_product_name,
    extract_goat_skin_status,
    extract_goat_storage_type,
    extract_goat_weight,
)
from .breed_registry import (
    GOAT_BREED_REGISTRY_ID,
    GoatBreed,
    GoatBreedMatch,
    GoatBreedRegistry,
)
from .cut_registry import (
    GOAT_CUT_REGISTRY_ID,
    GoatCut,
    GoatCutMatch,
    GoatCutRegistry,
)
from .parser import (
    GoatParser,
)
from .parser_models import (
    GoatParseResult,
)
from .provider import (
    GoatKnowledgeProvider,
)
from .rules import (
    apply_goat_rules,
    deduplicate_strings,
)
from .scoring import (
    DEFAULT_FINAL_SCORE_WEIGHTS,
    DEFAULT_KNOWLEDGE_WEIGHTS,
    calculate_available_average,
    calculate_goat_final_score,
    calculate_goat_knowledge_score,
    calculate_goat_scores,
    clamp_score,
    extract_registry_scores,
    safe_float,
)
from .type_registry import (
    GOAT_TYPE_REGISTRY_ID,
    GoatType,
    GoatTypeMatch,
    GoatTypeRegistry,
)

__all__ = [
    "GOAT_TYPE_REGISTRY_ID",
    "GOAT_BREED_REGISTRY_ID",
    "GOAT_CUT_REGISTRY_ID",
    "GoatType",
    "GoatTypeMatch",
    "GoatTypeRegistry",
    "GoatBreed",
    "GoatBreedMatch",
    "GoatBreedRegistry",
    "GoatCut",
    "GoatCutMatch",
    "GoatCutRegistry",
    "GoatParseResult",
    "GoatParser",
    "build_goat_attributes",
    "extract_goat_product_name",
    "extract_goat_country_text",
    "extract_goat_country_code",
    "extract_goat_weight",
    "extract_goat_storage_type",
    "extract_goat_certifications",
    "extract_goat_bone_status",
    "extract_goat_skin_status",
    "DEFAULT_KNOWLEDGE_WEIGHTS",
    "DEFAULT_FINAL_SCORE_WEIGHTS",
    "safe_float",
    "clamp_score",
    "calculate_available_average",
    "extract_registry_scores",
    "calculate_goat_knowledge_score",
    "calculate_goat_scores",
    "calculate_goat_final_score",
    "GoatKnowledgeProvider",
    "apply_goat_rules",
    "deduplicate_strings",
]
