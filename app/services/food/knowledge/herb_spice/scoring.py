from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.services.food.knowledge.herb_spice.parser_models import (
    HerbSpiceParseResult,
)


HERB_SPICE_KNOWLEDGE_WEIGHTS: dict[str, float] = {
    "ingredient": 0.40,
    "origin": 0.20,
    "form": 0.20,
    "usage": 0.20,
}

HERB_SPICE_FINAL_SCORE_WEIGHTS: dict[str, float] = {
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
    """0보다 큰 유효 점수만 사용해 평균을 계산한다."""
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

    아직 Registry 점수가 지정되지 않은 분석 축은
    Knowledge Score를 부당하게 낮추지 않도록 제외한다.
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
    parse_result: HerbSpiceParseResult,
) -> dict[str, float]:
    """
    ParseResult에 보존된 Registry Entry 점수를 추출한다.

    상품명 재파싱이나 Registry 재조회는 수행하지 않는다.
    """
    if not isinstance(
        parse_result,
        HerbSpiceParseResult,
    ):
        raise TypeError(
            "parse_result must be "
            "HerbSpiceParseResult"
        )

    scores: dict[str, float] = {
        "ingredient": 0.0,
        "origin": 0.0,
        "form": 0.0,
        "usage": 0.0,
    }

    selected_ingredient_match: Any = None

    if parse_result.classification == "herb":
        selected_ingredient_match = (
            parse_result.herb_match
        )
    elif parse_result.classification == "spice":
        selected_ingredient_match = (
            parse_result.spice_match
        )

    if selected_ingredient_match is not None:
        scores["ingredient"] = clamp_score(
            selected_ingredient_match
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

    if parse_result.form_match is not None:
        scores["form"] = clamp_score(
            parse_result
            .form_match
            .entry
            .score
        )

    if parse_result.usage_match is not None:
        scores["usage"] = clamp_score(
            parse_result
            .usage_match
            .entry
            .score
        )

    return scores


def calculate_herb_spice_knowledge_score(
    *,
    ingredient_score: Any = 0.0,
    origin_score: Any = 0.0,
    form_score: Any = 0.0,
    usage_score: Any = 0.0,
    weights: Mapping[str, Any] | None = None,
) -> float:
    """
    Herb & Spice 핵심 Registry 점수로
    Knowledge Score를 계산한다.
    """
    effective_weights = (
        dict(weights)
        if weights is not None
        else dict(
            HERB_SPICE_KNOWLEDGE_WEIGHTS
        )
    )

    return calculate_available_weighted_score(
        scores={
            "ingredient": ingredient_score,
            "origin": origin_score,
            "form": form_score,
            "usage": usage_score,
        },
        weights=effective_weights,
    )


def calculate_herb_spice_scores(
    *,
    product: Mapping[str, Any],
    parse_result: HerbSpiceParseResult,
) -> dict[str, float]:
    """
    외부 상품 점수와 Herb & Spice Registry 점수를 결합한다.

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
        HerbSpiceParseResult,
    ):
        raise TypeError(
            "parse_result must be "
            "HerbSpiceParseResult"
        )

    registry_scores = extract_registry_scores(
        parse_result
    )

    knowledge_score = (
        calculate_herb_spice_knowledge_score(
            ingredient_score=(
                registry_scores["ingredient"]
            ),
            origin_score=(
                registry_scores["origin"]
            ),
            form_score=(
                registry_scores["form"]
            ),
            usage_score=(
                registry_scores["usage"]
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


def calculate_herb_spice_final_score(
    scores: Mapping[str, Any],
    *,
    weights: Mapping[str, Any] | None = None,
) -> float:
    """
    외부 상품 점수와 Knowledge Score를 합산한다.

    Sprint 3 Tea 계약과 동일하게 누락 점수를
    재정규화하지 않고 전체 가중치를 적용한다.
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
            HERB_SPICE_FINAL_SCORE_WEIGHTS
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
    "HERB_SPICE_FINAL_SCORE_WEIGHTS",
    "HERB_SPICE_KNOWLEDGE_WEIGHTS",
    "calculate_available_average",
    "calculate_available_weighted_score",
    "calculate_herb_spice_final_score",
    "calculate_herb_spice_knowledge_score",
    "calculate_herb_spice_scores",
    "clamp_score",
    "extract_registry_scores",
    "safe_float",
]
