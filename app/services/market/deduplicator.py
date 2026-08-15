from __future__ import annotations

import hashlib
import re
from collections import defaultdict
from typing import Any, Dict, Iterable, List


STOP_WORDS = {
    "무료배송",
    "국내산",
    "당일",
    "새벽",
    "특가",
    "행사",
    "정품",
}


def normalize_product_name(name: str) -> str:
    """
    상품명을 비교 가능한 형태로 정규화한다.
    """

    if not name:
        return ""

    text = name.lower()

    text = re.sub(r"\[[^\]]*\]", " ", text)
    text = re.sub(r"\([^)]*\)", " ", text)
    text = re.sub(r"[^0-9a-z가-힣kgml입 ]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    words = [
        word
        for word in text.split()
        if word not in STOP_WORDS
    ]

    return " ".join(words)


def build_group_key(item: Dict[str, Any]) -> str:
    """
    동일 상품을 대표하는 Key 생성
    """

    brand = (
        item.get("brand_name")
        or ""
    ).strip().lower()

    category = (
        item.get("category_name")
        or ""
    ).strip().lower()

    product = normalize_product_name(
        item.get("product_name", "")
    )

    key = "|".join(
        [
            category,
            brand,
            product,
        ]
    )

    return hashlib.md5(
        key.encode("utf-8")
    ).hexdigest()


def deduplicate_market_items(
    items: Iterable[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    동일 상품을 플랫폼별 그룹으로 묶는다.
    """

    groups = defaultdict(list)

    for item in items:

        group_key = build_group_key(item)

        copied = dict(item)
        copied["group_key"] = group_key

        groups[group_key].append(copied)

    results = []

    for group_key, grouped_items in groups.items():

        grouped_items.sort(
            key=lambda x: (
                x.get("price") is None,
                x.get("price", 0),
            )
        )

        representative = grouped_items[0]

        results.append(
            {
                "group_key": group_key,
                "canonical_name": representative.get(
                    "product_name"
                ),
                "brand_name": representative.get(
                    "brand_name"
                ),
                "category_name": representative.get(
                    "category_name"
                ),
                "platform_count": len(
                    {
                        item.get("platform")
                        for item in grouped_items
                        if item.get("platform")
                    }
                ),
                "item_count": len(grouped_items),
                "lowest_price": representative.get(
                    "price"
                ),
                "items": grouped_items,
            }
        )

    results.sort(
        key=lambda g: (
            -g["platform_count"],
            g["lowest_price"]
            if g["lowest_price"] is not None
            else 10**12,
        )
    )

    return results