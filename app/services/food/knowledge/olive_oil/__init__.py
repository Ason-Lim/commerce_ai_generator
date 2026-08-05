"""Olive Oil knowledge domain package.

Shared food knowledge contracts must not be modified from this package.
"""

from app.services.food.knowledge.olive_oil.grade_registry import (
    OLIVE_OIL_GRADE_REGISTRY_ID,
    OliveOilGrade,
    OliveOilGradeMatch,
    OliveOilGradeRegistry,
)
from app.services.food.knowledge.olive_oil.origin_registry import (
    OLIVE_OIL_ORIGIN_REGISTRY_ID,
    OliveOilOrigin,
    OliveOilOriginMatch,
    OliveOilOriginRegistry,
)
from app.services.food.knowledge.olive_oil.processing_registry import (
    OLIVE_OIL_PROCESSING_REGISTRY_ID,
    OliveOilProcessing,
    OliveOilProcessingMatch,
    OliveOilProcessingRegistry,
)
from app.services.food.knowledge.olive_oil.type_registry import (
    OLIVE_OIL_TYPE_REGISTRY_ID,
    OliveOilType,
    OliveOilTypeMatch,
    OliveOilTypeRegistry,
)
from app.services.food.knowledge.olive_oil.variety_registry import (
    OLIVE_OIL_VARIETY_REGISTRY_ID,
    OliveOilVariety,
    OliveOilVarietyMatch,
    OliveOilVarietyRegistry,
)


__all__ = [
    "OLIVE_OIL_TYPE_REGISTRY_ID",
    "OLIVE_OIL_VARIETY_REGISTRY_ID",
    "OLIVE_OIL_ORIGIN_REGISTRY_ID",
    "OLIVE_OIL_PROCESSING_REGISTRY_ID",
    "OLIVE_OIL_GRADE_REGISTRY_ID",
    "OliveOilType",
    "OliveOilTypeMatch",
    "OliveOilTypeRegistry",
    "OliveOilVariety",
    "OliveOilVarietyMatch",
    "OliveOilVarietyRegistry",
    "OliveOilOrigin",
    "OliveOilOriginMatch",
    "OliveOilOriginRegistry",
    "OliveOilProcessing",
    "OliveOilProcessingMatch",
    "OliveOilProcessingRegistry",
    "OliveOilGrade",
    "OliveOilGradeMatch",
    "OliveOilGradeRegistry",
]

from app.services.food.knowledge.olive_oil.parser_models import (
    OliveOilParseResult,
)

__all__.extend(
    [
        "OliveOilParseResult",
    ]
)

from app.services.food.knowledge.olive_oil.parser import (
    OliveOilParser,
)

__all__.extend(
    [
        "OliveOilParser",
    ]
)

from app.services.food.knowledge.olive_oil.attributes import (
    extract_olive_oil_product_name,
)

__all__.extend(
    [
        "extract_olive_oil_product_name",
    ]
)

from app.services.food.knowledge.olive_oil.attributes import (
    extract_olive_oil_country_code,
    extract_olive_oil_country_text,
)

__all__.extend(
    [
        "extract_olive_oil_country_text",
        "extract_olive_oil_country_code",
    ]
)

from app.services.food.knowledge.olive_oil.attributes import (
    extract_olive_oil_certifications,
    extract_olive_oil_organic_status,
    extract_olive_oil_packaging_type,
    extract_olive_oil_volume,
)

__all__.extend(
    [
        "extract_olive_oil_volume",
        "extract_olive_oil_packaging_type",
        "extract_olive_oil_certifications",
        "extract_olive_oil_organic_status",
    ]
)

from app.services.food.knowledge.olive_oil.attributes import (
    build_olive_oil_attributes,
)

__all__.extend(
    [
        "build_olive_oil_attributes",
    ]
)

from app.services.food.knowledge.olive_oil.scoring import (
    OLIVE_OIL_FINAL_SCORE_WEIGHTS,
    OLIVE_OIL_KNOWLEDGE_WEIGHTS,
    calculate_available_average,
    calculate_available_weighted_score,
    calculate_olive_oil_final_score,
    calculate_olive_oil_knowledge_score,
    calculate_olive_oil_scores,
    clamp_score,
    extract_registry_scores,
    safe_float,
)

__all__.extend(
    [
        "OLIVE_OIL_FINAL_SCORE_WEIGHTS",
        "OLIVE_OIL_KNOWLEDGE_WEIGHTS",
        "calculate_available_average",
        "calculate_available_weighted_score",
        "calculate_olive_oil_final_score",
        "calculate_olive_oil_knowledge_score",
        "calculate_olive_oil_scores",
        "clamp_score",
        "extract_registry_scores",
        "safe_float",
    ]
)

from app.services.food.knowledge.olive_oil.rules import (
    apply_olive_oil_rules,
    deduplicate_strings,
)

__all__.extend(
    [
        "apply_olive_oil_rules",
        "deduplicate_strings",
    ]
)

from app.services.food.knowledge.olive_oil.provider import (
    OliveOilKnowledgeProvider,
)

__all__.extend(
    [
        "OliveOilKnowledgeProvider",
    ]
)
