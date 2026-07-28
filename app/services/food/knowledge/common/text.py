from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable
from typing import Any


_WHITESPACE_PATTERN = re.compile(r"\s+")


def normalize_text(
    value: Any,
    *,
    lowercase: bool = False,
) -> str:
    if value is None:
        return ""

    text = unicodedata.normalize(
        "NFKC",
        str(value),
    )

    text = _WHITESPACE_PATTERN.sub(
        " ",
        text,
    ).strip()

    if lowercase:
        text = text.lower()

    return text


def contains_keyword(
    text: Any,
    keyword: Any,
    *,
    case_sensitive: bool = False,
) -> bool:
    normalized_text = normalize_text(
        text,
        lowercase=not case_sensitive,
    )
    normalized_keyword = normalize_text(
        keyword,
        lowercase=not case_sensitive,
    )

    if not normalized_text or not normalized_keyword:
        return False

    return normalized_keyword in normalized_text


def detect_keywords(
    text: Any,
    keywords: Iterable[str],
    *,
    case_sensitive: bool = False,
) -> list[str]:
    return [
        keyword
        for keyword in keywords
        if contains_keyword(
            text,
            keyword,
            case_sensitive=case_sensitive,
        )
    ]


def deduplicate_texts(
    values: Iterable[Any],
) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []

    for value in values:
        normalized = normalize_text(value)

        if not normalized:
            continue

        comparison_key = normalized.lower()

        if comparison_key in seen:
            continue

        seen.add(comparison_key)
        result.append(normalized)

    return result
