from __future__ import annotations

from collections.abc import Mapping

from app.services.food.knowledge.common import (
    create_rule,
    safe_float,
    split_rule_messages,
)
from app.services.food.knowledge.models import (
    FoodRuleResult,
)


def evaluate_seafood_rules(
    attributes: Mapping[str, object],
    scores: Mapping[str, float],
) -> list[FoodRuleResult]:
    if not isinstance(attributes, Mapping):
        raise TypeError(
            "attributes must be a Mapping"
        )

    if not isinstance(scores, Mapping):
        raise TypeError(
            "scores must be a Mapping"
        )

    rules: list[FoodRuleResult] = []

    species = attributes.get("species")

    if species:
        rules.append(
            create_rule(
                rule_id="seafood.species_available",
                message=(
                    f"수산물 종 정보가 확인되었습니다: "
                    f"{species}"
                ),
                severity="positive",
            )
        )
    else:
        rules.append(
            create_rule(
                rule_id="seafood.missing_species",
                message=(
                    "수산물 종 정보가 확인되지 않았습니다."
                ),
                severity="warning",
            )
        )

    origin = attributes.get("origin")

    if origin:
        rules.append(
            create_rule(
                rule_id="seafood.origin_available",
                message=(
                    f"원산지 정보가 확인되었습니다: "
                    f"{origin}"
                ),
                severity="positive",
            )
        )
    else:
        rules.append(
            create_rule(
                rule_id="seafood.missing_origin",
                message=(
                    "원산지 정보가 확인되지 않았습니다."
                ),
                severity="warning",
            )
        )

    processing_state = attributes.get(
        "processing_state"
    )

    if processing_state:
        rules.append(
            create_rule(
                rule_id=(
                    "seafood.processing_state_available"
                ),
                message=(
                    "상품 상태 정보가 확인되었습니다: "
                    f"{processing_state}"
                ),
                severity="info",
            )
        )

    wild_farmed_status = attributes.get(
        "wild_farmed_status"
    )

    if wild_farmed_status:
        rules.append(
            create_rule(
                rule_id=(
                    "seafood.production_status_available"
                ),
                message=(
                    "자연산/양식 정보가 확인되었습니다: "
                    f"{wild_farmed_status}"
                ),
                severity="info",
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
                rule_id="seafood.low_information",
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


def split_seafood_rule_messages(
    rule_results: list[FoodRuleResult],
) -> tuple[list[str], list[str]]:
    return split_rule_messages(rule_results)


def build_seafood_rules(
    attributes: Mapping[str, object],
    scores: Mapping[str, float],
) -> tuple[
    list[FoodRuleResult],
    list[str],
    list[str],
]:
    rule_results = evaluate_seafood_rules(
        attributes,
        scores,
    )

    reasons, warnings = (
        split_seafood_rule_messages(
            rule_results
        )
    )

    return (
        rule_results,
        reasons,
        warnings,
    )


__all__ = [
    "evaluate_seafood_rules",
    "split_seafood_rule_messages",
    "build_seafood_rules",
]
