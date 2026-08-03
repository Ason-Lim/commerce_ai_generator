import re
from difflib import SequenceMatcher


# --------------------------------------------------------
# 광고/프로모션 문구 제거
# --------------------------------------------------------

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
]


def normalize_name(name: str) -> str:

    if not name:
        return ""

    text = name.lower()

    for pattern in REMOVE_PATTERNS:
        text = re.sub(
            pattern,
            " ",
            text,
            flags=re.IGNORECASE,
        )

    text = re.sub(r"\(.*?\)", " ", text)

    text = re.sub(
        r"[^가-힣a-z0-9 ]",
        " ",
        text,
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


# --------------------------------------------------------
# 문자열 유사도
# --------------------------------------------------------

def similarity(a: str, b: str) -> float:

    return SequenceMatcher(
        None,
        normalize_name(a),
        normalize_name(b),
    ).ratio()


# --------------------------------------------------------
# 더 좋은 상품 선택
# --------------------------------------------------------

def choose_better(item1: dict, item2: dict):

    ai1 = (
        item1.get("v7_final_score")
        or item1.get("platform_boost_score")
        or 0
    )

    ai2 = (
        item2.get("v7_final_score")
        or item2.get("platform_boost_score")
        or 0
    )

    if ai2 > ai1:
        return item2

    if ai1 > ai2:
        return item1

    price1 = float(item1.get("price") or 999999999)
    price2 = float(item2.get("price") or 999999999)

    if price2 < price1:
        return item2

    return item1


# --------------------------------------------------------
# 동일 상품 여부
# --------------------------------------------------------

def is_same_product(item1, item2):

    name1 = normalize_name(
        item1.get("product_name", "")
    )

    name2 = normalize_name(
        item2.get("product_name", "")
    )

    sim = similarity(name1, name2)

    if sim < 0.88:
        return False

    price1 = float(item1.get("price") or 0)
    price2 = float(item2.get("price") or 0)

    if price1 <= 0 or price2 <= 0:
        return sim >= 0.93

    diff = abs(price1 - price2)

    return diff <= max(price1, price2) * 0.15


# --------------------------------------------------------
# 중복 제거 엔진 V8.2
# --------------------------------------------------------

def deduplicate_market_items(items):

    unique = []

    for item in items:

        merged = False

        for idx, exist in enumerate(unique):

            if is_same_product(
                item,
                exist,
            ):

                unique[idx] = choose_better(
                    exist,
                    item,
                )

                merged = True
                break

        if not merged:
            unique.append(item)

    before = len(items)
    after = len(unique)

    print("=" * 60)
    print("[Deduplication Engine V8.2]")
    print(f"Original : {before}")
    print(f"Unique   : {after}")
    print(f"Removed  : {before-after}")
    print("=" * 60)

    return unique