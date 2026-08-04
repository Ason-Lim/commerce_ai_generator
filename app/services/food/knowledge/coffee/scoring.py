from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.services.food.knowledge.coffee.parser_models import (
    CoffeeParseResult,
)


COFFEE_KNOWLEDGE_WEIGHTS: dict[str, float] = {
    "bean": 0.30,
    "origin": 0.25,
    "roast": 0.20,
    "process": 0.25,
}

COFFEE_FINAL_SCORE_WEIGHTS: dict[str, float] = {
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
    0보다 큰 유효 점수만 이용해 평균을 계산한다.
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
    존재하는 양수 점수의 가중치만 재정규화하여 계산한다.

    누락된 Coffee Registry 필드가 확인된 점수를
    불필요하게 낮추지 않도록 한다.
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
    parse_result: CoffeeParseResult,
) -> dict[str, float]:
    """
    CoffeeParseResult에 보존된 Registry Entry 점수를 추출한다.

    상품명 재파싱이나 Registry 재조회는 수행하지 않는다.
    """
    if not isinstance(
        parse_result,
        CoffeeParseResult,
    ):
        raise TypeError(
            "parse_result must be CoffeeParseResult"
        )

    scores: dict[str, float] = {
        "bean": 0.0,
        "origin": 0.0,
        "roast": 0.0,
        "process": 0.0,
        "acidity": 0.0,
        "body": 0.0,
        "aroma": 0.0,
        "clarity": 0.0,
        "sweetness": 0.0,
    }

    acidity_scores: list[float] = []
    body_scores: list[float] = []
    aroma_scores: list[float] = []

    if parse_result.bean_match is not None:
        entry = (
            parse_result
            .bean_match
            .entry
        )

        scores["bean"] = clamp_score(
            entry.score
        )

        acidity_scores.append(
            clamp_score(
                entry.acidity_score
            )
        )
        body_scores.append(
            clamp_score(
                entry.body_score
            )
        )
        aroma_scores.append(
            clamp_score(
                entry.aroma_score
            )
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

        acidity_scores.append(
            clamp_score(
                entry.acidity_score
            )
        )
        body_scores.append(
            clamp_score(
                entry.body_score
            )
        )
        aroma_scores.append(
            clamp_score(
                entry.aroma_score
            )
        )

    if parse_result.roast_match is not None:
        entry = (
            parse_result
            .roast_match
            .entry
        )

        scores["roast"] = clamp_score(
            entry.score
        )

        acidity_scores.append(
            clamp_score(
                entry.acidity_score
            )
        )
        body_scores.append(
            clamp_score(
                entry.body_score
            )
        )
        aroma_scores.append(
            clamp_score(
                entry.aroma_score
            )
        )

    if parse_result.process_match is not None:
        entry = (
            parse_result
            .process_match
            .entry
        )

        scores["process"] = clamp_score(
            entry.score
        )
        scores["clarity"] = clamp_score(
            entry.clarity_score
        )
        scores["sweetness"] = clamp_score(
            entry.sweetness_score
        )

        body_scores.append(
            clamp_score(
                entry.body_score
            )
        )

    scores["acidity"] = (
        calculate_available_average(
            *acidity_scores
        )
    )
    scores["body"] = (
        calculate_available_average(
            *body_scores
        )
    )
    scores["aroma"] = (
        calculate_available_average(
            *aroma_scores
        )
    )

    return scores


def calculate_coffee_knowledge_score(
    *,
    bean_score: Any = 0.0,
    origin_score: Any = 0.0,
    roast_score: Any = 0.0,
    process_score: Any = 0.0,
    weights: Mapping[str, Any] | None = None,
) -> float:
    """
    Coffee Registry 핵심 4개 점수를 이용해
    Knowledge Score를 계산한다.
    """
    effective_weights = (
        dict(weights)
        if weights is not None
        else dict(
            COFFEE_KNOWLEDGE_WEIGHTS
        )
    )

    return calculate_available_weighted_score(
        scores={
            "bean": bean_score,
            "origin": origin_score,
            "roast": roast_score,
            "process": process_score,
        },
        weights=effective_weights,
    )


def calculate_coffee_scores(
    *,
    product: Mapping[str, Any],
    parse_result: CoffeeParseResult,
) -> dict[str, float]:
    """
    외부 상품 점수와 Coffee Registry 점수를 조합한
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
        CoffeeParseResult,
    ):
        raise TypeError(
            "parse_result must be CoffeeParseResult"
        )

    registry_scores = extract_registry_scores(
        parse_result
    )

    knowledge_score = (
        calculate_coffee_knowledge_score(
            bean_score=(
                registry_scores["bean"]
            ),
            origin_score=(
                registry_scores["origin"]
            ),
            roast_score=(
                registry_scores["roast"]
            ),
            process_score=(
                registry_scores["process"]
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


def calculate_coffee_final_score(
    scores: Mapping[str, Any],
    *,
    weights: Mapping[str, Any] | None = None,
) -> float:
    """
    외부 평가 점수와 Coffee Knowledge Score를 합산한다.

    최종 점수는 누락 점수를 재정규화하지 않고
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
            COFFEE_FINAL_SCORE_WEIGHTS
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
    "COFFEE_KNOWLEDGE_WEIGHTS",
    "COFFEE_FINAL_SCORE_WEIGHTS",
    "safe_float",
    "clamp_score",
    "calculate_available_average",
    "calculate_available_weighted_score",
    "extract_registry_scores",
    "calculate_coffee_knowledge_score",
    "calculate_coffee_scores",
    "calculate_coffee_final_score",
]
