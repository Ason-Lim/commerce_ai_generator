from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.services.food.knowledge.cheese.parser_models import (
    CheeseParseResult,
)


CHEESE_KNOWLEDGE_WEIGHTS: dict[str, float] = {
    "cheese_type": 0.30,
    "milk_source": 0.15,
    "origin": 0.20,
    "texture": 0.15,
    "aging": 0.20,
}

CHEESE_FINAL_SCORE_WEIGHTS: dict[str, float] = {
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
    숫자로 변환할 수 없는 값은 default로 반환한다.
    """
    if value is None:
        return float(default)

    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def clamp_score(
    value: Any,
) -> float:
    """
    점수를 0.0~100.0 범위로 제한한다.
    """
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
    """
    0보다 큰 유효 점수만으로 단순 평균을 계산한다.
    """
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
    존재하는 양수 점수의 가중치만 다시 정규화하여 계산한다.

    누락된 Registry 정보 때문에 확인된 점수가 부당하게
    낮아지지 않도록 한다.
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
    parse_result: CheeseParseResult,
) -> dict[str, float]:
    """
    CheeseParseResult에 보존된 Registry Entry 점수를 추출한다.

    상품명 재파싱이나 Registry 재조회는 수행하지 않는다.
    """
    if not isinstance(
        parse_result,
        CheeseParseResult,
    ):
        raise TypeError(
            "parse_result must be CheeseParseResult"
        )

    scores: dict[str, float] = {
        "cheese_type": 0.0,
        "milk_source": 0.0,
        "origin": 0.0,
        "texture": 0.0,
        "aging": 0.0,
        "flavor": 0.0,
        "versatility": 0.0,
        "richness": 0.0,
        "availability": 0.0,
        "tradition": 0.0,
        "firmness": 0.0,
        "moisture": 0.0,
    }

    if parse_result.cheese_type_match is not None:
        entry = (
            parse_result
            .cheese_type_match
            .entry
        )

        scores["cheese_type"] = clamp_score(
            entry.score
        )
        scores["flavor"] = clamp_score(
            entry.flavor_score
        )
        scores["versatility"] = clamp_score(
            entry.versatility_score
        )

    if parse_result.milk_source_match is not None:
        entry = (
            parse_result
            .milk_source_match
            .entry
        )

        scores["milk_source"] = clamp_score(
            entry.score
        )
        scores["richness"] = clamp_score(
            entry.richness_score
        )
        scores["availability"] = clamp_score(
            entry.availability_score
        )

    if parse_result.origin_match is not None:
        entry = (
            parse_result
            .origin_match
            .entry
        )

        scores["origin"] = clamp_score(
            entry.score
        )
        scores["tradition"] = clamp_score(
            entry.tradition_score
        )

    if parse_result.texture_match is not None:
        entry = (
            parse_result
            .texture_match
            .entry
        )

        scores["texture"] = clamp_score(
            entry.score
        )
        scores["firmness"] = clamp_score(
            entry.firmness_score
        )
        scores["moisture"] = clamp_score(
            entry.moisture_score
        )

    if parse_result.aging_match is not None:
        entry = (
            parse_result
            .aging_match
            .entry
        )

        scores["aging"] = clamp_score(
            entry.score
        )

    return scores


def calculate_cheese_knowledge_score(
    *,
    cheese_type_score: Any = 0.0,
    milk_source_score: Any = 0.0,
    origin_score: Any = 0.0,
    texture_score: Any = 0.0,
    aging_score: Any = 0.0,
    weights: Mapping[str, Any] | None = None,
) -> float:
    """
    Cheese Registry의 핵심 5개 점수를 이용해
    Knowledge Score를 계산한다.
    """
    effective_weights = (
        dict(weights)
        if weights is not None
        else dict(
            CHEESE_KNOWLEDGE_WEIGHTS
        )
    )

    return calculate_available_weighted_score(
        scores={
            "cheese_type": cheese_type_score,
            "milk_source": milk_source_score,
            "origin": origin_score,
            "texture": texture_score,
            "aging": aging_score,
        },
        weights=effective_weights,
    )


def calculate_cheese_scores(
    *,
    product: Mapping[str, Any],
    parse_result: CheeseParseResult,
) -> dict[str, float]:
    """
    외부 상품 점수와 Cheese Registry 점수를 조합한
    Scoring 결과를 반환한다.

    이 함수는 최종 점수를 계산하지 않는다.
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
        CheeseParseResult,
    ):
        raise TypeError(
            "parse_result must be CheeseParseResult"
        )

    registry_scores = extract_registry_scores(
        parse_result
    )

    knowledge_score = (
        calculate_cheese_knowledge_score(
            cheese_type_score=(
                registry_scores["cheese_type"]
            ),
            milk_source_score=(
                registry_scores["milk_source"]
            ),
            origin_score=(
                registry_scores["origin"]
            ),
            texture_score=(
                registry_scores["texture"]
            ),
            aging_score=(
                registry_scores["aging"]
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


def calculate_cheese_final_score(
    scores: Mapping[str, Any],
    *,
    weights: Mapping[str, Any] | None = None,
) -> float:
    """
    외부 평가 점수와 Cheese Knowledge Score를 합산한다.

    최종 점수는 누락 점수를 재정규화하지 않고,
    정의된 전체 가중치에 따라 계산한다.
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
            CHEESE_FINAL_SCORE_WEIGHTS
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
    "CHEESE_KNOWLEDGE_WEIGHTS",
    "CHEESE_FINAL_SCORE_WEIGHTS",
    "safe_float",
    "clamp_score",
    "calculate_available_average",
    "calculate_available_weighted_score",
    "extract_registry_scores",
    "calculate_cheese_knowledge_score",
    "calculate_cheese_scores",
    "calculate_cheese_final_score",
]
