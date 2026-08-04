from app.services.food.knowledge.coffee.bean_registry import (
    COFFEE_BEAN_REGISTRY_ID,
    CoffeeBean,
    CoffeeBeanMatch,
    CoffeeBeanRegistry,
)
from app.services.food.knowledge.coffee.origin_registry import (
    COFFEE_ORIGIN_REGISTRY_ID,
    CoffeeOrigin,
    CoffeeOriginMatch,
    CoffeeOriginRegistry,
)
from app.services.food.knowledge.coffee.parser import (
    CoffeeParser,
)
from app.services.food.knowledge.coffee.parser_models import (
    CoffeeParseResult,
)
from app.services.food.knowledge.coffee.process_registry import (
    COFFEE_PROCESS_REGISTRY_ID,
    CoffeeProcess,
    CoffeeProcessMatch,
    CoffeeProcessRegistry,
)
from app.services.food.knowledge.coffee.roast_registry import (
    COFFEE_ROAST_REGISTRY_ID,
    CoffeeRoast,
    CoffeeRoastMatch,
    CoffeeRoastRegistry,
)


__all__ = [
    "COFFEE_BEAN_REGISTRY_ID",
    "COFFEE_ORIGIN_REGISTRY_ID",
    "COFFEE_ROAST_REGISTRY_ID",
    "COFFEE_PROCESS_REGISTRY_ID",
    "CoffeeBean",
    "CoffeeBeanMatch",
    "CoffeeBeanRegistry",
    "CoffeeOrigin",
    "CoffeeOriginMatch",
    "CoffeeOriginRegistry",
    "CoffeeRoast",
    "CoffeeRoastMatch",
    "CoffeeRoastRegistry",
    "CoffeeProcess",
    "CoffeeProcessMatch",
    "CoffeeProcessRegistry",
    "CoffeeParseResult",
    "CoffeeParser",
]

from app.services.food.knowledge.coffee.attributes import (
    build_coffee_attributes,
    extract_coffee_altitude,
    extract_coffee_certifications,
    extract_coffee_country_code,
    extract_coffee_country_text,
    extract_coffee_decaf,
    extract_coffee_flavor_notes,
    extract_coffee_grind_type,
    extract_coffee_product_form,
    extract_coffee_product_name,
    extract_coffee_roast_date,
    extract_coffee_weight,
)

__all__.extend(
    [
        "build_coffee_attributes",
        "extract_coffee_product_name",
        "extract_coffee_country_text",
        "extract_coffee_country_code",
        "extract_coffee_weight",
        "extract_coffee_grind_type",
        "extract_coffee_product_form",
        "extract_coffee_decaf",
        "extract_coffee_certifications",
        "extract_coffee_flavor_notes",
        "extract_coffee_altitude",
        "extract_coffee_roast_date",
    ]
)

from app.services.food.knowledge.coffee.scoring import (
    COFFEE_FINAL_SCORE_WEIGHTS,
    COFFEE_KNOWLEDGE_WEIGHTS,
    calculate_available_average,
    calculate_available_weighted_score,
    calculate_coffee_final_score,
    calculate_coffee_knowledge_score,
    calculate_coffee_scores,
    clamp_score,
    extract_registry_scores,
    safe_float,
)

__all__.extend(
    [
        "COFFEE_KNOWLEDGE_WEIGHTS",
        "COFFEE_FINAL_SCORE_WEIGHTS",
        "safe_float",
        "clamp_score",
        "calculate_available_average",
        "calculate_available_weighted_score",
        "extract_registry_scores",
        "calculate_coffee_knowledge_score",
        "calculate_coffee_scores",
        "calculate_coffee_final_score",
    ]
)

from app.services.food.knowledge.coffee.rules import (
    apply_coffee_rules,
    deduplicate_strings,
)

__all__.extend(
    [
        "apply_coffee_rules",
        "deduplicate_strings",
    ]
)

from app.services.food.knowledge.coffee.provider import (
    CoffeeKnowledgeProvider,
)

__all__.extend(
    [
        "CoffeeKnowledgeProvider",
    ]
)
