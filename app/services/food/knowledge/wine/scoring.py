from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.services.food.knowledge.wine.parser_models import (
    WineParseResult,
)


WINE_KNOWLEDGE_WEIGHTS: dict[str, float] = {
    "wine_type": 0.15,
    "grape": 0.20,
    "region": 0.25,
    "sweetness": 0.10,
    "body": 0.15,
    "acidity": 0.15,
}

WINE_FINAL_SCORE_WEIGHTS: dict[str, float] = {
    "quality": 0.25,
    "price": 0.10,
    "trust": 0.20,
    "knowledge": 0.45,
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
    0보다 큰 유효 점수만으로 평균을 계산한다.
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
    존재하는 양수 점수의 가중치만 다시 정규화해 계산한다.
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
    parse_result: WineParseResult,
) -> dict[str, float]:
    """
    WineParseResult에 보존된 Registry Entry 점수를 추출한다.

    상품명 재파싱이나 Registry 재조회는 수행하지 않는다.
    """
    if not isinstance(
        parse_result,
        WineParseResult,
    ):
        raise TypeError(
            "parse_result must be WineParseResult"
        )

    scores: dict[str, float] = {
        "wine_type": 0.0,
        "grape": 0.0,
        "region": 0.0,
        "sweetness": 0.0,
        "body": 0.0,
        "acidity": 0.0,
    }

    if parse_result.wine_type_match is not None:
        scores["wine_type"] = clamp_score(
            parse_result
            .wine_type_match
            .entry
            .score
        )

    if parse_result.grape_match is not None:
        scores["grape"] = clamp_score(
            parse_result
            .grape_match
            .entry
            .score
        )

    if parse_result.region_match is not None:
        scores["region"] = clamp_score(
            parse_result
            .region_match
            .entry
            .score
        )

    if parse_result.sweetness_match is not None:
        scores["sweetness"] = clamp_score(
            parse_result
            .sweetness_match
            .entry
            .score
        )

    if parse_result.body_match is not None:
        scores["body"] = clamp_score(
            parse_result
            .body_match
            .entry
            .score
        )

    if parse_result.acidity_match is not None:
        scores["acidity"] = clamp_score(
            parse_result
            .acidity_match
            .entry
            .score
        )

    return scores


def calculate_wine_knowledge_score(
    *,
    wine_type_score: Any = 0.0,
    grape_score: Any = 0.0,
    region_score: Any = 0.0,
    sweetness_score: Any = 0.0,
    body_score: Any = 0.0,
    acidity_score: Any = 0.0,
    weights: Mapping[str, Any] | None = None,
) -> float:
    """
    Wine Registry 핵심 점수로 Knowledge Score를 계산한다.
    """
    effective_weights = (
        dict(weights)
        if weights is not None
        else dict(WINE_KNOWLEDGE_WEIGHTS)
    )

    return calculate_available_weighted_score(
        scores={
            "wine_type": wine_type_score,
            "grape": grape_score,
            "region": region_score,
            "sweetness": sweetness_score,
            "body": body_score,
            "acidity": acidity_score,
        },
        weights=effective_weights,
    )


def calculate_wine_quality_score(
    *,
    registry_scores: Mapping[str, Any],
    parse_result: WineParseResult,
) -> float:
    """
    Registry 품질 점수와 빈티지·도수 정보 완전성을 반영한다.
    """
    if not isinstance(
        registry_scores,
        Mapping,
    ):
        raise TypeError(
            "registry_scores must be a Mapping"
        )

    if not isinstance(
        parse_result,
        WineParseResult,
    ):
        raise TypeError(
            "parse_result must be WineParseResult"
        )

    base_score = calculate_available_average(
        registry_scores.get("grape"),
        registry_scores.get("region"),
        registry_scores.get("wine_type"),
        registry_scores.get("body"),
        registry_scores.get("acidity"),
    )

    completeness_bonus = 0.0

    if parse_result.vintage is not None:
        completeness_bonus += 2.0

    if parse_result.alcohol_percent is not None:
        completeness_bonus += 2.0

    if parse_result.is_complete:
        completeness_bonus += 3.0

    return clamp_score(
        base_score + completeness_bonus
    )


