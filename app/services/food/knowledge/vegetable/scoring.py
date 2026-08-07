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


DEFAULT_VEGETABLE_SCORE_WEIGHTS = {
    "quality": 0.35,
    "price": 0.20,
    "trust": 0.20,
    "information": 0.25,
}


def calculate_vegetable_scores(
    product: Mapping[str, Any],
    attributes: Mapping[str, Any],
    context: FoodKnowledgeContext | None = None,
) -> dict[str, float]:
    """
    Vegetable 도메인의 세부 점수를 계산한다.

    책임:
    - 외부에서 제공된 quality/price/trust 점수 정규 사용
    - Vegetable 정보 완전성 점수 계산

    수행하지 않는 책임:
    - 상품명 재파싱
    - Registry 변경
    - 추천 또는 개인화 판단
    - 외부 API 호출

    context는 공통 호출 계약 호환성을 위해 수용하지만,
    Sprint 3 Vegetable 도메인 점수에는 사용하지 않는다.
    """
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
            calculate_vegetable_information_score(
                attributes
            )
        ),
    }


def calculate_vegetable_final_score(
    scores: Mapping[str, float],
    context: FoodKnowledgeContext | None = None,
) -> float:
    """
    Vegetable 도메인 점수의 결정론적 가중 평균.

    Recommendation Engine의 추천 점수와 별개이다.
    """
    if not isinstance(scores, Mapping):
        raise TypeError(
            "scores must be a Mapping"
        )

    _ = context

    return weighted_average(
        scores,
        DEFAULT_VEGETABLE_SCORE_WEIGHTS,
    )


def calculate_vegetable_information_score(
    attributes: Mapping[str, Any],
) -> float:
    """
    Vegetable 분석 정보 완전성을 0~100으로 환산한다.
    """
    if not isinstance(attributes, Mapping):
        raise TypeError(
            "attributes must be a Mapping"
        )

    field_names = (
        "product_name",
        "origin",
        "variety",
        "grade",
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
    "DEFAULT_VEGETABLE_SCORE_WEIGHTS",
    "calculate_vegetable_scores",
    "calculate_vegetable_final_score",
    "calculate_vegetable_information_score",
]
