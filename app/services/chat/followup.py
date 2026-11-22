"""대화 이어 묻기 1단계 — 조건 바꾸기 (2026-11-22, claude/chat_followup_design_2026-11-20.md · coupang_gap_design 3단계).

방금 보여 준 쇼핑 추천에 이어 짧게 말한 조건만 받는다 (규칙 사전 — AI 호출 없음):

| 말 | 의도 | 쿠팡 다시 찾기 |
|---|---|---|
| 싼 순으로 · 가격 낮은 순 · 더 싼 거 | sort(price) — 보여 준 후보를 가격 낮은 순 보기 ('추천순 아님') | 아니오 |
| 100g당 싼 순 | sort(per100g) | 아니오 |
| 로켓배송만 · 무료배송만 | filter — 보여 준 후보 중 표시가 있는 것만 (추천 순서 그대로) | 아니오 |
| ○○ 빼고 · ○○ 말고 | exclude — 상품명에 ○○가 없는 것만 | 아니오 |
| 2kg으로 · 1L짜리 · 10개짜리 | size/count — 검색어의 양을 바꿔 새로 찾음 | 예 |
| 선물용으로 | gift — '○○ 선물세트'로 새로 찾음 | 예 |
| 더 찾아보기 · 다른 거 더 | more — 바꿔 쓸 말로 더 찾아 '추천순 아님' 칸 | 예 |
| 처음 조건으로 · 원래대로 | reset — 처음 찾은 후보를 추천순으로 (저장된 후보, 새로 찾지 않음) | 아니오 |

* 문장 전체가 조건 말일 때만 잡는다 — '사과 2kg'·'올리브유 싼 거'처럼 품목이 들어가면 새 검색(평소 경로).
* 기본 추천순·고른 상품은 바꾸지 않는다(순위 동결). 정렬 보기는 '추천순 아님' 라벨 (사용자 결정 11-22).
* 쿠팡 다시 찾기는 대화(세션)당 FOLLOWUP_SEARCH_MAX(기본 10, 사용자 결정 11-22) — 넘으면 새로 찾지 않고 알린다.
  2026-11-22 외부 검토 1: '고객이 요청한 다시 찾기 횟수'(followup_searches)와 '실제 쿠팡 호출 수'(api_calls — 첫 검색·
  자동 다시 찾기·후보가 적을 때 더 찾기·실패 호출 포함, 같은 차례 같은 말은 한 번만)를 따로 센다. 이어 묻기 다시 찾기는
  둘 중 하나라도 상한(10번 / FOLLOWUP_API_MAX 40회)이면 하지 않는다.
* 보기 조건(정렬·배송 표시·빼기)은 쌓이고, 양·수량·선물·더 찾아보기로 다시 찾아도 이어 적용한다 (외부 검토 4).
  '처음 조건으로'는 한 단계 되돌리기가 아니라 **처음 찾은 후보로** 돌아가며 모든 조건을 푼다.
"""

from __future__ import annotations

import os
import re

FOLLOWUP_SEARCH_MAX = 10
RESEARCH_KINDS = ("size", "count", "gift", "more")

_END = r"\s*(?:(?:으로|로)?\s*(?:보여\s*(?:줘|주세요|줄래요?)|찾아\s*(?:줘|주세요|봐(?:요|줘)?)|해\s*(?:줘|주세요)|"\
       r"할게요?|볼게요?|요|은요|는요|있어요?|없어요?|부탁해요?)?)?\s*[?.!~]*$"

_SORT_PRICE = re.compile(r"^(?:(?:가격\s*)?(?:싼|저렴한|낮은|가격\s*낮은|가격)\s*순(?:서)?|더\s*(?:싼|저렴한)\s*(?:거|것|상품)?|"
                         r"싼\s*(?:거|것)\s*(?:부터|먼저)|가격\s*순)" + _END)
_SORT_PER100G = re.compile(r"^(?:100\s*g\s*당|그램\s*당|백\s*그램\s*당)\s*(?:가격\s*)?(?:싼|저렴한|낮은)?\s*순(?:서)?" + _END)
_ROCKET = re.compile(r"^로켓\s*(?:배송|프레시|와우)?\s*(?:만|으로|상품만)" + _END)
_FREE_SHIP = re.compile(r"^무료\s*배송\s*(?:만|상품만|으로)" + _END)
_EXCLUDE = re.compile(r"^(?P<word>[가-힣A-Za-z0-9]{1,15}?)\s*(?:은|는|이|가)?\s*(?:빼고|말고|제외(?:하고)?|없이|빼\s*줘)" + _END)
_SIZE = re.compile(r"^(?P<num>\d+(?:\.\d+)?)\s*(?P<unit>kg|킬로(?:그램)?|g|그램|l|리터|ml|미리(?:리터)?)\s*(?:짜리|정도|용량)?" + _END,
                   re.IGNORECASE)
