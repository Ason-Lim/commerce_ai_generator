from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.services.food.knowledge.common.constants import (
    DEFAULT_CONFIDENCE_FIELD_WEIGHT,
)
from app.services.food.knowledge.common.normalizer import (
    safe_float,
)


def is_available(
    value: Any,
) -> bool:
    if value is None:
        return False

    if isinstance(value, str):
        return bool(value.strip())

    if isinstance(value, (list, tuple, set, dict)):
        return bool(value)

    return True


def calculate_field_confidence(
    fields: Mapping[str, Any],
    *,
    weights: Mapping[str, float] | None = None,
    required_fields: set[str] | None = None,
    required_field_penalty: float = 0.1,
) -> float:
    if not fields:
        return 0.0

    weights = weights or {}
    required_fields = required_fields or set()

    available_weight = 0.0
    total_weight = 0.0
    missing_required_count = 0

    for field_name, value in fields.items():
        field_weight = safe_float(
            weights.get(
                field_name,
                DEFAULT_CONFIDENCE_FIELD_WEIGHT,
            ),
            default=DEFAULT_CONFIDENCE_FIELD_WEIGHT,
        )

        if field_weight is None:
            field_weight = DEFAULT_CONFIDENCE_FIELD_WEIGHT

        field_weight = max(0.0, field_weight)
        total_weight += field_weight

        if is_available(value):
            available_weight += field_weight
        elif field_name in required_fields:
            missing_required_count += 1

    if total_weight <= 0:
        return 0.0

    confidence = (
        available_weight / total_weight
    )

    confidence -= (
        missing_required_count
        * max(0.0, required_field_penalty)
    )

    return round(
        max(0.0, min(1.0, confidence)),
        2,
    )
