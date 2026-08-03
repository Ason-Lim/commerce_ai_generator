from __future__ import annotations

from typing import Any, Mapping

from app.services.food.knowledge.meat.beef.parser_models import (
    BeefParseResult,
)
from app.services.food.knowledge.models import (
    FoodKnowledgeContext,
)


DEFAULT_FINAL_SCORE_WEIGHTS: dict[str, float] = {
    "quality": 0.25,
    "price": 0.20,
    "trust": 0.20,
    "knowledge": 0.35,
}

DEFAULT_KNOWLEDGE_WEIGHTS: dict[str, float] = {
    "breed": 0.25,
    "grade": 0.45,
    "cut": 0.30,
}


def safe_float(
    value: Any,
    default: float = 0.0,
) -> float:
    """
    값을 안전하게 float로 변환한다.
    """
    try:
        if value is None or value == "":
            return default

        return float(value)

    except (TypeError, ValueError):
        return default


def clamp_score(
    value: Any,
    *,
    minimum: float = 0.0,
    maximum: float = 100.0,
) -> float:
    """
    점수를 지정된 범위 안으로 제한한다.
    """
    numeric_value = safe_float(value)

    return max(
        minimum,
        min(
            maximum,
            numeric_value,
        ),
    )


def extract_registry_scores(
    parse_result: BeefParseResult,
) -> dict[str, float]:
    """
    BeefParseResult에서 Registry 기반 점수를 추출한다.

    Returns:
        breed:
            품종 Registry 점수
        grade:
            등급 Registry 점수
        cut:
            부위 Registry 점수
        tenderness:
            부위 연도 점수
    """
    breed_score = 0.0
    grade_score = 0.0
    cut_score = 0.0
    tenderness_score = 0.0

    if parse_result.breed_match is not None:
        breed_score = safe_float(
            parse_result.breed_match.breed.score
        )

    if parse_result.grade_match is not None:
        grade_score = safe_float(
            parse_result.grade_match.grade.score
        )

    if parse_result.cut_match is not None:
        cut_entry = parse_result.cut_match.cut

        cut_score = safe_float(
            cut_entry.score
        )

        tenderness_score = safe_float(
            cut_entry.tenderness_score
        )

    return {
        "breed": round(
            clamp_score(breed_score),
            2,
        ),
        "grade": round(
            clamp_score(grade_score),
            2,
        ),
        "cut": round(
            clamp_score(cut_score),
            2,
        ),
        "tenderness": round(
            clamp_score(tenderness_score),
            2,
        ),
    }


def calculate_beef_knowledge_score(
    *,
    breed_score: float,
    grade_score: float,
    cut_score: float,
    weights: Mapping[str, float] | None = None,
) -> float:
    """
    품종·등급·부위 Registry 점수로 쇠고기 지식 점수를 계산한다.

    인식된 항목만 분모에 포함한다.

    예:
    - 등급과 부위만 인식되면 두 항목의 가중치만 사용
    - 모든 항목이 없으면 0점
    """
    score_weights = dict(
        weights
        or DEFAULT_KNOWLEDGE_WEIGHTS
    )

    registry_scores = {
        "breed": clamp_score(
            breed_score
        ),
        "grade": clamp_score(
            grade_score
        ),
        "cut": clamp_score(
            cut_score
        ),
    }

    weighted_sum = 0.0
    total_weight = 0.0

    for key, score in registry_scores.items():
        if score <= 0:
            continue

        weight = max(
            0.0,
            safe_float(
                score_weights.get(key)
            ),
        )

        if weight <= 0:
            continue

        weighted_sum += score * weight
        total_weight += weight

    if total_weight <= 0:
        return 0.0

    return round(
        clamp_score(
            weighted_sum / total_weight
        ),
        2,
    )


def calculate_beef_scores(
    *,
    product: Mapping[str, Any],
    parse_result: BeefParseResult,
    context: FoodKnowledgeContext | None = None,
) -> dict[str, float]:
    """
    외부 상품 점수와 Beef Registry 점수를 결합한다.

    현재 context는 인터페이스 호환성을 위해 전달받는다.
    priority별 가중치 적용은 이후 확장할 수 있다.
    """
    del context

    registry_scores = extract_registry_scores(
        parse_result
    )

    knowledge_score = (
        calculate_beef_knowledge_score(
            breed_score=registry_scores[
                "breed"
            ],
            grade_score=registry_scores[
                "grade"
            ],
            cut_score=registry_scores[
                "cut"
            ],
        )
    )

    return {
        "quality": round(
            clamp_score(
                product.get(
                    "quality_score"
                )
            ),
            2,
        ),
        "price": round(
            clamp_score(
                product.get(
                    "price_score"
                )
            ),
            2,
        ),
        "trust": round(
            clamp_score(
                product.get(
                    "trust_score"
                )
            ),
            2,
        ),
        "breed": registry_scores[
            "breed"
        ],
        "grade": registry_scores[
            "grade"
        ],
        "cut": registry_scores[
            "cut"
        ],
        "tenderness": registry_scores[
            "tenderness"
        ],
        "knowledge": knowledge_score,
    }


def calculate_beef_final_score(
    scores: Mapping[str, Any],
    *,
    weights: Mapping[str, float] | None = None,
) -> float:
    """
    상품 외부 점수와 Beef Knowledge 점수를 이용해
    최종 점수를 계산한다.
    """
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
    "DEFAULT_FINAL_SCORE_WEIGHTS",
    "DEFAULT_KNOWLEDGE_WEIGHTS",
    "safe_float",
    "clamp_score",
    "extract_registry_scores",
    "calculate_beef_knowledge_score",
    "calculate_beef_scores",
    "calculate_beef_final_score",
]
