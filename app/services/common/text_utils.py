from __future__ import annotations

from typing import Any


def clean_display_text(
    value: Any,
) -> str:
    """표시용 문자열 정리."""

    if value is None:
        return ""

    text = str(value).strip()

    empty_tokens = {
        "[]",
        "{}",
        "None",
        "null",
        "nan",
        "NaN",
        "-",
    }

    if text in empty_tokens:
        return ""

    return text