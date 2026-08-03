import re
from difflib import SequenceMatcher
from urllib.parse import urlparse, parse_qs


REMOVE_PATTERNS = [
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
]


def normalize_name(name: str) -> str:
    text = (name or "").lower()

    for pattern in REMOVE_PATTERNS:
        text = re.sub(pattern, " ", text, flags=re.IGNORECASE)

    text = re.sub(r"\(.*?\)", " ", text)
    text = re.sub(r"[^가-힣a-z0-9 ]", " ", text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, normalize_name(a), normalize_name(b)).ratio()


def safe_float(value, default=0):
    try:
        if value is None or value == "":
            return default
        return float(value)
    except Exception:
        return default


def extract_url_identity(url: str) -> dict:
    if not url:
        return {}

    try:
        parsed = urlparse(url)
        qs = parse_qs(parsed.query)

        return {
            "pageKey": (qs.get("pageKey") or [""])[0],
            "itemId": (qs.get("itemId") or [""])[0],
            "vendorItemId": (qs.get("vendorItemId") or [""])[0],
        }
    except Exception:
        return {}


def build_identity_key(item: dict) -> str:
    url = item.get("product_url") or item.get("raw_link") or ""
    url_ids = extract_url_identity(url)

    platform = item.get("platform") or ""
    mall = item.get("mall_name") or item.get("seller_name") or ""
    name = normalize_name(item.get("product_name") or item.get("name") or "")

    if url_ids.get("pageKey") and url_ids.get("itemId"):
        return f"coupang:{url_ids['pageKey']}:{url_ids['itemId']}"

    if item.get("product_identity_key"):
        return f"identity:{item.get('product_identity_key')}"

    return f"{platform}:{mall}:{name}"


def choose_better(item1: dict, item2: dict):
    score1 = safe_float(
        item1.get("v8_final_score")
        or item1.get("v7_final_score")
        or item1.get("platform_boost_score")
    )

    score2 = safe_float(
        item2.get("v8_final_score")
        or item2.get("v7_final_score")
        or item2.get("platform_boost_score")
    )

    if score2 > score1:
        return item2
    if score1 > score2:
        return item1

    price1 = safe_float(item1.get("price"), 999999999)
    price2 = safe_float(item2.get("price"), 999999999)

    return item2 if price2 < price1 else item1


def is_same_product(item1: dict, item2: dict) -> bool:
    key1 = build_identity_key(item1)
    key2 = build_identity_key(item2)

    if key1 and key2 and key1 == key2:
        return True

    name1 = item1.get("product_name") or item1.get("name") or ""
    name2 = item2.get("product_name") or item2.get("name") or ""
    
    normalized_name1 = normalize_name(name1)
    normalized_name2 = normalize_name(name2)

    # 상품명이 정규화 후 완전히 같으면 동일 상품으로 처리
    if normalized_name1 and normalized_name1 == normalized_name2:
        return True
    
    sim = similarity(name1, name2)

    if sim < 0.80:
        return False

    price1 = safe_float(item1.get("price"), 0)
    price2 = safe_float(item2.get("price"), 0)

    if price1 <= 0 or price2 <= 0:
        return sim >= 0.93

    price_diff_ratio = abs(price1 - price2) / max(price1, price2)

    return price_diff_ratio <= 0.35


def deduplicate_market_items(items: list[dict]) -> list[dict]:
    unique = []
    key_index = {}

    for item in items:
        if not isinstance(item, dict):
            continue

        key = build_identity_key(item)

        if key in key_index:
            idx = key_index[key]
            unique[idx] = choose_better(unique[idx], item)
            continue

        merged = False

        for idx, exist in enumerate(unique):
            if is_same_product(item, exist):
                unique[idx] = choose_better(exist, item)
                key_index[key] = idx
                merged = True
                break

        if not merged:
            key_index[key] = len(unique)
            unique.append(item)

    before = len(items)
    after = len(unique)

    print("=" * 60)
    print("[Deduplication Engine V8.3]")
    print(f"Original : {before}")
    print(f"Unique   : {after}")
    print(f"Removed  : {before - after}")
    print("=" * 60)

    return unique
