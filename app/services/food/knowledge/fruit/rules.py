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


def evaluate_fruit_rules(
    attributes: Mapping[str, Any],
    scores: Mapping[str, float],
) -> list[FoodRuleResult]:
    """
    과일 상품의 추천 이유와 주의사항을 평가한다.
    """

    rules: list[FoodRuleResult] = []

    rules.extend(
        _evaluate_brix_rules(
            attributes
        )
    )

    rules.extend(
        _evaluate_origin_rules(
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


def split_fruit_rule_messages(
    rule_results: list[FoodRuleResult],
) -> tuple[list[str], list[str]]:
    return split_rule_messages(
        rule_results
    )


def build_fruit_rules(
    attributes: Mapping[str, Any],
    scores: Mapping[str, float],
) -> tuple[
    list[FoodRuleResult],
    list[str],
    list[str],
]:
    rule_results = evaluate_fruit_rules(
        attributes,
        scores,
    )

    reasons, warnings = (
        split_fruit_rule_messages(
            rule_results
        )
    )

    return (
        rule_results,
        reasons,
        warnings,
    )


def _evaluate_brix_rules(
    attributes: Mapping[str, Any],
) -> list[FoodRuleResult]:
    brix = safe_float(
        attributes.get("brix"),
        default=None,
    )

    if brix is None:
        return [
            create_rule(
                rule_id="fruit.missing_brix",
                message=(
                    "당도 정보가 제공되지 않았습니다."
                ),
                severity="warning",
            )
        ]

    if brix >= 14:
        return [
            create_rule(
                rule_id="fruit.high_brix",
                message=(
                    "당도가 매우 높은 상품으로 평가됩니다."
                ),
                severity="positive",
                metadata={
                    "brix": brix,
                },
            )
        ]

    if brix >= 12:
        return [
            create_rule(
                rule_id="fruit.good_brix",
                message=(
                    "당도가 높은 편인 과일입니다."
                ),
                severity="positive",
                metadata={
                    "brix": brix,
                },
            )
        ]

    return [
        create_rule(
            rule_id="fruit.normal_brix",
            message=(
                "표시 당도는 일반적인 수준입니다."
            ),
            severity="info",
            metadata={
                "brix": brix,
            },
        )
    ]


def _evaluate_origin_rules(
    attributes: Mapping[str, Any],
) -> list[FoodRuleResult]:
    origin = attributes.get("origin")

    if origin:
        return [
            create_rule(
                rule_id="fruit.origin_available",
                message=(
                    f"원산지 정보가 확인되었습니다: {origin}"
                ),
                severity="positive",
            )
        ]

    return [
        create_rule(
            rule_id="fruit.missing_origin",
            message=(
                "원산지 정보가 확인되지 않았습니다."
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
                rule_id="fruit.grade_available",
                message=(
                    f"표시 등급은 {grade}입니다."
                ),
                severity="info",
            )
        ]

    return [
        create_rule(
            rule_id="fruit.missing_grade",
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
            "fruit.high_quality_score",
            "품질 평가 점수가 높은 상품입니다.",
        ),
        (
            "price",
            "fruit.high_price_value",
            "가격 경쟁력이 높은 상품입니다.",
        ),
        (
            "trust",
            "fruit.high_trust_score",
            "판매 및 반응 신뢰도가 높은 상품입니다.",
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
        and information_score < 50
    ):
        rules.append(
            create_rule(
                rule_id="fruit.low_information",
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
        "고당도": (
            "상품명에서 고당도 특징이 확인됩니다."
        ),
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
                    "fruit.keyword."
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
