"""장보기 질문 다듬기 (2026-11-23 — 사용자·지인 의견).

* 어떤 고기로 하는지 갈리는 요리('백숙' → 닭백숙/오리백숙)는 레시피를 만들기 전에 먼저 묻는다.
* '재료 뭐 사야 해'처럼 장보기 질문이면 레시피 카드를 재료 먼저 · 만드는 순서 접힘(layout=shopping)으로.
* 손님이 '○○으로'라고 짚은 재료(가을 능이버섯으로 백숙…)는 상품을 맨 먼저 보여 준다.
"""
from __future__ import annotations

import re

# 요리 이름 → (선택지들, 이미 정해졌다고 볼 낱말)
AMBIGUOUS: dict[str, tuple[tuple[str, ...], str]] = {
    "백숙": (("닭백숙", "오리백숙"), r"닭|오리|삼계|토종닭|영계"),
    "갈비찜": (("소갈비찜", "돼지갈비찜"), r"소|돼지|한우|LA|엘에이"),
}

SHOPPING_Q = re.compile(r"(재료|뭐|무엇|뭘|뭐뭐)\S{0,4}\s*(사야|살까|사면|사요|구매|준비해야|필요해)|장보기|장\s*볼|사야\s*(해|할|돼|되)")
RECIPE_WORDS = re.compile(r"레시피|만드는\s*(법|방법)|요리\s*(법|방법)|조리\s*(법|방법)|끓이는\s*법|어떻게\s*만들")
_VIA = re.compile(r"([가-힣]{2,10}?)(?:으로|로)(?=\s)")
_NOT_INGREDIENT = {"선물", "간식", "이걸", "그걸", "저걸", "뭘", "무엇", "반찬", "안주", "아침", "점심", "저녁", "야식", "집에서",
                   "에어프라이어", "전자레인지", "냄비", "오븐", "밥솥", "혼자", "가족", "손님", "택배", "쿠팡", "인터넷", "최저가",
                   "한번", "처음", "오늘", "내일", "주말", "명절", "제사", "다이어트", "간단히", "빨리", "쉽게"}


def ro(word: str) -> str:
    """받침이 있으면(ㄹ 받침 제외) '으로', 아니면 '로'."""
    if not word:
        return "로"
    code = ord(word[-1]) - 0xAC00
    if not 0 <= code <= 11171:
        return "로"
    jong = code % 28
    return "으로" if jong and jong != 8 else "로"


def ambiguous(dish: str | None, text: str | None) -> tuple[str, tuple[str, ...]] | None:
    """(요리 이름 속 낱말, 선택지) — 이미 정해졌으면 None."""
    if not dish:
        return None
    flat = re.sub(r"\s+", "", dish)
    for key, (options, settled) in AMBIGUOUS.items():
        if flat.endswith(key) and not re.search(settled, flat) and not re.search(settled, text or ""):
            return key, options
    return None


def option_texts(text: str, key: str, options: tuple[str, ...]) -> list[str]:
    """손님 문장의 '백숙'을 선택지로 바꾼 문장 (칩을 누르면 그 문장을 보낸다)."""
    out = []
    for opt in options:
        if key in text:
            out.append(text.replace(key, opt, 1))
        else:
            out.append(f"{opt} {text}".strip())
    return out


def is_shopping_question(text: str | None) -> bool:
    t = text or ""
    return bool(SHOPPING_Q.search(t)) and not RECIPE_WORDS.search(t)


def named_ingredient(text: str | None) -> str | None:
    """'가을 능이버섯으로 백숙' → '능이버섯'. 도구·때·대상('에어프라이어로', '선물로')은 빼고."""
    for m in _VIA.finditer(text or ""):
        w = m.group(1)
        if w not in _NOT_INGREDIENT and not w.endswith(("에서", "한테", "에게")):
            return w
    return None


__all__ = ["ro", "AMBIGUOUS", "ambiguous", "option_texts", "is_shopping_question", "named_ingredient"]
