from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.services.food.knowledge.seafood.parser_models import (
    SeafoodParseResult,
)


def extract_seafood_product_name(
    product: Mapping[str, Any],
) -> str:
    return str(
        product.get("product_name")
        or product.get("title")
        or product.get("name")
        or product.get("raw_name")
        or product.get("display_name")
        or ""
    ).strip()


def extract_seafood_weight(
    product: Mapping[str, Any],
) -> Any:
    for field_name in (
        "weight",
        "quantity",
        "package_weight",
        "net_weight",
        "weight_text",
    ):
        if field_name not in product:
            continue

        value = product.get(field_name)

        if value is not None:
            return value

    return None


def build_seafood_attributes(
    *,
    product: Mapping[str, Any],
    parse_result: SeafoodParseResult,
) -> dict[str, Any]:
    if not isinstance(product, Mapping):
        raise TypeError(
            "product must be a Mapping"
        )

    if not isinstance(
        parse_result,
        SeafoodParseResult,
    ):
        raise TypeError(
            "parse_result must be SeafoodParseResult"
        )

    return {
        "product_name": (
            extract_seafood_product_name(product)
        ),
        "seafood_group": parse_result.seafood_group,
        "species": parse_result.species,
        "origin": parse_result.origin,
        "grade": parse_result.grade,
        "wild_farmed_status": (
            parse_result.wild_farmed_status
        ),
        "processing_state": (
            parse_result.processing_state
        ),
        "weight": extract_seafood_weight(product),
        "weight_grams": parse_result.weight_grams,
        "confidence": parse_result.confidence,
        "detected_keywords": list(
            parse_result.detected_keywords
        ),
        "warnings": list(
            parse_result.warnings
        ),
        "matched_field_count": (
            parse_result.matched_field_count
        ),
        "is_complete": parse_result.is_complete,
        "is_usable": parse_result.is_usable,
    }


__all__ = [
    "build_seafood_attributes",
    "extract_seafood_product_name",
    "extract_seafood_weight",
]
