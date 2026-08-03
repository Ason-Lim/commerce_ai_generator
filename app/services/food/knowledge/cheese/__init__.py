from app.services.food.knowledge.cheese.aging_registry import (
    CHEESE_AGING_REGISTRY_ID,
    CheeseAging,
    CheeseAgingMatch,
    CheeseAgingRegistry,
)
from app.services.food.knowledge.cheese.milk_source_registry import (
    CHEESE_MILK_SOURCE_REGISTRY_ID,
    CheeseMilkSource,
    CheeseMilkSourceMatch,
    CheeseMilkSourceRegistry,
)
from app.services.food.knowledge.cheese.origin_registry import (
    CHEESE_ORIGIN_REGISTRY_ID,
    CheeseOrigin,
    CheeseOriginMatch,
    CheeseOriginRegistry,
)
from app.services.food.knowledge.cheese.texture_registry import (
    CHEESE_TEXTURE_REGISTRY_ID,
    CheeseTexture,
    CheeseTextureMatch,
    CheeseTextureRegistry,
)
from app.services.food.knowledge.cheese.type_registry import (
    CHEESE_TYPE_REGISTRY_ID,
    CheeseType,
    CheeseTypeMatch,
    CheeseTypeRegistry,
)


__all__ = [
    "CHEESE_TYPE_REGISTRY_ID",
    "CHEESE_MILK_SOURCE_REGISTRY_ID",
    "CHEESE_ORIGIN_REGISTRY_ID",
    "CHEESE_TEXTURE_REGISTRY_ID",
    "CHEESE_AGING_REGISTRY_ID",
    "CheeseType",
    "CheeseTypeMatch",
    "CheeseTypeRegistry",
    "CheeseMilkSource",
    "CheeseMilkSourceMatch",
    "CheeseMilkSourceRegistry",
    "CheeseOrigin",
    "CheeseOriginMatch",
    "CheeseOriginRegistry",
    "CheeseTexture",
    "CheeseTextureMatch",
    "CheeseTextureRegistry",
    "CheeseAging",
    "CheeseAgingMatch",
    "CheeseAgingRegistry",
]

from app.services.food.knowledge.cheese.parser import (
    CheeseParser,
)
from app.services.food.knowledge.cheese.parser_models import (
    CheeseParseResult,
)

__all__.extend(
    [
        "CheeseParseResult",
        "CheeseParser",
    ]
)

from app.services.food.knowledge.cheese.attributes import (
    build_cheese_attributes,
    extract_cheese_certifications,
    extract_cheese_country_code,
    extract_cheese_country_text,
    extract_cheese_fat_content,
    extract_cheese_packaging_type,
    extract_cheese_pasteurization,
    extract_cheese_product_name,
    extract_cheese_rind_type,
    extract_cheese_storage_type,
    extract_cheese_weight,
)

__all__.extend(
    [
        "build_cheese_attributes",
        "extract_cheese_product_name",
        "extract_cheese_country_text",
        "extract_cheese_country_code",
        "extract_cheese_weight",
        "extract_cheese_storage_type",
        "extract_cheese_packaging_type",
        "extract_cheese_pasteurization",
        "extract_cheese_certifications",
        "extract_cheese_fat_content",
        "extract_cheese_rind_type",
    ]
)

from app.services.food.knowledge.cheese.scoring import (
    CHEESE_FINAL_SCORE_WEIGHTS,
    CHEESE_KNOWLEDGE_WEIGHTS,
    calculate_available_average,
    calculate_available_weighted_score,
    calculate_cheese_final_score,
    calculate_cheese_knowledge_score,
    calculate_cheese_scores,
    clamp_score,
    extract_registry_scores,
    safe_float,
)

__all__.extend(
    [
        "CHEESE_KNOWLEDGE_WEIGHTS",
        "CHEESE_FINAL_SCORE_WEIGHTS",
        "safe_float",
        "clamp_score",
        "calculate_available_average",
        "calculate_available_weighted_score",
        "extract_registry_scores",
        "calculate_cheese_knowledge_score",
        "calculate_cheese_scores",
        "calculate_cheese_final_score",
    ]
)

from app.services.food.knowledge.cheese.rules import (
    apply_cheese_rules,
    deduplicate_strings,
)

__all__.extend(
    [
        "apply_cheese_rules",
        "deduplicate_strings",
    ]
)

from app.services.food.knowledge.cheese.provider import (
    CheeseKnowledgeProvider,
)

__all__.extend(
    [
        "CheeseKnowledgeProvider",
    ]
)
