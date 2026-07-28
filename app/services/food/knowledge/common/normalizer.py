from __future__ import annotations

import re
from typing import Any

from app.services.food.knowledge.common.text import (
    normalize_text,
)


_NUMBER_PATTERN = re.compile(
    r"-?\d+(?:\.\d+)?"
)

_WEIGHT_PATTERNS = (
    (
        re.compile(
            r"(?P<value>\d+(?:\.\d+)?)\s*(?:kg|킬로그램|킬로)",
            flags=re.IGNORECASE,
        ),
        1000.0,
    ),
    (
        re.compile(
            r"(?P<value>\d+(?:\.\d+)?)\s*(?:g|그램)",
            flags=re.IGNORECASE,
        ),
        1.0,
    ),
)

_MILLILITER_PATTERNS = (
    (
        re.compile(
            r"(?P<value>\d+(?:\.\d+)?)\s*(?:l|리터)",
            flags=re.IGNORECASE,
        ),
        1000.0,
    ),
    (
        re.compile(
            r"(?P<value>\d+(?:\.\d+)?)\s*(?:ml|밀리리터)",
            flags=re.IGNORECASE,
        ),
        1.0,
    ),
)


def safe_float(
    value: Any,
    *,
    default: float | None = 0.0,
) -> float | None:
    if value is None or value == "":
        return default

    if isinstance(value, bool):
        return default

    if isinstance(value, (int, float)):
        return float(value)

    text = normalize_text(value).replace(",", "")

    matched = _NUMBER_PATTERN.search(text)

    if not matched:
        return default

    try:
        return float(matched.group())
    except ValueError:
        return default


def safe_int(
    value: Any,
    *,
    default: int | None = 0,
) -> int | None:
    parsed = safe_float(
        value,
        default=None,
    )

    if parsed is None:
        return default

    return int(parsed)


def normalize_weight_grams(
    value: Any,
) -> float | None:
    text = normalize_text(
        value,
        lowercase=True,
    )

    if not text:
        return None

    for pattern, multiplier in _WEIGHT_PATTERNS:
        matched = pattern.search(text)

        if not matched:
            continue

        parsed = safe_float(
            matched.group("value"),
            default=None,
        )

        if parsed is None:
            continue

        return round(
            parsed * multiplier,
            2,
        )

    return None


def normalize_volume_ml(
    value: Any,
) -> float | None:
    text = normalize_text(
        value,
        lowercase=True,
    )

    if not text:
        return None

    for pattern, multiplier in _MILLILITER_PATTERNS:
        matched = pattern.search(text)

        if not matched:
            continue

        parsed = safe_float(
            matched.group("value"),
            default=None,
        )

        if parsed is None:
            continue

        return round(
            parsed * multiplier,
            2,
        )

    return None


def normalize_boolean(
    value: Any,
    *,
    default: bool | None = None,
) -> bool | None:
    if isinstance(value, bool):
        return value

    if value is None:
        return default

    normalized = normalize_text(
        value,
        lowercase=True,
    )

    true_values = {
        "true",
        "yes",
        "y",
        "1",
        "예",
        "맞음",
        "포함",
        "해당",
    }

    false_values = {
        "false",
        "no",
        "n",
        "0",
        "아니오",
        "아님",
        "미포함",
        "비해당",
    }

    if normalized in true_values:
        return True

    if normalized in false_values:
        return False

    return default
