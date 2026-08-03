from __future__ import annotations

import re
from typing import Any

from .text_utils import clean_display_text


def normalize_weight_to_grams(
    weight_text: Any,
) -> float:
    """중량 문자열을 g 기준 숫자로 변환합니다."""

    if not weight_text:
        return 0.0

    match = re.search(
        r"(\d+(?:\.\d+)?)\s*(kg|g)",
        str(weight_text),
        re.IGNORECASE,
    )

    if not match:
        return 0.0

    value = float(
        match.group(1)
    )

    unit = match.group(2).lower()

    if unit == "kg":
        return value * 1000

    return value


def get_weight_text_from_item(
    item: dict | None,
) -> str:
    """원본 item과 상품명에서 중량 텍스트를 추출합니다."""

    item = item or {}

    candidates = [
        item.get("weight_text"),
        item.get("weight"),
        item.get("product_weight"),
        item.get("capacity"),
        item.get("volume"),
        item.get("product_name"),
        item.get("raw_name"),
        item.get("title"),
        item.get("name"),
    ]

    for value in candidates:
        text_value = clean_display_text(
            value
        )

        if not text_value:
            continue

        match = re.search(
            r"(\d+(?:\.\d+)?)\s*(kg|g)",
            text_value,
            re.IGNORECASE,
        )

        if match:
            return (
                f"{match.group(1)}"
                f"{match.group(2)}"
            )

    return ""