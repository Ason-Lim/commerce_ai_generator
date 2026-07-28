from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from app.services.food.knowledge.common.text import (
    deduplicate_texts,
)
from app.services.food.knowledge.models import (
    FoodRuleResult,
)


WARNING_SEVERITIES = {
    "warning",
    "error",
    "critical",
}


def split_rule_messages(
    rule_results: Iterable[FoodRuleResult],
) -> tuple[list[str], list[str]]:
    reasons: list[str] = []
    warnings: list[str] = []

    for rule in rule_results:
        if not rule.matched:
            continue

        message = str(
            rule.message or ""
        ).strip()

        if not message:
            continue

        severity = str(
            rule.severity or "info"
        ).strip().lower()

        if severity in WARNING_SEVERITIES:
            warnings.append(message)
        else:
            reasons.append(message)

    return (
        deduplicate_texts(reasons),
        deduplicate_texts(warnings),
    )


def merge_rule_results(
    *rule_groups: Iterable[FoodRuleResult],
) -> list[FoodRuleResult]:
    result: list[FoodRuleResult] = []
    seen: set[tuple[str, str]] = set()

    for rule_group in rule_groups:
        for rule in rule_group:
            key = (
                str(rule.rule_id),
                str(rule.message),
            )

            if key in seen:
                continue

            seen.add(key)
            result.append(rule)

    return result


def create_rule(
    *,
    rule_id: str,
    message: str,
    severity: str = "info",
    matched: bool = True,
    metadata: dict[str, Any] | None = None,
) -> FoodRuleResult:
    return FoodRuleResult(
        rule_id=rule_id,
        matched=matched,
        message=message,
        severity=severity,
        metadata=metadata or {},
    )