def calculate_wine_trust_score(
    *,
    product: Mapping[str, Any],
    parse_result: WineParseResult,
) -> float:
    """
    구조화 정보와 Parser 신뢰도를 기반으로 Trust Score를 계산한다.
    """
    if not isinstance(product, Mapping):
        raise TypeError(
            "product must be a Mapping"
        )

    if not isinstance(
        parse_result,
        WineParseResult,
    ):
        raise TypeError(
            "parse_result must be WineParseResult"
        )

    score = (
        clamp_score(
            parse_result.confidence * 100.0
        )
        * 0.60
    )

    evidence_fields = (
        "producer",
        "winery",
        "country",
        "country_code",
        "origin_country",
        "certifications",
        "certification",
        "vintage",
        "alcohol_percent",
        "volume",
        "volume_ml",
    )

    evidence_count = sum(
        1
        for field_name in evidence_fields
        if (
            field_name in product
            and product[field_name] is not None
            and str(product[field_name]).strip()
        )
    )

    score += min(
        40.0,
        evidence_count * 5.0,
    )

    return round(
        clamp_score(score),
        2,
    )


def calculate_wine_price_score(
    product: Mapping[str, Any],
) -> float:
    """
    공통 입력 가격 점수가 있으면 사용한다.

    가격 정보가 없으면 Wine Scoring 계층이 임의의 가격 평가를
    생성하지 않고 0.0을 반환한다.
    """
    if not isinstance(product, Mapping):
        raise TypeError(
            "product must be a Mapping"
        )

    for field_name in (
        "price_score",
        "value_score",
        "market_price_score",
    ):
        if field_name not in product:
            continue

        return round(
            clamp_score(
                product[field_name]
            ),
            2,
        )

    return 0.0


def calculate_wine_scores(
    *,
    product: Mapping[str, Any],
    parse_result: WineParseResult,
) -> dict[str, float]:
    """
    Wine 도메인의 표준 점수 집합을 계산한다.
    """
    if not isinstance(product, Mapping):
        raise TypeError(
            "product must be a Mapping"
        )

    if not isinstance(
        parse_result,
        WineParseResult,
    ):
        raise TypeError(
            "parse_result must be WineParseResult"
        )

    registry_scores = extract_registry_scores(
        parse_result
    )

    knowledge_score = (
        calculate_wine_knowledge_score(
            wine_type_score=(
                registry_scores["wine_type"]
            ),
            grape_score=(
                registry_scores["grape"]
            ),
            region_score=(
                registry_scores["region"]
            ),
            sweetness_score=(
                registry_scores["sweetness"]
            ),
            body_score=(
                registry_scores["body"]
            ),
            acidity_score=(
                registry_scores["acidity"]
            ),
        )
    )

    quality_score = calculate_wine_quality_score(
        registry_scores=registry_scores,
        parse_result=parse_result,
    )

    trust_score = calculate_wine_trust_score(
        product=product,
        parse_result=parse_result,
    )

    price_score = calculate_wine_price_score(
        product
    )

    return {
        "quality": round(
            quality_score,
            2,
        ),
        "price": round(
            price_score,
            2,
        ),
        "trust": round(
            trust_score,
            2,
        ),
        "knowledge": round(
            knowledge_score,
            2,
        ),
        "wine_type": registry_scores[
            "wine_type"
        ],
        "grape": registry_scores[
            "grape"
        ],
        "region": registry_scores[
            "region"
        ],
        "sweetness": registry_scores[
            "sweetness"
        ],
        "body": registry_scores[
            "body"
        ],
        "acidity": registry_scores[
            "acidity"
        ],
    }


def calculate_wine_final_score(
    scores: Mapping[str, Any],
    *,
    weights: Mapping[str, Any] | None = None,
) -> float:
    """
    Wine 최종 점수를 계산한다.
    """
    effective_weights = (
        dict(weights)
        if weights is not None
        else dict(WINE_FINAL_SCORE_WEIGHTS)
    )

    return calculate_available_weighted_score(
        scores=scores,
        weights=effective_weights,
    )


__all__ = [
    "WINE_FINAL_SCORE_WEIGHTS",
    "WINE_KNOWLEDGE_WEIGHTS",
    "calculate_available_average",
    "calculate_available_weighted_score",
    "calculate_wine_final_score",
    "calculate_wine_knowledge_score",
    "calculate_wine_price_score",
    "calculate_wine_quality_score",
    "calculate_wine_scores",
    "calculate_wine_trust_score",
    "clamp_score",
    "extract_registry_scores",
    "safe_float",
]
