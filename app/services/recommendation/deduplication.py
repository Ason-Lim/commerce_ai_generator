from __future__ import annotations

import re
from difflib import SequenceMatcher
from urllib.parse import parse_qs, urlparse


REMOVE_PATTERNS = (
    r"\[.*?\]",
    r"\+\d+%쿠폰",
    r"\d+%쿠폰",
    r"쿠폰",
    r"특가",
    r"한정",
    r"무료배송",
    r"당일출고",
    r"오늘출발",
    r"샛별배송",
    r"새벽배송",
    r"프리미엄",
    r"명품",
    r"베스트",
    r"재구매\d*위",
    r"\d+박스한정",
    r"마지막최저가",
    r"단하루특가",
    r"파격초특가",
)


def normalize_name(name: str) -> str:
    text = (name or "").lower()

    for pattern in REMOVE_PATTERNS:
        text = re.sub(
            pattern,
            " ",
            text,
            flags=re.IGNORECASE,
        )

    text = re.sub(r"\(.*?\)", " ", text)
    text = re.sub(r"[^가-힣a-z0-9 ]", " ", text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def similarity(a: str, b: str) -> float:
    return SequenceMatcher(
        None,
        normalize_name(a),
        normalize_name(b),
    ).ratio()


def _safe_float(
    value: object,
    default: float = 0.0,
) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def extract_url_identity(url: str) -> dict[str, str]:
    if not url:
        return {}

    try:
        parsed = urlparse(url)
        query = parse_qs(parsed.query)

        return {
            "pageKey": (
                query.get("pageKey") or [""]
            )[0],
            "itemId": (
                query.get("itemId") or [""]
            )[0],
            "vendorItemId": (
                query.get("vendorItemId") or [""]
            )[0],
        }
    except (TypeError, ValueError):
        return {}


def build_identity_key(item: dict) -> str:
    explicit_identity = item.get(
        "product_identity_key"
    )

    if explicit_identity:
        return f"identity:{explicit_identity}"

    url = (
        item.get("product_url")
        or item.get("raw_link")
        or ""
    )
    url_ids = extract_url_identity(str(url))

    if (
        url_ids.get("pageKey")
        and url_ids.get("itemId")
    ):
        return (
            "coupang:"
            f"{url_ids['pageKey']}:"
            f"{url_ids['itemId']}"
        )

    platform = item.get("platform") or ""
    mall = (
        item.get("mall_name")
        or item.get("seller_name")
        or ""
    )
    name = normalize_name(
        item.get("product_name")
        or item.get("name")
        or ""
    )

    return f"{platform}:{mall}:{name}"


def choose_representative(
    item1: dict,
    item2: dict,
) -> dict:
    """
    Select a deterministic representative without
    performing recommendation ranking.

    Lower valid price wins. If neither candidate has
    a strictly lower valid price, preserve the first
    candidate.
    """
    price1 = _safe_float(item1.get("price"), 0.0)
    price2 = _safe_float(item2.get("price"), 0.0)

    valid1 = price1 > 0
    valid2 = price2 > 0

    if valid1 and valid2:
        return item2 if price2 < price1 else item1

    if valid2 and not valid1:
        return item2

    return item1


def is_same_product(
    item1: dict,
    item2: dict,
) -> bool:
    key1 = build_identity_key(item1)
    key2 = build_identity_key(item2)

    if key1 and key2 and key1 == key2:
        return True

    name1 = (
        item1.get("product_name")
        or item1.get("name")
        or ""
    )
    name2 = (
        item2.get("product_name")
        or item2.get("name")
        or ""
    )

    normalized1 = normalize_name(str(name1))
    normalized2 = normalize_name(str(name2))

    if (
        normalized1
        and normalized1 == normalized2
    ):
        return True

    score = similarity(
        str(name1),
        str(name2),
    )

    if score < 0.80:
        return False

    price1 = _safe_float(
        item1.get("price"),
        0.0,
    )
    price2 = _safe_float(
        item2.get("price"),
        0.0,
    )

    if price1 <= 0 or price2 <= 0:
        return score >= 0.93

    price_diff_ratio = (
        abs(price1 - price2)
        / max(price1, price2)
    )

    return price_diff_ratio <= 0.35


def deduplicate_market_items(
    items: list[dict],
) -> list[dict]:
    unique: list[dict] = []
    key_index: dict[str, int] = {}

    for item in items:
        if not isinstance(item, dict):
            continue

        key = build_identity_key(item)

        if key in key_index:
            idx = key_index[key]
            unique[idx] = choose_representative(
                unique[idx],
                item,
            )
            continue

        merged = False

        for idx, existing in enumerate(unique):
            if is_same_product(item, existing):
                unique[idx] = choose_representative(
                    existing,
                    item,
                )
                key_index[key] = idx
                merged = True
                break

        if not merged:
            key_index[key] = len(unique)
            unique.append(item)

    return unique
