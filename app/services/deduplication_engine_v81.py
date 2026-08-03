import re
from difflib import SequenceMatcher


def normalize_name(name: str) -> str:
    if not name:
        return ""

    name = name.lower()

    # 괄호 제거
    name = re.sub(r"\(.*?\)", "", name)

    # 특수문자 제거
    name = re.sub(r"[^가-힣a-z0-9 ]", " ", name)

    # 공백 정리
    name = " ".join(name.split())

    return name


def similarity(a: str, b: str) -> float:
    return SequenceMatcher(
        None,
        normalize_name(a),
        normalize_name(b),
    ).ratio()


def choose_better(item1: dict, item2: dict):
    """
    동일 상품이면 더 좋은 하나만 선택
    """

    score1 = item1.get("platform_boost_score", 0)
    score2 = item2.get("platform_boost_score", 0)

    if score2 > score1:
        return item2

    price1 = item1.get("price") or 999999999
    price2 = item2.get("price") or 999999999

    if price2 < price1:
        return item2

    return item1

def deduplicate_market_items(
    items: list,
    threshold: float = 0.93,
):
    unique = []

    for item in items:

        merged = False

        for idx, exist in enumerate(unique):

            if similarity(
                item.get("product_name", ""),
                exist.get("product_name", ""),
            ) >= threshold:

                unique[idx] = choose_better(
                    exist,
                    item,
                )

                merged = True
                break

        if not merged:
            unique.append(item)

    # ✅ for문 종료 후 한 번만 출력
    before = len(items)
    after = len(unique)

    print(f"[Dedup V8.1] {before} -> {after} ({before-after}개 중복 제거)")

    return unique
