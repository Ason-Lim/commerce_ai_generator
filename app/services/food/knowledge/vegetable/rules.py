from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.services.food.knowledge.common import (
    create_rule,
    safe_float,
    split_rule_messages,
)
from app.services.food.knowledge.models import (
    FoodRuleResult,
)


def evaluate_vegetable_rules(
    attributes: Mapping[str, Any],
    scores: Mapping[str, float],
) -> list[FoodRuleResult]:
    """
    Vegetable attributes와 scores에 대한
    독립적인 도메인 Rule 평가.
    """
    if not isinstance(attributes, Mapping):
        raise TypeError(
            "attributes must be a Mapping"
        )

    if not isinstance(scores, Mapping):
        raise TypeError(
            "scores must be a Mapping"
        )

    rules: list[FoodRuleResult] = []

    rules.extend(
        _evaluate_origin_rules(
            attributes
        )
    )

    rules.extend(
        _evaluate_variety_rules(
            attributes
        )
    )

    rules.extend(
        _evaluate_grade_rules(
            attributes
        )
    )

    rules.extend(
        _evaluate_score_rules(
            scores
        )
    )

    rules.extend(
        _evaluate_keyword_rules(
            attributes
        )
    )

    return rules


def split_vegetable_rule_messages(
    rule_results: list[FoodRuleResult],
) -> tuple[list[str], list[str]]:
    return split_rule_messages(
        rule_results
    )


def build_vegetable_rules(
    attributes: Mapping[str, Any],
    scores: Mapping[str, float],
) -> tuple[
    list[FoodRuleResult],
    list[str],
    list[str],
]:
    rule_results = evaluate_vegetable_rules(
        attributes,
        scores,
    )

    reasons, warnings = (
        split_vegetable_rule_messages(
            rule_results
        )
    )

    return (
        rule_results,
        reasons,
        warnings,
    )


def _evaluate_origin_rules(
    attributes: Mapping[str, Any],
) -> list[FoodRuleResult]:
    origin = attributes.get("origin")

    if origin:
        return [
            create_rule(
                rule_id=(
                    "vegetable.origin_available"
                ),
                message=(
                    f"원산지 정보가 확인되었습니다: {origin}"
                ),
                severity="positive",
            )
        ]

    return [
        create_rule(
            rule_id="vegetable.missing_origin",
            message=(
                "원산지 정보가 확인되지 않았습니다."
            ),
            severity="warning",
        )
    ]


def _evaluate_variety_rules(
    attributes: Mapping[str, Any],
) -> list[FoodRuleResult]:
    variety = attributes.get("variety")

    if variety:
        return [
            create_rule(
                rule_id=(
                    "vegetable.variety_available"
                ),
                message=(
                    f"채소 품목 또는 품종이 확인되었습니다: "
                    f"{variety}"
                ),
                severity="positive",
            )
        ]

    return [
        create_rule(
            rule_id="vegetable.missing_variety",
            message=(
                "채소 품목 또는 품종 정보가 "
                "확인되지 않았습니다."
            ),
            severity="warning",
        )
    ]


def _evaluate_grade_rules(
    attributes: Mapping[str, Any],
) -> list[FoodRuleResult]:
    grade = attributes.get("grade")

    if grade:
        return [
            create_rule(
                rule_id="vegetable.grade_available",
                message=(
                    f"표시 등급은 {grade}입니다."
                ),
                severity="info",
            )
        ]

    return [
        create_rule(
            rule_id="vegetable.missing_grade",
            message=(
                "상품 등급 정보가 제공되지 않았습니다."
            ),
            severity="warning",
        )
    ]


def _evaluate_score_rules(
    scores: Mapping[str, float],
) -> list[FoodRuleResult]:
    rules: list[FoodRuleResult] = []

    score_definitions = (
        (
            "quality",
            "vegetable.high_quality_score",
            "품질 평가 점수가 높은 상품입니다.",
        ),
        (
            "price",
            "vegetable.high_price_value",
            "가격 평가 점수가 높은 상품입니다.",
        ),
        (
            "trust",
            "vegetable.high_trust_score",
            "상품 신뢰 평가 점수가 높은 편입니다.",
        ),
    )

    for (
        score_name,
        rule_id,
        message,
    ) in score_definitions:
        score = safe_float(
            scores.get(score_name),
            default=0.0,
        )

        if score is None or score < 80:
            continue

        rules.append(
            create_rule(
                rule_id=rule_id,
                message=message,
                severity="positive",
                metadata={
                    "score": score,
                },
            )
        )

    information_score = safe_float(
        scores.get("information"),
        default=0.0,
    )

    if (
        information_score is not None
        and information_score < 60
    ):
        rules.append(
            create_rule(
                rule_id=(
                    "vegetable.low_information"
                ),
                message=(
                    "상품 상세 정보가 충분하지 않습니다."
                ),
                severity="warning",
                metadata={
                    "score": information_score,
                },
            )
        )

    return rules


def _evaluate_keyword_rules(
    attributes: Mapping[str, Any],
) -> list[FoodRuleResult]:
    keywords = (
        attributes.get(
            "detected_keywords"
        )
        or []
    )

    keyword_messages = {
        "산지직송": (
            "산지직송 상품으로 표시되어 있습니다."
        ),
        "당일수확": (
            "당일수확 상품으로 표시되어 있습니다."
        ),
        "유기농": (
            "유기농 상품으로 표시되어 있습니다."
        ),
        "무농약": (
            "무농약 상품으로 표시되어 있습니다."
        ),
        "친환경": (
            "친환경 상품으로 표시되어 있습니다."
        ),
        "저탄소": (
            "저탄소 상품으로 표시되어 있습니다."
        ),
        "GAP": (
            "GAP 인증 관련 표시가 확인됩니다."
        ),
        "세척": (
            "세척 상품으로 표시되어 있습니다."
        ),
        "손질": (
            "손질 상품으로 표시되어 있습니다."
        ),
    }

    rules: list[FoodRuleResult] = []

    for keyword in keywords:
        message = keyword_messages.get(
            keyword
        )

        if not message:
            continue

        rules.append(
            create_rule(
                rule_id=(
                    "vegetable.keyword."
                    f"{str(keyword).lower()}"
                ),
                message=message,
                severity="info",
                metadata={
                    "keyword": keyword,
                },
            )
        )

    return rules


__all__ = [
    "evaluate_vegetable_rules",
    "split_vegetable_rule_messages",
    "build_vegetable_rules",
]
