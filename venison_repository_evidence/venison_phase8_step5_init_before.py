from __future__ import annotations

from .breed_registry import (
    VENISON_BREED_REGISTRY_ID,
    VenisonBreed,
    VenisonBreedMatch,
    VenisonBreedRegistry,
)
from .cut_registry import (
    VENISON_CUT_REGISTRY_ID,
    VenisonCut,
    VenisonCutMatch,
    VenisonCutRegistry,
)
from .type_registry import (
    VENISON_TYPE_REGISTRY_ID,
    VenisonType,
    VenisonTypeMatch,
    VenisonTypeRegistry,
)

__all__ = [
    "VENISON_TYPE_REGISTRY_ID",
    "VENISON_BREED_REGISTRY_ID",
    "VENISON_CUT_REGISTRY_ID",
    "VenisonType",
    "VenisonTypeMatch",
    "VenisonTypeRegistry",
    "VenisonBreed",
    "VenisonBreedMatch",
    "VenisonBreedRegistry",
    "VenisonCut",
    "VenisonCutMatch",
    "VenisonCutRegistry",
]

from .parser import (
    VenisonParser,
)
from .parser_models import (
    VenisonParseResult,
)

for _name in (
    "VenisonParseResult",
    "VenisonParser",
):
    if _name not in __all__:
        __all__.append(_name)

del _name

# BEGIN VENISON PHASE 6 EXPORTS
from .attributes import (
    build_venison_attributes,
    extract_venison_bone_status,
    extract_venison_certifications,
    extract_venison_country_code,
    extract_venison_country_text,
    extract_venison_product_name,
    extract_venison_skin_status,
    extract_venison_storage_type,
    extract_venison_weight,
)

_PHASE6_EXPORTS = [
    "build_venison_attributes",
    "extract_venison_product_name",
    "extract_venison_country_text",
    "extract_venison_country_code",
    "extract_venison_weight",
    "extract_venison_storage_type",
    "extract_venison_certifications",
    "extract_venison_bone_status",
    "extract_venison_skin_status",
]

for _name in _PHASE6_EXPORTS:
    if _name not in __all__:
        __all__.append(_name)

del _name
del _PHASE6_EXPORTS
# END VENISON PHASE 6 EXPORTS


# BEGIN VENISON PHASE 7 EXPORTS
from .scoring import (
    DEFAULT_KNOWLEDGE_WEIGHTS,
    DEFAULT_FINAL_SCORE_WEIGHTS,
    safe_float,
    clamp_score,
    calculate_available_average,
    extract_registry_scores,
    calculate_venison_knowledge_score,
    calculate_venison_scores,
    calculate_venison_final_score,
)

_PHASE7_EXPORTS = [
    "DEFAULT_KNOWLEDGE_WEIGHTS",
    "DEFAULT_FINAL_SCORE_WEIGHTS",
    "safe_float",
    "clamp_score",
    "calculate_available_average",
    "extract_registry_scores",
    "calculate_venison_knowledge_score",
    "calculate_venison_scores",
    "calculate_venison_final_score",
]

for _name in _PHASE7_EXPORTS:
    if _name not in __all__:
        __all__.append(_name)

del _name
del _PHASE7_EXPORTS
# END VENISON PHASE 7 EXPORTS

# BEGIN VENISON PHASE 8 RULES EXPORTS
from .rules import (
    apply_venison_rules,
    deduplicate_strings,
)

_PHASE8_RULES_EXPORTS = [
    "apply_venison_rules",
    "deduplicate_strings",
]

for _name in _PHASE8_RULES_EXPORTS:
    if _name not in __all__:
        __all__.append(_name)

del _name
del _PHASE8_RULES_EXPORTS
# END VENISON PHASE 8 RULES EXPORTS
