from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.services.food.knowledge.olive_oil.parser_models import (
    OliveOilParseResult,
)


OLIVE_OIL_KNOWLEDGE_WEIGHTS: dict[str, float] = {
    "olive_oil_type": 0.20,
    "variety": 0.15,
    "origin": 0.20,
    "processing": 0.15,
    "grade": 0.30,
}

OLIVE_OIL_FINAL_SCORE_WEIGHTS: dict[str, float] = {
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
    존재하는 양수 점수의 가중치만 재정규화해 계산한다.

    score가 아직 지정되지 않은 Registry가 확인된 점수를
    불필요하게 낮추지 않도록 한다.
    """
    if not isinstance(scores, Mapping):
        raise TypeError(
            "scores must be a Mapping"
        )

    if not isinstance(weights, Mapping):
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
    parse_result: OliveOilParseResult,
) -> dict[str, float]:
    """
    OliveOilParseResult에 보존된 Registry Entry 점수를 추출한다.

    상품명 재파싱이나 Registry 재조회는 수행하지 않는다.
    """
    if not isinstance(
        parse_result,
        OliveOilParseResult,
    ):
        raise TypeError(
            "parse_result must be OliveOilParseResult"
        )

    scores: dict[str, float] = {
        "olive_oil_type": 0.0,
        "variety": 0.0,
        "origin": 0.0,
        "processing": 0.0,
        "grade": 0.0,
    }

    if (
        parse_result.olive_oil_type_match
        is not None
    ):
        scores["olive_oil_type"] = clamp_score(
            parse_result
            .olive_oil_type_match
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

    if parse_result.origin_match is not None:
        scores["origin"] = clamp_score(
            parse_result
            .origin_match
            .entry
            .score
        )

    if (
        parse_result.processing_match
        is not None
    ):
        scores["processing"] = clamp_score(
            parse_result
            .processing_match
            .entry
            .score
        )

    if parse_result.grade_match is not None:
        scores["grade"] = clamp_score(
            parse_result
            .grade_match
            .entry
            .score
        )

    return scores


def calculate_olive_oil_knowledge_score(
    *,
    olive_oil_type_score: Any = 0.0,
    variety_score: Any = 0.0,
    origin_score: Any = 0.0,
    processing_score: Any = 0.0,
    grade_score: Any = 0.0,
    weights: Mapping[str, Any] | None = None,
) -> float:
    """
    Olive Oil Registry 핵심 5개 점수로
    Knowledge Score를 계산한다.
    """
    effective_weights = (
        dict(weights)
        if weights is not None
        else dict(
            OLIVE_OIL_KNOWLEDGE_WEIGHTS
        )
    )

    return calculate_available_weighted_score(
        scores={
            "olive_oil_type": (
                olive_oil_type_score
            ),
            "variety": variety_score,
            "origin": origin_score,
            "processing": processing_score,
            "grade": grade_score,
        },
        weights=effective_weights,
    )


def calculate_olive_oil_scores(
    *,
    product: Mapping[str, Any],
    parse_result: OliveOilParseResult,
) -> dict[str, float]:
    """
    외부 상품 점수와 Olive Oil Registry 점수를 결합한다.

    이 함수는 final score를 계산하지 않는다.
    """
    if not isinstance(product, Mapping):
        raise TypeError(
            "product must be a Mapping"
        )

    if not isinstance(
        parse_result,
        OliveOilParseResult,
    ):
        raise TypeError(
            "parse_result must be OliveOilParseResult"
        )

    registry_scores = extract_registry_scores(
        parse_result
    )

    knowledge_score = (
        calculate_olive_oil_knowledge_score(
            olive_oil_type_score=(
                registry_scores[
                    "olive_oil_type"
                ]
            ),
            variety_score=(
                registry_scores["variety"]
            ),
            origin_score=(
                registry_scores["origin"]
            ),
            processing_score=(
                registry_scores["processing"]
            ),
            grade_score=(
                registry_scores["grade"]
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


def calculate_olive_oil_final_score(
    scores: Mapping[str, Any],
    *,
    weights: Mapping[str, Any] | None = None,
) -> float:
    """
    외부 평가 점수와 Olive Oil Knowledge Score를 합산한다.

    누락된 final-score 항목은 재정규화하지 않고,
    전체 정의 가중치를 그대로 적용한다.
    """
    if not isinstance(scores, Mapping):
        raise TypeError(
            "scores must be a Mapping"
        )

    effective_weights = (
        dict(weights)
        if weights is not None
        else dict(
            OLIVE_OIL_FINAL_SCORE_WEIGHTS
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
    "OLIVE_OIL_FINAL_SCORE_WEIGHTS",
    "OLIVE_OIL_KNOWLEDGE_WEIGHTS",
    "calculate_available_average",
    "calculate_available_weighted_score",
    "calculate_olive_oil_final_score",
    "calculate_olive_oil_knowledge_score",
    "calculate_olive_oil_scores",
    "clamp_score",
    "extract_registry_scores",
    "safe_float",
]
