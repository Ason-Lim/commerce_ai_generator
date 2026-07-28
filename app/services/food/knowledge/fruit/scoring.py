from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.services.food.knowledge.common import (
    apply_score_boost,
    clamp_score,
    first_numeric_score,
    normalize_range_score,
    safe_float,
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


DEFAULT_FRUIT_SCORE_WEIGHTS = {
    "quality": 0.30,
    "price": 0.20,
    "trust": 0.20,
    "sweetness": 0.20,
    "information": 0.10,
}


def calculate_fruit_scores(
    product: Mapping[str, Any],
    attributes: Mapping[str, Any],
    context: FoodKnowledgeContext | None = None,
) -> dict[str, float]:
    """
    과일 상품의 세부 점수를 계산한다.
    """

    scores = {
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
        "sweetness": calculate_sweetness_score(
            attributes.get("brix")
        ),
        "information": calculate_information_score(
            attributes
        ),
    }

    return apply_context_score_adjustments(
        scores,
        context=context,
    )


def calculate_fruit_final_score(
    scores: Mapping[str, float],
    context: FoodKnowledgeContext | None = None,
) -> float:
    weights = _resolve_score_weights(
        context
    )

    return weighted_average(
        scores,
        weights,
    )


def calculate_sweetness_score(
    brix: Any,
) -> float:
    """
    과일 공통 초기 점수 모델.

    8 Brix 이하: 0점
    16 Brix 이상: 100점
    """

    return normalize_range_score(
        brix,
        minimum_value=8.0,
        maximum_value=16.0,
    )


def calculate_information_score(
    attributes: Mapping[str, Any],
) -> float:
    field_names = (
        "product_name",
        "origin",
        "variety",
        "grade",
        "brix",
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


def apply_context_score_adjustments(
    scores: Mapping[str, float],
    *,
    context: FoodKnowledgeContext | None,
) -> dict[str, float]:
    adjusted = {
        key: clamp_score(value)
        for key, value in scores.items()
    }

    priority = _normalize_priority(
        context
    )

    if priority in {
        "quality",
        "quality_adaptive",
    }:
        adjusted["quality"] = apply_score_boost(
            adjusted.get("quality", 0.0),
            3.0,
        )

    elif priority in {
        "price",
        "value",
        "price_adaptive",
        "value_adaptive",
    }:
        adjusted["price"] = apply_score_boost(
            adjusted.get("price", 0.0),
            3.0,
        )

    elif priority in {
        "trust",
        "trust_adaptive",
    }:
        adjusted["trust"] = apply_score_boost(
            adjusted.get("trust", 0.0),
            3.0,
        )

    return adjusted


def _resolve_score_weights(
    context: FoodKnowledgeContext | None,
) -> dict[str, float]:
    priority = _normalize_priority(
        context
    )

    if priority in {
        "quality",
        "quality_adaptive",
    }:
        return {
            "quality": 0.40,
            "price": 0.10,
            "trust": 0.20,
            "sweetness": 0.20,
            "information": 0.10,
        }

    if priority in {
        "price",
        "value",
        "price_adaptive",
        "value_adaptive",
    }:
        return {
            "quality": 0.20,
            "price": 0.40,
            "trust": 0.15,
            "sweetness": 0.15,
            "information": 0.10,
        }

    if priority in {
        "trust",
        "trust_adaptive",
    }:
        return {
            "quality": 0.20,
            "price": 0.15,
            "trust": 0.40,
            "sweetness": 0.15,
            "information": 0.10,
        }

    return dict(
        DEFAULT_FRUIT_SCORE_WEIGHTS
    )


def _normalize_priority(
    context: FoodKnowledgeContext | None,
) -> str:
    if context is None:
        return ""

    priority = getattr(
        context,
        "priority",
        None,
    )

    if not priority:
        return ""

    return str(priority).strip().lower()


def _is_available(
    value: Any,
) -> bool:
    if value is None:
        return False

    if isinstance(value, str):
        return bool(value.strip())

    return True


__all__ = [
    "DEFAULT_FRUIT_SCORE_WEIGHTS",
    "calculate_fruit_scores",
    "calculate_fruit_final_score",
    "calculate_sweetness_score",
    "calculate_information_score",
    "apply_context_score_adjustments",
    "clamp_score",
    "safe_float",
]
