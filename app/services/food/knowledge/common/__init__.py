from app.services.food.knowledge.common.confidence import (
    calculate_field_confidence,
    is_available,
)
from app.services.food.knowledge.common.normalizer import (
    normalize_boolean,
    normalize_volume_ml,
    normalize_weight_grams,
    safe_float,
    safe_int,
)
from app.services.food.knowledge.common.parser import (
    extract_first_number,
    extract_origin,
    extract_price,
    extract_product_name,
    extract_weight_grams,
    extract_weight_text,
    first_non_empty,
)
from app.services.food.knowledge.common.rules import (
    WARNING_SEVERITIES,
    create_rule,
    merge_rule_results,
    split_rule_messages,
)
from app.services.food.knowledge.common.scoring import (
    apply_score_boost,
    clamp_score,
    first_numeric_score,
    normalize_range_score,
    weighted_average,
)
from app.services.food.knowledge.common.text import (
    contains_keyword,
    deduplicate_texts,
    detect_keywords,
    normalize_text,
)
from app.services.food.knowledge.common.base_registry import (
    AliasCandidate,
    AliasMatch,
    BaseAliasRegistry,
    BaseKnowledgeRegistry,
    DomainRegistryConfigurationError,
    DomainRegistryEntryNotFoundError,
    DomainRegistryError,
    normalize_string_list,
    optional_float,
    optional_int,
    optional_string,
)
from app.services.food.knowledge.common.base_model import (
    EntryT,
    RegistryEntry,
    RegistryMatch,
    to_plain_value,
)


from app.services.food.knowledge.common.parser_models import (
    BaseParseResult,
)

from app.services.food.knowledge.common.parser_base import (
    BaseKnowledgeParser,
    ParseResultT,
)

__all__ = [
    "safe_float",
    "safe_int",
    "normalize_boolean",
    "normalize_weight_grams",
    "normalize_volume_ml",
    "normalize_text",
    "contains_keyword",
    "detect_keywords",
    "deduplicate_texts",
    "first_non_empty",
    "extract_product_name",
    "extract_origin",
    "extract_price",
    "extract_weight_text",
    "extract_weight_grams",
    "extract_first_number",
    "clamp_score",
    "normalize_range_score",
    "weighted_average",
    "first_numeric_score",
    "apply_score_boost",
    "calculate_field_confidence",
    "is_available",
    "split_rule_messages",
    "merge_rule_results",
    "create_rule",
    "WARNING_SEVERITIES",
    "AliasCandidate",
    "AliasMatch",
    "BaseAliasRegistry",
    "BaseKnowledgeRegistry",
    "DomainRegistryConfigurationError",
    "DomainRegistryEntryNotFoundError",
    "DomainRegistryError",
    "normalize_string_list",
    "optional_float",
    "optional_int",
    "optional_string",
    "EntryT",
    "RegistryEntry",
    "RegistryMatch",
    "to_plain_value",
    "BaseKnowledgeParser",
    "BaseParseResult",
    "ParseResultT",
]
