from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.services.food.knowledge.tea.parser_models import (
    TeaParseResult,
)


TEA_KNOWLEDGE_WEIGHTS: dict[str, float] = {
    "tea_type": 1.0 / 6.0,
    "origin": 1.0 / 6.0,
    "variety": 1.0 / 6.0,
    "processing": 1.0 / 6.0,
    "oxidation": 1.0 / 6.0,
    "flavor": 1.0 / 6.0,
}

TEA_FINAL_SCORE_WEIGHTS: dict[str, float] = {
    "quality": 0.20,
    "price": 0.15,
    "trust": 0.15,
    "knowledge": 0.50,
}


def safe_float(
    value: Any,
    default: float = 0.0,
) -> float:
    """숫자로 변환할 수 없는 값은 default로 반환한다."""
    if value is None:
        return float(default)

    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def clamp_score(
    value: Any,
) -> float:
    """점수를 0.0~100.0 범위로 제한한다."""
    return max(
        0.0,
        min(
            100.0,
            safe_float(value),
        ),
    )


def calculate_available_average(
    *values: Any,
) -> float:
    """0보다 큰 유효 점수만 이용해 평균을 계산한다."""
    available = [
        clamp_score(value)
        for value in values
        if clamp_score(value) > 0.0
    ]

    if not available:
        return 0.0

    return round(
        sum(available) / len(available),
        2,
    )


def calculate_available_weighted_score(
    *,
    scores: Mapping[str, Any],
    weights: Mapping[str, Any],
) -> float:
    """
    존재하는 양수 점수의 가중치만 재정규화하여 계산한다.

    누락되거나 아직 점수가 지정되지 않은 Registry 때문에
    확인된 점수가 부당하게 낮아지지 않도록 한다.
    """
    if not isinstance(
        scores,
        Mapping,
    ):
        raise TypeError(
            "scores must be a Mapping"
        )

    if not isinstance(
        weights,
        Mapping,
    ):
        raise TypeError(
            "weights must be a Mapping"
        )

    weighted_sum = 0.0
    available_weight = 0.0

    for key, raw_weight in weights.items():
        score = clamp_score(
            scores.get(key)
        )
        weight = max(
            0.0,
            safe_float(raw_weight),
        )

        if score <= 0.0 or weight <= 0.0:
            continue

        weighted_sum += score * weight
        available_weight += weight

    if available_weight <= 0.0:
        return 0.0

    return round(
        weighted_sum / available_weight,
        2,
    )


def extract_registry_scores(
    parse_result: TeaParseResult,
) -> dict[str, float]:
    """
    TeaParseResult에 보존된 Registry Entry 점수를 추출한다.

    상품명 재파싱이나 Registry 재조회는 수행하지 않는다.
    """
    if not isinstance(
        parse_result,
        TeaParseResult,
    ):
        raise TypeError(
            "parse_result must be TeaParseResult"
        )

    scores: dict[str, float] = {
        "tea_type": 0.0,
        "origin": 0.0,
        "variety": 0.0,
        "processing": 0.0,
        "oxidation": 0.0,
        "flavor": 0.0,
    }

    if parse_result.tea_type_match is not None:
        scores["tea_type"] = clamp_score(
            parse_result
            .tea_type_match
            .entry
            .score
        )

    if parse_result.origin_match is not None:
        scores["origin"] = clamp_score(
            parse_result
            .origin_match
            .entry
            .score
        )

    if parse_result.variety_match is not None:
        scores["variety"] = clamp_score(
            parse_result
            .variety_match
            .entry
            .score
        )

    if parse_result.processing_match is not None:
        scores["processing"] = clamp_score(
            parse_result
            .processing_match
            .entry
            .score
        )

    if parse_result.oxidation_match is not None:
        scores["oxidation"] = clamp_score(
            parse_result
            .oxidation_match
            .entry
            .score
        )

    if parse_result.flavor_match is not None:
        scores["flavor"] = clamp_score(
            parse_result
            .flavor_match
            .entry
            .score
        )

    return scores


def calculate_tea_knowledge_score(
    *,
    tea_type_score: Any = 0.0,
    origin_score: Any = 0.0,
    variety_score: Any = 0.0,
    processing_score: Any = 0.0,
    oxidation_score: Any = 0.0,
    flavor_score: Any = 0.0,
    weights: Mapping[str, Any] | None = None,
) -> float:
    """Tea Registry 핵심 6개 점수로 Knowledge Score를 계산한다."""
    effective_weights = (
        dict(weights)
        if weights is not None
        else dict(
            TEA_KNOWLEDGE_WEIGHTS
        )
    )

    return calculate_available_weighted_score(
        scores={
            "tea_type": tea_type_score,
            "origin": origin_score,
            "variety": variety_score,
            "processing": processing_score,
            "oxidation": oxidation_score,
            "flavor": flavor_score,
        },
        weights=effective_weights,
    )


def calculate_tea_scores(
    *,
    product: Mapping[str, Any],
    parse_result: TeaParseResult,
) -> dict[str, float]:
    """
    외부 상품 점수와 Tea Registry 점수를 결합한다.

    이 함수는 final score를 계산하지 않는다.
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
        TeaParseResult,
    ):
        raise TypeError(
            "parse_result must be TeaParseResult"
        )

    registry_scores = extract_registry_scores(
        parse_result
    )

    knowledge_score = (
        calculate_tea_knowledge_score(
            tea_type_score=(
                registry_scores["tea_type"]
            ),
            origin_score=(
                registry_scores["origin"]
            ),
            variety_score=(
                registry_scores["variety"]
            ),
            processing_score=(
                registry_scores["processing"]
            ),
            oxidation_score=(
                registry_scores["oxidation"]
            ),
            flavor_score=(
                registry_scores["flavor"]
            ),
        )
    )

    return {
        "quality": clamp_score(
            product.get("quality_score")
        ),
        "price": clamp_score(
            product.get("price_score")
        ),
        "trust": clamp_score(
            product.get("trust_score")
        ),
        "knowledge": knowledge_score,
        **registry_scores,
    }


def calculate_tea_final_score(
    scores: Mapping[str, Any],
    *,
    weights: Mapping[str, Any] | None = None,
) -> float:
    """
    외부 평가 점수와 Tea Knowledge Score를 합산한다.

    Coffee와 Cheese의 Sprint 3 계약과 동일하게
    누락 점수를 재정규화하지 않고 전체 가중치를 적용한다.
    """
    if not isinstance(
        scores,
        Mapping,
    ):
        raise TypeError(
            "scores must be a Mapping"
        )

    effective_weights = (
        dict(weights)
        if weights is not None
        else dict(
            TEA_FINAL_SCORE_WEIGHTS
        )
    )

    total = 0.0

    for key, raw_weight in (
        effective_weights.items()
    ):
        score = clamp_score(
            scores.get(key)
        )
        weight = max(
            0.0,
            safe_float(raw_weight),
        )

        total += score * weight

    return round(
        clamp_score(total),
        2,
    )


__all__ = [
    "TEA_FINAL_SCORE_WEIGHTS",
    "TEA_KNOWLEDGE_WEIGHTS",
    "calculate_available_average",
    "calculate_available_weighted_score",
    "calculate_tea_final_score",
    "calculate_tea_knowledge_score",
    "calculate_tea_scores",
    "clamp_score",
    "extract_registry_scores",
    "safe_float",
]