_COUNT = re.compile(r"^(?P<num>\d{1,3})\s*(?P<unit>개|팩|봉|병|입|박스|세트)\s*(?:짜리|들이|묶음)?" + _END)
_GIFT = re.compile(r"^선물\s*(?:용|세트)" + _END)
_MORE = re.compile(r"^(?:더\s*찾아\s*(?:보기|봐(?:요|줘)?|줘|주세요)|다른\s*(?:상품|거|것)\s*(?:더|도)?\s*(?:있어요?|없어요?|보여\s*줘|찾아\s*줘)?|"
                   r"더\s*(?:보여\s*(?:줘|주세요)|있어요?|없어요?)|후보\s*더)\s*[?.!~]*$")
_RESET = re.compile(r"^(?:처음\s*(?:조건|추천|순서)?\s*(?:으로|대로)?|원래\s*(?:대로|조건으로|순서로)|추천\s*순\s*(?:으로|서로)?)" + _END)

_UNIT = {"킬로": "kg", "킬로그램": "kg", "그램": "g", "리터": "L", "l": "L", "미리": "ml", "미리리터": "ml"}
_SIZE_IN_QUERY = re.compile(r"\s*\d+(?:\.\d+)?\s*(?:kg|g|ml|l|리터|킬로)\b", re.IGNORECASE)
_COUNT_IN_QUERY = re.compile(r"\s*\d{1,3}\s*(?:개|팩|봉|병|입|박스|세트)(?:입)?")
_DELIVERY_LABEL = {"rocket": "로켓배송", "free_shipping": "무료배송"}


def search_max() -> int:
    try:
        return max(0, int(os.environ.get("CHAT_FOLLOWUP_SEARCH_MAX") or FOLLOWUP_SEARCH_MAX))
    except ValueError:
        return FOLLOWUP_SEARCH_MAX


FOLLOWUP_API_MAX = 40      # 이어 묻기로 다시 찾을 때 세션 전체의 실제 쿠팡 호출 수 상한 (자동 다시 찾기·더 찾기 포함)


def api_max() -> int:
    try:
        return max(0, int(os.environ.get("CHAT_FOLLOWUP_API_MAX") or FOLLOWUP_API_MAX))
    except ValueError:
        return FOLLOWUP_API_MAX


def base_set(state: dict) -> dict | None:
    """이어 물을 대상 — 직전이 쇼핑 답이고 저장된 후보 묶음이 있을 때 그 묶음."""
    if (state or {}).get("mode") != "shopping":
        return None
    seen = state.get("seen") or []
    fu = state.get("followup") or {}
    if fu.get("query"):
        for s in reversed(seen):
            if s.get("query") == fu["query"]:
                return s
    return seen[-1] if seen else None


def parse(text: str) -> dict | None:
    """짧은 조건 말 → {'kind': …, …} 또는 None."""
    t = " ".join((text or "").split())
    if not t or len(t) > 30:
        return None
    if _SORT_PER100G.match(t):
        return {"kind": "sort", "by": "per100g"}
    if _SORT_PRICE.match(t):
        return {"kind": "sort", "by": "price"}
    if _ROCKET.match(t):
        return {"kind": "filter", "field": "rocket"}
    if _FREE_SHIP.match(t):
        return {"kind": "filter", "field": "free_shipping"}
    if _GIFT.match(t):
        return {"kind": "gift"}
    if _MORE.match(t):
        return {"kind": "more"}
    if _RESET.match(t):
        return {"kind": "reset"}
    if m := _SIZE.match(t):
        unit = _UNIT.get(m["unit"].lower(), _UNIT.get(m["unit"], m["unit"].lower()))
        return {"kind": "size", "value": f"{m['num']}{unit}"}
    if m := _COUNT.match(t):
        return {"kind": "count", "value": f"{m['num']}{m['unit']}"}
    if m := _EXCLUDE.match(t):
        word = m["word"]
        if word in ("그거", "그것", "이거", "이것", "저거", "전부", "다"):
            return None
        return {"kind": "exclude", "word": word}
    return None


def compared(cards: list[dict]) -> list[dict]:
    """같은 기준으로 견준 후보만 (업체 제공·냉동·더 찾은 상품 제외), 추천 순서대로."""
    keep = [c for c in cards if not c.get("partner") and not c.get("frozen") and not c.get("more_as")]
    return sorted(keep, key=lambda c: c.get("rank") or 0)


