from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.services.food.knowledge.common.constants import (
    MAX_SCORE,
    MIN_SCORE,
)
from app.services.food.knowledge.common.normalizer import (
    safe_float,
)


def clamp_score(
    value: Any,
    *,
    minimum: float = MIN_SCORE,
    maximum: float = MAX_SCORE,
) -> float:
    parsed = safe_float(
        value,
        default=minimum,
    )

    if parsed is None:
        parsed = minimum

    return round(
        max(
            minimum,
            min(maximum, parsed),
        ),
        2,
    )


def normalize_range_score(
    value: Any,
    *,
    minimum_value: float,
    maximum_value: float,
    minimum_score: float = MIN_SCORE,
    maximum_score: float = MAX_SCORE,
) -> float:
    parsed = safe_float(
        value,
        default=None,
    )

    if parsed is None:
        return minimum_score

    if maximum_value <= minimum_value:
        raise ValueError(
            "maximum_value must be greater than minimum_value"
        )

    ratio = (
        parsed - minimum_value
    ) / (
        maximum_value - minimum_value
    )

    score = (
        minimum_score
        + ratio
        * (
            maximum_score
            - minimum_score
        )
    )

    return clamp_score(
        score,
        minimum=minimum_score,
        maximum=maximum_score,
    )


def weighted_average(
    scores: Mapping[str, Any],
    weights: Mapping[str, float],
    *,
    normalize_weights: bool = True,
) -> float:
    weighted_sum = 0.0
    total_weight = 0.0

    for key, weight in weights.items():
        parsed_weight = safe_float(
            weight,
            default=0.0,
        )

        if parsed_weight is None:
            continue

        if parsed_weight <= 0:
            continue

        score = clamp_score(
            scores.get(key, 0.0)
        )

        weighted_sum += score * parsed_weight
        total_weight += parsed_weight

    if total_weight <= 0:
        return 0.0

    if normalize_weights:
        weighted_sum /= total_weight

    return clamp_score(weighted_sum)


def first_numeric_score(
    product: Mapping[str, Any],
    keys: tuple[str, ...],
    *,
    default: float = 0.0,
) -> float:
    for key in keys:
        value = product.get(key)

        parsed = safe_float(
            value,
            default=None,
        )

        if parsed is not None:
            return clamp_score(parsed)

    return clamp_score(default)


def apply_score_boost(
    score: Any,
    boost: Any,
) -> float:
    parsed_score = clamp_score(score)

    parsed_boost = safe_float(
        boost,
        default=0.0,
    )

    if parsed_boost is None:
        parsed_boost = 0.0

    return clamp_score(
        parsed_score + parsed_boost
    )
