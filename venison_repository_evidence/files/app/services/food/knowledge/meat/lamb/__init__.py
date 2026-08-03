from app.services.food.knowledge.meat.lamb.age_registry import (
    LambAge,
    LambAgeMatch,
    LambAgeRegistry,
)
from app.services.food.knowledge.meat.lamb.attributes import (
    build_lamb_attributes,
    extract_lamb_certifications,
    extract_lamb_country_code,
    extract_lamb_country_text,
    extract_lamb_product_name,
    extract_lamb_storage_type,
    extract_lamb_weight,
)
from app.services.food.knowledge.meat.lamb.breed_registry import (
    LambBreed,
    LambBreedMatch,
    LambBreedRegistry,
)
from app.services.food.knowledge.meat.lamb.cut_registry import (
    LambCut,
    LambCutMatch,
    LambCutRegistry,
)
from app.services.food.knowledge.meat.lamb.parser import (
    LambParser,
)
from app.services.food.knowledge.meat.lamb.parser_models import (
    LambParseResult,
)
from app.services.food.knowledge.meat.lamb.provider import (
    LambKnowledgeProvider,
)
from app.services.food.knowledge.meat.lamb.rules import (
    apply_lamb_rules,
    deduplicate_strings,
)
from app.services.food.knowledge.meat.lamb.scoring import (
    DEFAULT_FINAL_SCORE_WEIGHTS,
    DEFAULT_KNOWLEDGE_WEIGHTS,
    calculate_available_average,
    calculate_lamb_final_score,
    calculate_lamb_knowledge_score,
    calculate_lamb_scores,
    clamp_score,
    extract_registry_scores,
    safe_float,
)


__all__ = [
    "LambAge",
    "LambAgeMatch",
    "LambAgeRegistry",
    "LambBreed",
    "LambBreedMatch",
    "LambBreedRegistry",
    "LambCut",
    "LambCutMatch",
    "LambCutRegistry",
    "LambParseResult",
    "LambParser",
    "LambKnowledgeProvider",
    "build_lamb_attributes",
    "extract_lamb_product_name",
    "extract_lamb_country_text",
    "extract_lamb_country_code",
    "extract_lamb_weight",
    "extract_lamb_storage_type",
    "extract_lamb_certifications",
    "DEFAULT_KNOWLEDGE_WEIGHTS",
    "DEFAULT_FINAL_SCORE_WEIGHTS",
    "safe_float",
    "clamp_score",
    "calculate_available_average",
    "extract_registry_scores",
    "calculate_lamb_knowledge_score",
    "calculate_lamb_scores",
    "calculate_lamb_final_score",
    "apply_lamb_rules",
    "deduplicate_strings",
]
