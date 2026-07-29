from __future__ import annotations

from .breed_registry import (
    DUCK_BREED_REGISTRY_ID,
    DuckBreed,
    DuckBreedMatch,
    DuckBreedRegistry,
)
from .cut_registry import (
    DUCK_CUT_REGISTRY_ID,
    DuckCut,
    DuckCutMatch,
    DuckCutRegistry,
)
from .type_registry import (
    DUCK_TYPE_REGISTRY_ID,
    DuckType,
    DuckTypeMatch,
    DuckTypeRegistry,
)

__all__ = [
    "DUCK_TYPE_REGISTRY_ID",
    "DUCK_BREED_REGISTRY_ID",
    "DUCK_CUT_REGISTRY_ID",
    "DuckType",
    "DuckTypeMatch",
    "DuckTypeRegistry",
    "DuckBreed",
    "DuckBreedMatch",
    "DuckBreedRegistry",
    "DuckCut",
    "DuckCutMatch",
    "DuckCutRegistry",
]
# BEGIN DUCK PHASE 4 EXPORTS
from app.services.food.knowledge.meat.duck.breed_registry import (
    DuckBreed,
    DuckBreedMatch,
    DuckBreedRegistry,
)
from app.services.food.knowledge.meat.duck.cut_registry import (
    DuckCut,
    DuckCutMatch,
    DuckCutRegistry,
)
from app.services.food.knowledge.meat.duck.parser import (
    DuckParser,
)
from app.services.food.knowledge.meat.duck.parser_models import (
    DuckParseResult,
)
from app.services.food.knowledge.meat.duck.type_registry import (
    DuckType,
    DuckTypeMatch,
    DuckTypeRegistry,
)

_PHASE4_EXPORTS = [
    "DuckType",
    "DuckTypeMatch",
    "DuckTypeRegistry",
    "DuckBreed",
    "DuckBreedMatch",
    "DuckBreedRegistry",
    "DuckCut",
    "DuckCutMatch",
    "DuckCutRegistry",
    "DuckParseResult",
    "DuckParser",
]

try:
    __all__
except NameError:
    __all__ = []

for _name in _PHASE4_EXPORTS:
    if _name not in __all__:
        __all__.append(_name)

del _name
# END DUCK PHASE 4 EXPORTS
# BEGIN DUCK PHASE 5 EXPORTS
from app.services.food.knowledge.meat.duck.attributes import (
    build_duck_attributes,
    extract_duck_bone_status,
    extract_duck_certifications,
    extract_duck_country_code,
    extract_duck_country_text,
    extract_duck_product_name,
    extract_duck_skin_status,
    extract_duck_storage_type,
    extract_duck_weight,
)

_PHASE5_EXPORTS = [
    "build_duck_attributes",
    "extract_duck_product_name",
    "extract_duck_country_text",
    "extract_duck_country_code",
    "extract_duck_weight",
    "extract_duck_storage_type",
    "extract_duck_certifications",
    "extract_duck_bone_status",
    "extract_duck_skin_status",
]

for _name in _PHASE5_EXPORTS:
    if _name not in __all__:
        __all__.append(_name)

del _name
# END DUCK PHASE 5 EXPORTS

# BEGIN DUCK PHASE 9 EXPORTS
from app.services.food.knowledge.meat.duck.provider import (
    DuckKnowledgeProvider,
)
from app.services.food.knowledge.meat.duck.rules import (
    apply_duck_rules,
    deduplicate_strings,
)
from app.services.food.knowledge.meat.duck.scoring import (
    calculate_duck_final_score,
    calculate_duck_knowledge_score,
    calculate_duck_scores,
)

_PHASE9_EXPORTS = [
    "calculate_duck_scores",
    "calculate_duck_knowledge_score",
    "calculate_duck_final_score",
    "apply_duck_rules",
    "deduplicate_strings",
    "DuckKnowledgeProvider",
]

for _name in _PHASE9_EXPORTS:
    if _name not in __all__:
        __all__.append(_name)

del _name
# END DUCK PHASE 9 EXPORTS