def _price(c: dict) -> float | None:
    for k in ("total", "price"):
        v = c.get(k)
        if isinstance(v, (int, float)) and v > 0:
            return float(v)
    return None


def sort_view(cards: list[dict], by: str) -> tuple[list[dict], int]:
    """(가격 낮은 순 후보, 값이 없어 뒤로 둔 수)."""
    key = _price if by == "price" else (lambda c: c.get("per100g") if isinstance(c.get("per100g"), (int, float)) else None)
    known = sorted([c for c in cards if key(c) is not None], key=key)
    unknown = [c for c in cards if key(c) is None]
    return known + unknown, len(unknown)


def filter_view(cards: list[dict], field: str) -> list[dict]:
    return [c for c in cards if c.get(field)]


def exclude_view(cards: list[dict], word: str) -> list[dict]:
    flat = re.sub(r"\s+", "", word)
    return [c for c in cards if flat not in re.sub(r"\s+", "", c.get("title") or "")]


def research_text(kind: str, query: str, value: str | None = None) -> str:
    """양·수량·선물 — 새로 찾을 말."""
    q = " ".join((query or "").split())
    if kind == "size":
        return f"{_SIZE_IN_QUERY.sub('', q).strip()} {value}".strip()
    if kind == "count":
        return f"{_COUNT_IN_QUERY.sub('', q).strip()} {value}".strip()
    if kind == "gift":
        return q if "선물" in q else f"{q} 선물세트"
    return q


def describe(intent: dict) -> str:
    kind = intent["kind"]
    if kind == "sort":
        return "100g당 가격 낮은 순" if intent["by"] == "per100g" else "가격 낮은 순"
    if kind == "filter":
        return f"{_DELIVERY_LABEL[intent['field']]} 표시 상품만"
    if kind == "exclude":
        return f"'{intent['word']}' 빼고"
    if kind in ("size", "count"):
        return intent["value"]
    if kind == "gift":
        return "선물용"
    if kind == "more":
        return "더 찾아보기"
    return "처음 조건"


VIEW_KINDS = ("sort", "filter", "exclude")


def merge_cond(conds: list[dict], intent: dict) -> list[dict]:
    """보기 조건 쌓기 — 정렬은 하나(새 것으로 바꿈), 배송 표시는 칸별 하나, 빼기 말은 모아 둔다."""
    out = [c for c in conds or [] if not (
        (intent["kind"] == "sort" and c["kind"] == "sort")
        or (intent["kind"] == "filter" and c["kind"] == "filter" and c["field"] == intent["field"])
        or (intent["kind"] == "exclude" and c["kind"] == "exclude" and c["word"] == intent["word"]))]
    return out + [intent]


def apply_conds(cards: list[dict], conds: list[dict]) -> tuple[list[dict], int, dict | None]:
    """(조건에 맞는 후보, 정렬 값이 없어 뒤로 둔 수, 정렬 조건) — 거르기·빼기 뒤 정렬. 정렬이 없으면 추천 순서 그대로."""
    view = list(cards)
    sort = None
    for c in conds or []:
        if c["kind"] == "filter":
            view = filter_view(view, c["field"])
        elif c["kind"] == "exclude":
            view = exclude_view(view, c["word"])
        elif c["kind"] == "sort":
            sort = c
    unknown = 0
    if sort:
        view, unknown = sort_view(view, sort["by"])
    return view, unknown, sort


def describe_conds(conds: list[dict]) -> str:
    return " · ".join(describe(c) for c in conds or [])


def chips_after(cards: list[dict], *, more_left: bool, changed: bool) -> list[str]:
    """쇼핑 답 끝 칩 — 누르면 그 말을 보낸다 (parse 가 받는 말만)."""
    base = compared(cards)
    out = []
    if changed:
        out.append("처음 조건으로")
    if len(base) >= 3:
        out.append("가격 낮은 순으로")
    if any(c.get("rocket") for c in base) and not all(c.get("rocket") for c in base):
        out.append("로켓배송만")
    if more_left:
        out.append("더 찾아보기")
    return out


__all__ = ["parse", "base_set", "compared", "sort_view", "filter_view", "exclude_view", "research_text", "describe",
           "chips_after", "search_max", "merge_cond", "apply_conds", "describe_conds", "VIEW_KINDS", "api_max", "FOLLOWUP_SEARCH_MAX", "RESEARCH_KINDS"]
