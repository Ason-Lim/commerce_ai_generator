from __future__ import annotations

from typing import Any

from .text_utils import (
    clean_display_text,
)


def get_raw_product_url(
    item: dict | None,
) -> str:
    """상품 URL 후보를 여러 필드에서 안전하게 추출합니다."""

    item = item or {}

    url_candidates = [
        item.get("product_url"),
        item.get("url"),
        item.get("link"),
        item.get("product_link"),
        item.get("detail_url"),
        item.get("landing_url"),
    ]

    for url in url_candidates:
        cleaned_url = clean_display_text(
            url
        )

        if not cleaned_url:
            continue

        return cleaned_url

    return ""


def is_search_url(
    url: Any,
) -> bool:
    """상품 상세 페이지가 아닌 검색 URL인지 판단합니다."""

    cleaned_url = clean_display_text(
        url
    ).lower()

    if not cleaned_url:
        return False

    return (
        "/search" in cleaned_url
        or "sword=" in cleaned_url
        or "query=" in cleaned_url
    )