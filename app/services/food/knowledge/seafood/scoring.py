from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.services.food.knowledge.common import (
    first_numeric_score,
    weighted_average,
)
from app.services.food.knowledge.common.constants import (
    PRICE_SCORE_KEYS,
    QUALITY_SCORE_KEYS,
    TRUST_SCORE_KEYS,
)
from app.services.food.knowledge.models import (
    FoodKnowledgeContext,
)


DEFAULT_SEAFOOD_SCORE_WEIGHTS = {
    "quality": 0.35,
    "price": 0.20,
    "trust": 0.20,
    "information": 0.25,
}


def calculate_seafood_scores(
    product: Mapping[str, Any],
    attributes: Mapping[str, Any],
    context: FoodKnowledgeContext | None = None,
) -> dict[str, float]:
    if not isinstance(product, Mapping):
        raise TypeError(
            "product must be a Mapping"
        )

    if not isinstance(attributes, Mapping):
        raise TypeError(
            "attributes must be a Mapping"
        )

    _ = context

    return {
        "quality": first_numeric_score(
            product,
            QUALITY_SCORE_KEYS,
        ),
        "price": first_numeric_score(
            product,
            PRICE_SCORE_KEYS,
        ),
        "trust": first_numeric_score(
            product,
            TRUST_SCORE_KEYS,
        ),
        "information": (
            calculate_seafood_information_score(
                attributes
            )
        ),
    }


def calculate_seafood_final_score(
    scores: Mapping[str, float],
    context: FoodKnowledgeContext | None = None,
) -> float:
    if not isinstance(scores, Mapping):
        raise TypeError(
            "scores must be a Mapping"
        )

    _ = context

    return weighted_average(
        scores,
        DEFAULT_SEAFOOD_SCORE_WEIGHTS,
    )


def calculate_seafood_information_score(
    attributes: Mapping[str, Any],
) -> float:
    if not isinstance(attributes, Mapping):
        raise TypeError(
            "attributes must be a Mapping"
        )

    field_names = (
        "product_name",
        "species",
        "seafood_group",
        "origin",
        "processing_state",
        "weight",
    )

    available_count = sum(
        _is_available(
            attributes.get(field_name)
        )
        for field_name in field_names
    )

    return round(
        available_count
        / len(field_names)
        * 100.0,
        2,
    )


def _is_available(
    value: Any,
) -> bool:
    if value is None:
        return False

    if isinstance(value, str):
        return bool(value.strip())

    return True


__all__ = [
    "DEFAULT_SEAFOOD_SCORE_WEIGHTS",
    "calculate_seafood_scores",
    "calculate_seafood_final_score",
    "calculate_seafood_information_score",
]
