from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, kw_only=True)
class LayerPolicy:
    layer_id: str
    title: str
    filenames: tuple[str, ...]
    forbidden_module_segments: tuple[
        str,
        ...
    ] = ()
    forbidden_import_symbols: tuple[
        str,
        ...
    ] = ()
    forbidden_call_names: tuple[
        str,
        ...
    ] = ()
    forbidden_call_prefixes: tuple[
        str,
        ...
    ] = ()
    required_class_base: str | None = None
    required_function: str | None = None
    required_call_sequence: tuple[
        str,
        ...
    ] = ()


EXTERNAL_FORBIDDEN_ROOTS: tuple[str, ...] = (
    "requests",
    "httpx",
    "sqlalchemy",
    "streamlit",
)


PARSER_POLICY = LayerPolicy(
    layer_id="parser",
    title="Parser Layer",
    filenames=(
        "parser.py",
        "parser_models.py",
    ),
    forbidden_module_segments=(
        "scoring",
        "rules",
        "provider",
    ),
    forbidden_import_symbols=(
        "FoodKnowledgeResult",
        "FoodKnowledgeProvider",
    ),
    forbidden_call_names=(
        "FoodKnowledgeResult",
        "FoodKnowledgeProvider",
        "apply_cheese_rules",
        "calculate_cheese_scores",
        "calculate_cheese_final_score",
    ),
    forbidden_call_prefixes=(
        "calculate_",
    ),
)


ATTRIBUTE_POLICY = LayerPolicy(
    layer_id="attributes",
    title="Attribute Layer",
    filenames=(
        "attributes.py",
    ),
    forbidden_module_segments=(
        "scoring",
        "rules",
        "provider",
    ),
    forbidden_import_symbols=(
        "FoodKnowledgeResult",
        "FoodKnowledgeProvider",
    ),
    forbidden_call_names=(
        "FoodKnowledgeResult",
        "FoodKnowledgeProvider",
        "calculate_cheese_scores",
        "calculate_cheese_final_score",
        "apply_cheese_rules",
    ),
    forbidden_call_prefixes=(
        "calculate_",
    ),
)


SCORING_POLICY = LayerPolicy(
    layer_id="scoring",
    title="Scoring Layer",
    filenames=(
        "scoring.py",
    ),
    forbidden_module_segments=(
        "parser",
        "rules",
        "provider",
    ),
    forbidden_import_symbols=(
        "CheeseParser",
        "FoodKnowledgeResult",
        "FoodKnowledgeProvider",
    ),
    forbidden_call_names=(
        "parse",
        "parse_product",
        "CheeseParser",
        "FoodKnowledgeResult",
        "FoodKnowledgeProvider",
        "apply_cheese_rules",
    ),
)


RULE_POLICY = LayerPolicy(
    layer_id="rules",
    title="Rule Layer",
    filenames=(
        "rules.py",
    ),
    forbidden_module_segments=(
        "parser",
        "scoring",
        "provider",
    ),
    forbidden_import_symbols=(
        "CheeseParser",
        "FoodKnowledgeResult",
        "FoodKnowledgeProvider",
    ),
    forbidden_call_names=(
        "parse",
        "parse_product",
        "CheeseParser",
        "FoodKnowledgeResult",
        "FoodKnowledgeProvider",
        "calculate_cheese_scores",
        "calculate_cheese_final_score",
    ),
)


PROVIDER_POLICY = LayerPolicy(
    layer_id="provider",
    title="Provider Layer",
    filenames=(
        "provider.py",
    ),
    required_class_base=(
        "FoodKnowledgeProvider"
    ),
    required_function="analyze",
    required_call_sequence=(
        "parse_product",
        "build_cheese_attributes",
        "calculate_cheese_scores",
        "apply_cheese_rules",
        "calculate_cheese_final_score",
        "FoodKnowledgeResult",
    ),
)


DEFAULT_LAYER_POLICIES: tuple[
    LayerPolicy,
    ...
] = (
    PARSER_POLICY,
    ATTRIBUTE_POLICY,
    SCORING_POLICY,
    RULE_POLICY,
    PROVIDER_POLICY,
)


__all__ = [
    "LayerPolicy",
    "EXTERNAL_FORBIDDEN_ROOTS",
    "PARSER_POLICY",
    "ATTRIBUTE_POLICY",
    "SCORING_POLICY",
    "RULE_POLICY",
    "PROVIDER_POLICY",
    "DEFAULT_LAYER_POLICIES",
]
