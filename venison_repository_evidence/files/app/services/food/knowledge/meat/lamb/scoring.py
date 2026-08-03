from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.services.food.knowledge.meat.lamb.parser_models import (
    LambParseResult,
)
from app.services.food.knowledge.models import (
    FoodKnowledgeContext,
)


DEFAULT_KNOWLEDGE_WEIGHTS: dict[str, float] = {
    "age": 0.35,
    "breed": 0.25,
    "cut": 0.40,
}


DEFAULT_FINAL_SCORE_WEIGHTS: dict[str, float] = {
    "quality": 0.20,
    "price": 0.15,
    "trust": 0.15,
    "knowledge": 0.50,
}


def safe_float(
    value: Any,
    default: float = 0.0,
) -> float:
    """
    값을 안전하게 float로 변환한다.
    """
    if value is None:
        return float(default)

    if isinstance(value, bool):
        return float(value)

    try:
        return float(value)
    except (
        TypeError,
        ValueError,
        OverflowError,
    ):
        return float(default)


def clamp_score(
    value: Any,
    *,
    minimum: float = 0.0,
    maximum: float = 100.0,
) -> float:
    """
    점수를 지정된 범위로 제한한다.
    """
    normalized = safe_float(
        value,
        default=minimum,
    )

    return max(
        minimum,
        min(
            maximum,
            normalized,
        ),
    )


def calculate_available_average(
    *values: Any,
) -> float:
    """
    0보다 큰 유효 점수만 평균에 포함한다.
    """
    normalized_values = [
        clamp_score(value)
        for value in values
        if clamp_score(value) > 0.0
    ]

    if not normalized_values:
        return 0.0

    return round(
        sum(normalized_values)
        / len(normalized_values),
        2,
    )


def extract_registry_scores(
    parse_result: LambParseResult,
) -> dict[str, float]:
    """
    LambParseResult의 Registry Match에서 점수를 추출한다.

    Parser가 인식하지 못한 항목은 0점으로 반환한다.
    """
    if not isinstance(
        parse_result,
        LambParseResult,
    ):
        raise TypeError(
            "parse_result must be LambParseResult"
        )

    age_score = 0.0
    breed_score = 0.0
    cut_score = 0.0

    breed_tenderness_score = 0.0
    cut_tenderness_score = 0.0

    breed_flavor_score = 0.0
    cut_flavor_score = 0.0

    if parse_result.age_match is not None:
        age_score = clamp_score(
            parse_result.age_match.age.score
        )

    if parse_result.breed_match is not None:
        breed = parse_result.breed_match.breed

        breed_score = clamp_score(
            breed.score
        )
        breed_tenderness_score = clamp_score(
            breed.tenderness_score
        )
        breed_flavor_score = clamp_score(
            breed.flavor_score
        )

    if parse_result.cut_match is not None:
        cut = parse_result.cut_match.cut

        cut_score = clamp_score(
            cut.score
        )
        cut_tenderness_score = clamp_score(
            cut.tenderness_score
        )
        cut_flavor_score = clamp_score(
            cut.flavor_score
        )

    tenderness_score = (
        calculate_available_average(
            breed_tenderness_score,
            cut_tenderness_score,
        )
    )

    flavor_score = (
        calculate_available_average(
            breed_flavor_score,
            cut_flavor_score,
        )
    )

    return {
        "age": round(age_score, 2),
        "breed": round(breed_score, 2),
        "cut": round(cut_score, 2),
        "tenderness": tenderness_score,
        "flavor": flavor_score,
    }


def calculate_lamb_knowledge_score(
    *,
    age_score: Any,
    breed_score: Any,
    cut_score: Any,
    weights: Mapping[str, float] | None = None,
) -> float:
    """
    Lamb Registry 점수를 가중 평균한다.

    인식된 항목만 분모에 포함한다.

    예:
    - 연령과 부위만 인식되면 두 항목의 가중치만 사용
    - 아무 항목도 인식되지 않으면 0점
    """
    score_weights = dict(
        weights
        or DEFAULT_KNOWLEDGE_WEIGHTS
    )

    registry_scores = {
        "age": clamp_score(
            age_score
        ),
        "breed": clamp_score(
            breed_score
        ),
        "cut": clamp_score(
            cut_score
        ),
    }

    weighted_sum = 0.0
    total_weight = 0.0

    for key, score in registry_scores.items():
        if score <= 0.0:
            continue

        weight = max(
            0.0,
            safe_float(
                score_weights.get(key)
            ),
        )

        if weight <= 0.0:
            continue

        weighted_sum += score * weight
        total_weight += weight

    if total_weight <= 0.0:
        return 0.0

    return round(
        clamp_score(
            weighted_sum / total_weight
        ),
        2,
    )


def calculate_lamb_scores(
    *,
    product: Mapping[str, Any],
    parse_result: LambParseResult,
    context: FoodKnowledgeContext | None = None,
) -> dict[str, float]:
    """
    외부 상품 점수와 Lamb Registry 점수를 구성한다.

    현재 context는 Provider 인터페이스 호환성을 위해
    전달받으며, priority별 가중치는 아직 적용하지 않는다.
    """
    if not isinstance(
        product,
        Mapping,
    ):
        raise TypeError(
            "product must be a Mapping"
        )

    if not isinstance(
        parse_result,
        LambParseResult,
    ):
        raise TypeError(
            "parse_result must be LambParseResult"
        )

    del context

    registry_scores = extract_registry_scores(
        parse_result
    )

    knowledge_score = (
        calculate_lamb_knowledge_score(
            age_score=registry_scores["age"],
            breed_score=registry_scores[
                "breed"
            ],
            cut_score=registry_scores["cut"],
        )
    )

    return {
        "quality": round(
            clamp_score(
                product.get("quality_score")
            ),
            2,
        ),
        "price": round(
            clamp_score(
                product.get("price_score")
            ),
            2,
        ),
        "trust": round(
            clamp_score(
                product.get("trust_score")
            ),
            2,
        ),
        "age": registry_scores["age"],
        "breed": registry_scores["breed"],
        "cut": registry_scores["cut"],
        "tenderness": registry_scores[
            "tenderness"
        ],
        "flavor": registry_scores["flavor"],
        "knowledge": knowledge_score,
    }


def calculate_lamb_final_score(
    scores: Mapping[str, Any],
    *,
    weights: Mapping[str, float] | None = None,
) -> float:
    """
    외부 상품 점수와 Lamb Knowledge 점수로
    최종 점수를 계산한다.
    """
    if not isinstance(
        scores,
        Mapping,
    ):
        raise TypeError(
            "scores must be a Mapping"
        )

    score_weights = dict(
        weights
        or DEFAULT_FINAL_SCORE_WEIGHTS
    )

    weighted_sum = 0.0

    for key, weight in score_weights.items():
        normalized_weight = max(
            0.0,
            safe_float(weight),
        )

        if normalized_weight <= 0.0:
            continue

        weighted_sum += (
            clamp_score(
                scores.get(key)
            )
            * normalized_weight
        )

    return round(
        clamp_score(weighted_sum),
        2,
    )


__all__ = [
    "DEFAULT_KNOWLEDGE_WEIGHTS",
    "DEFAULT_FINAL_SCORE_WEIGHTS",
    "safe_float",
    "clamp_score",
    "calculate_available_average",
    "extract_registry_scores",
    "calculate_lamb_knowledge_score",
    "calculate_lamb_scores",
    "calculate_lamb_final_score",
]
