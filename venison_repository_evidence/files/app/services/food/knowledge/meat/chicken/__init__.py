from app.services.food.knowledge.meat.chicken.attributes import (
    build_chicken_attributes,
    extract_chicken_bone_status,
    extract_chicken_certifications,
    extract_chicken_country_code,
    extract_chicken_country_text,
    extract_chicken_product_name,
    extract_chicken_skin_status,
    extract_chicken_storage_type,
    extract_chicken_weight,
)
from app.services.food.knowledge.meat.chicken.breed_registry import (
    ChickenBreed,
    ChickenBreedMatch,
    ChickenBreedRegistry,
)
from app.services.food.knowledge.meat.chicken.cut_registry import (
    ChickenCut,
    ChickenCutMatch,
    ChickenCutRegistry,
)
from app.services.food.knowledge.meat.chicken.parser import (
    ChickenParser,
)
from app.services.food.knowledge.meat.chicken.provider import (
    ChickenKnowledgeProvider,
)
from app.services.food.knowledge.meat.chicken.parser_models import (
    ChickenParseResult,
)
from app.services.food.knowledge.meat.chicken.rules import (
    apply_chicken_rules,
    deduplicate_strings,
)
from app.services.food.knowledge.meat.chicken.scoring import (
    DEFAULT_FINAL_SCORE_WEIGHTS,
    DEFAULT_KNOWLEDGE_WEIGHTS,
    calculate_available_average,
    calculate_chicken_final_score,
    calculate_chicken_knowledge_score,
    calculate_chicken_scores,
    clamp_score,
    extract_registry_scores,
    safe_float,
)
from app.services.food.knowledge.meat.chicken.type_registry import (
    ChickenType,
    ChickenTypeMatch,
    ChickenTypeRegistry,
)


__all__ = [
    "ChickenType",
    "ChickenTypeMatch",
    "ChickenTypeRegistry",
    "ChickenBreed",
    "ChickenBreedMatch",
    "ChickenBreedRegistry",
    "ChickenCut",
    "ChickenCutMatch",
    "ChickenCutRegistry",
    "ChickenParseResult",
    "ChickenParser",
    "ChickenKnowledgeProvider",
    "build_chicken_attributes",
    "extract_chicken_product_name",
    "extract_chicken_country_text",
    "extract_chicken_country_code",
    "extract_chicken_weight",
    "extract_chicken_storage_type",
    "extract_chicken_certifications",
    "extract_chicken_bone_status",
    "extract_chicken_skin_status",
    "DEFAULT_KNOWLEDGE_WEIGHTS",
    "DEFAULT_FINAL_SCORE_WEIGHTS",
    "safe_float",
    "clamp_score",
    "calculate_available_average",
    "extract_registry_scores",
    "calculate_chicken_knowledge_score",
    "calculate_chicken_scores",
    "calculate_chicken_final_score",
    "apply_chicken_rules",
    "deduplicate_strings",
]
