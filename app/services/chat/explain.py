"""'왜 이 상품인가' — 추천 사유를 계산으로만 만든다 (2026-11-01).

검색 결과를 순서대로 보여 주면 판매처 검색과 다를 게 없다.  후보 전체를 같은 기준으로 견준 뒤
역할이 다른 상품을 하나씩 고른다:

    value  가성비     100g당(또는 개당) 가격이 가장 낮은 상품 — 비교할 양이 없으면 '최저가'
    fast   빠른 배송  판매처가 '로켓배송'으로 표시한 상품 중 가장 저렴한 것
    ample  넉넉한 양  용량이 가장 큰 상품 (가성비 상품보다 30% 이상 많을 때만)
    gift   선물용     선물을 찾는 말이 있고, 상품명에 선물세트 등의 표기가 있을 때 (판매자 표기)
    alt    다른 선택  역할이 겹쳐 빈자리를 채우는 후보

사유(why)의 근거(basis)는 셋 중 하나다 — 화면은 이 구분을 그대로 보여 준다.
    calc  우리가 후보끼리 계산한 값 (상품명 표기 중량·판매가 기준)
    mall  판매처 API가 준 표시 (로켓배송·무료배송)
    you   고객이 말한 조건 (예산)

판매자 문구(고당도·1++·국내산 …)는 사유·순서에 쓰지 않고 seller_claims 로만 따로 내려 보낸다.
평점·후기·도착일은 쿠팡·네이버 검색 API가 주지 않는다 → 만들지 않고 판매처 확인 안내(check_at_mall).
"""
from __future__ import annotations

import hashlib
import re

from app.services.chat.budget import fits

# app.admin.shared.markets.base.parse_units 와 같은 규칙 — 대화 서비스가 관리자 패키지(pydantic)를 불러오지 않도록 옮겨 둠
_UNIT_RE = re.compile(r"(\d+)\s*(?:개입|개|입|팩|봉|구)\b")
# 2026-11-11: '\b' 대신 '영문자가 뒤따르지 않음' — '4kg내외'·'10kg박스'처럼 한글이 바로 붙어도 읽는다
_WEIGHT_RE = re.compile(r"(\d+(?:\.\d+)?)\s*(kg|g)(?![A-Za-z])", re.IGNORECASE)


# 2026-11-12: 포장 단위 수량 — 쉼표 앞뒤('1kg, 2개' · '2개, 1kg') 또는 바로 뒤('100g 10팩').  낱알 수(입·구·과)는 제외
_PACK = r"(?:개|팩|봉지|봉|박스|상자|병|캔|통|EA|ea)(?![가-힣A-Za-z\d])"
_PAREN = r"(?:\s*\([^)]*\))?"
# 쉼표 없이 바로 붙은 수('100g 10팩')는 포장 단위만 — '사과 3kg 10개'의 '개'는 낱알일 수 있어 곱하지 않는다
_BOX = r"(?:팩|봉지|봉|박스|상자|병|캔|통)(?![가-힣A-Za-z\d])"


def _pack_matches(text: str, unit: str, conv) -> list[tuple[float, str, tuple[int, int]]]:
    """[(총량, '1kg×2', span)] — 수량이 2 이상인 것만."""
    after = re.compile(r"(\d+(?:\.\d+)?)\s*" + unit + r"(?![A-Za-z])" + _PAREN
                       + r"(?:\s*,\s*(\d+)\s*" + _PACK + r"|\s*(\d+)\s*" + _BOX + ")", re.IGNORECASE)
    before = re.compile(r"(?<![\d.])(\d+)\s*" + _PACK + r"\s*,\s*(\d+(?:\.\d+)?)\s*" + unit + r"(?![A-Za-z])", re.IGNORECASE)
    out = []
    for m in after.finditer(text):
        each, n = conv(m.group(1), m.group(2)), int(m.group(3) or m.group(4))
        out.append((each, n, m.span()))
    for m in before.finditer(text):
        if any(a <= m.start() < b or a < m.end() <= b for _, _, (a, b) in out):
            continue
        each, n = conv(m.group(2), m.group(3)), int(m.group(1))
        out.append((each, n, m.span()))
    fmt = _wtext if conv is _grams else _vtext
    return [(each * n, f"{fmt(each)}×{n}", span) for each, n, span in out if n >= 2]

_MULTIPLY_RE = re.compile(r"(\d+(?:\.\d+)?)\s*(kg|g)\s*[x×X*]\s*(\d+(?:\.\d+)?)(?!\s*(?:kg|g)(?![A-Za-z]))", re.IGNORECASE)
# 2026-11-03 p34: 곱한 수 뒤에 또 곱하기가 이어지면('500g × 2팩 × 3세트') 일부만 계산하지 않는다
_CHAINED_RE = re.compile(r"\s*[가-힣A-Za-z]{0,4}\s*[x×X*]\s*\d")

# 2026-11-11: 증정분 — '3kg+1kg', '5kg (+500g 증정)', '1kg 증정', '1+1'.  옵션 목록과 다르게 "증정분이 있어요"로 알린다.
#   증정분이 실제로 함께 오는지(선착순·조건)는 상품명만으로 알 수 없어 100g당은 계산하지 않는다.
_BONUS_PLUS_RE = re.compile(r"(\d+(?:\.\d+)?)\s*(kg|g)\s*\(?\s*\+\s*(\d+(?:\.\d+)?)\s*(kg|g)(?![A-Za-z])", re.IGNORECASE)
_BONUS_WORD_RE = re.compile(
    r"(?:(?:증정|덤|서비스|추가\s*증정)\s*(\d+(?:\.\d+)?)\s*(kg|g)(?![A-Za-z])|(\d+(?:\.\d+)?)\s*(kg|g)\s*\)?\s*(?:증정|덤|더\s*드림|서비스|추가\s*증정))",
    re.IGNORECASE)
_BONUS_COUNT_RE = re.compile(r"(?<![\d.])([1-9])\s*\+\s*([1-9])(?![\d.])(?!\s*(?:kg|g)(?![A-Za-z]))", re.IGNORECASE)


def _bonus(text: str) -> dict | None:
    """증정분 표기 → {'base': '3kg'|None, 'extra': '1kg'|None, 'count': '1+1'|None}"""
    m = _BONUS_PLUS_RE.search(text)
    if m:
        return {"base": _wtext(_grams(m.group(1), m.group(2))), "extra": _wtext(_grams(m.group(3), m.group(4))),
                "count": None}
    m = _BONUS_WORD_RE.search(text)
    if m:
        amount, unit = (m.group(1), m.group(2)) if m.group(1) else (m.group(3), m.group(4))
        extra = _grams(amount, unit)
        others = [_grams(a, u) for a, u in _WEIGHT_RE.findall(text) if round(_grams(a, u), 6) != round(extra, 6)]
        return {"base": _wtext(others[0]) if others else None, "extra": _wtext(extra), "count": None}
    m = _BONUS_COUNT_RE.search(text)
    if m:
        return {"base": None, "extra": None, "count": f"{m.group(1)}+{m.group(2)}"}
    return None


def _grams(amount: str, unit: str) -> float:
    return float(amount) * (1000 if unit.lower() == "kg" else 1)


def _wtext(g: float) -> str:
    return f"{g / 1000:g}kg" if g >= 1000 else f"{g:g}g"


def parse_weight(title: str) -> dict:
    """상품명에서 중량(g)을 읽고, 어떻게 읽었는지 함께 돌려준다 (2026-11-03 p32).

    kind:
      'single'     중량 표기가 하나 (같은 값이 반복돼도 하나)          → weight = 그 값
      'multiplied' '500g x 2팩'처럼 곱하기가 명시됨                   → weight = 500 × 2, formula = '500g×2'
      'ambiguous'  서로 다른 중량이 2개 이상 ('5kg 10kg' 옵션 목록 등) → weight = None (어느 옵션 가격인지 모름)
      'count_unclear' 낱알 수·개입이 붙음 ('500g 10개입') → weight = None (개당·전체 불명, p33)
                    2026-11-12 사용자 결정: 포장 단위 수('1kg, 2개'·'2개, 1kg'·'100g 10팩')는 곱한다 → multiplied
      'multiply_unclear' 소수 수량·여러 번 곱하기 ('500g × 2.5팩', '500g × 2팩 × 3세트') → weight = None (p34)
      'none'       중량 표기 없음                                     → weight = None
      'bonus'      증정분 표기 ('3kg+1kg', '1kg 증정', '1+1')           → weight = None, bonus = {...} (2026-11-11)
    곱하기 결과와 나머지 표기가 모두 같은 값이면('500g x 2 총 1kg') 그 값으로 본다."""
    text = title or ""
    bonus = _bonus(text)
    if bonus:
        found = [_wtext(_grams(a, u)) for a, u in _WEIGHT_RE.findall(text)] + ([bonus["count"]] if bonus["count"] else [])
        return {"weight": None, "kind": "bonus", "formula": None, "found": found, "bonus": bonus}
    totals, formulas, spans = [], [], []
    for m in _MULTIPLY_RE.finditer(text):
        # p34: 소수 수량('× 2.5팩')·여러 번 곱하기('× 2팩 × 3세트')는 지원하지 않음 → 일부만 계산하지 않고 보류
        if "." in m.group(3) or _CHAINED_RE.match(text, m.end()):
            return {"weight": None, "kind": "multiply_unclear", "formula": None,
                    "found": [re.sub(r"\s+", "", text[m.start():m.end() + 12]).strip()]}
        each, count = _grams(m.group(1), m.group(2)), int(m.group(3))
        if count >= 1:
            totals.append(each * count)
            formulas.append(f"{_wtext(each)}×{count}")
            spans.append(m.span())
    pack_used = False
    for total, formula, span in _pack_matches(text, r"(kg|g)", _grams):   # 2026-11-12: '1kg, 2개' → 2kg
        if not any(a0 <= span[0] < b0 for a0, b0 in spans):
            totals.append(total)
            formulas.append(formula)
            spans.append(span)
            pack_used = True
    eaches = {round(t / int(f.rsplit("×", 1)[1]), 6) for t, f in zip(totals, formulas)}
    singles = [_grams(a, u) for m in _WEIGHT_RE.finditer(text)
               if not any(a0 <= m.start() < b0 for a0, b0 in spans)
               for a, u in [m.groups()]]
    # 2026-11-13: 곱한 식의 한 개 크기를 상품명에 한 번 더 적은 것('180g, 180g, 18개')은 같은 표기 — 옵션 목록으로 보지 않음
    singles = [v for v in singles if round(v, 6) not in eaches]
    values = totals + singles
    found = [_wtext(v) for v in values]
    if not values:
        return {"weight": None, "kind": "none", "formula": None, "found": []}
    if len({round(v, 6) for v in values}) > 1:
        if pack_used:   # 옵션 목록 근거에는 상품명에 적힌 그대로의 중량을 남긴다 (곱한 값 아님)
            found = [_wtext(_grams(a, u)) for a, u in _WEIGHT_RE.findall(text)]
        return {"weight": None, "kind": "ambiguous", "formula": None, "found": found}
    if totals:
        return {"weight": totals[0], "kind": "multiplied", "formula": formulas[0], "found": found}
    # 2026-11-03 p33: '100g 10팩'처럼 곱하기 표시 없이 개수가 붙으면 개당 중량인지 전체 중량인지 모른다 → 쓰지 않음
    count = _UNIT_RE.search(text)
    if count and int(count.group(1)) > 1:
        return {"weight": None, "kind": "count_unclear", "formula": None,
                "found": found + [count.group(0).replace(" ", "")]}
    return {"weight": values[0], "kind": "single", "formula": None, "found": found}


def parse_units(title: str) -> tuple[int | None, float | None]:
    """상품명에서 개입 수·중량(g)을 읽는다 (상품명 표기 그대로).
    2026-11-03 p32: 중량은 parse_weight 규칙 — 옵션 목록처럼 중량이 여러 개면 None, '500g x 2'는 1000."""
    m = _UNIT_RE.search(title or "")
    unit = int(m.group(1)) if m else None
    return unit, parse_weight(title)["weight"]


# 2026-11-12: 액체 용량 — 100ml당 가격.  중량(g)과는 섞지 않는다 (밀도가 상품마다 달라 g=ml 로 보지 않음).
_VOL_UNIT = r"(ml|mL|ML|l|L|리터)"
_VOLUME_RE = re.compile(r"(\d+(?:\.\d+)?)\s*" + _VOL_UNIT + r"(?![A-Za-z])")
_VOL_MULTIPLY_RE = re.compile(r"(\d+(?:\.\d+)?)\s*" + _VOL_UNIT + r"\s*[x×X*]\s*(\d+)(?![\d.])(?!\s*" + _VOL_UNIT + ")")
# '용량, 수량'('190ml, 12개')·'용량 수량'('500ml 20병')은 _pack_matches 로 계산 (중량과 같은 규칙)


def _ml(amount: str, unit: str) -> float:
    return float(amount) * (1 if unit.lower() == "ml" else 1000)


def _vtext(ml: float) -> str:
    return f"{ml / 1000:g}L" if ml >= 1000 else f"{ml:g}ml"


def parse_volume(title: str) -> dict:
    """상품명에서 용량(ml)을 읽는다 — parse_weight 와 같은 원칙.
    kind: single · multiplied('1L x 2', '190ml, 12개') · ambiguous(서로 다른 용량 여러 개) · count_unclear('200ml 24팩')
          · bonus('1+1') · has_weight(중량 표기가 있으면 용량은 쓰지 않음) · none"""
    text = title or ""
    if _WEIGHT_RE.search(text):
        return {"volume": None, "kind": "has_weight", "formula": None, "found": []}
    vols = list(_VOLUME_RE.finditer(text))
    if not vols:
        return {"volume": None, "kind": "none", "formula": None, "found": []}
    if _BONUS_COUNT_RE.search(text):
        return {"volume": None, "kind": "bonus", "formula": None, "found": [_vtext(_ml(*m.groups())) for m in vols]}
    totals, formulas, spans = [], [], []
    for m in _VOL_MULTIPLY_RE.finditer(text):
        each, count = _ml(m.group(1), m.group(2)), int(m.group(3))
        if count >= 1:
            totals.append(each * count)
            formulas.append(f"{_vtext(each)}×{count}")
            spans.append(m.span())
    for total, formula, span in _pack_matches(text, _VOL_UNIT, _ml):
        if not any(a <= span[0] < b for a, b in spans):
            totals.append(total)
            formulas.append(formula)
            spans.append(span)
    eaches = {round(t / int(f.rsplit("×", 1)[1]), 6) for t, f in zip(totals, formulas)}
    singles = [_ml(*m.groups()) for m in vols if not any(a <= m.start() < b for a, b in spans)]
    singles = [v for v in singles if round(v, 6) not in eaches]   # 2026-11-13: '180ml, 180ml, 18개' 같은 반복 표기
    values = totals + singles
    found = [_vtext(v) for v in values]
    if len({round(v, 6) for v in values}) > 1:
        return {"volume": None, "kind": "ambiguous", "formula": None, "found": found}
    if totals:
        return {"volume": totals[0], "kind": "multiplied", "formula": formulas[0], "found": found}
    count = _UNIT_RE.search(text)
    if count and int(count.group(1)) > 1:
        return {"volume": None, "kind": "count_unclear", "formula": None,
                "found": found + [count.group(0).replace(" ", "")]}
    return {"volume": values[0], "kind": "single", "formula": None, "found": found}


VOLUME_KEYS = ("volume_ml", "volume_formula", "per100ml")


def _set_volume(card: dict, weight) -> dict:
    """중량을 쓰지 않은 카드에만 용량·100ml당을 붙인다. 용량이 없으면 키를 두지 않는다(기존 응답 모양 유지)."""
    for k in VOLUME_KEYS:
        card.pop(k, None)
    if weight or card.get("weight_source") in UNUSABLE_SOURCES:
        return card
    pv = parse_volume(card.get("title") or "")
    vol = pv["volume"] if pv["volume"] and 1 <= pv["volume"] <= 200_000 else None
    if vol:
        basis = _basis(card)
        card.update(volume_ml=vol, volume_formula=pv["formula"], per100ml=round(basis / vol * 100) if basis else None)
    return card


def weight_note(title: str) -> dict | None:
    """상세페이지를 열기 전에 알 수 있게 — 중량 옵션·증정분 안내 (2026-11-11).
    {'kind': 'options'|'bonus', 'label': '중량 옵션이 있어요', 'detail': '2kg · 5kg · 10kg'}"""
    parsed = parse_weight(title or "")
    if parsed["kind"] == "ambiguous":
        return {"kind": "options", "label": "중량 옵션이 있어요", "detail": " · ".join(dict.fromkeys(parsed["found"]))}
    if parsed["kind"] == "bonus":
        b = parsed["bonus"]
        if b["count"]:
            detail = f"{b['count']} 구성"
        elif b["base"]:
            detail = f"{b['base']} + {b['extra']} 증정"
        else:
            detail = f"{b['extra']} 증정"
        return {"kind": "bonus", "label": "증정분이 있어요", "detail": detail}
    return None


# 2026-11-11: 냉동 상품 — 생과·생물과 쓰임새가 달라 같은 기준(100g당·가성비)으로 견주지 않는다.
# '무냉동'·'비냉동'·'냉동 아님'·'냉동실 보관'은 냉동 상품이 아니다.
_FROZEN_RE = re.compile(r"(?<![무비])냉동(?!\s*(?:아님|안\s*함|X(?![A-Za-z])|x(?![A-Za-z])|실|보관))")


def is_frozen(title: str) -> bool:
    return bool(_FROZEN_RE.search(title or ""))


def wants_frozen(text: str) -> bool:
    """고객이 냉동을 찾을 때는 나누지 않는다 ('냉동 블루베리', '냉동 딸기 추천')."""
    return "냉동" in (text or "")


WEIGHT_SOURCE = {"single": "title", "multiplied": "title_multiplied", "ambiguous": "title_ambiguous", "bonus": "title_bonus",
                 "count_unclear": "title_count_unclear", "multiply_unclear": "title_multiply_unclear"}
UNUSABLE_TITLE_KINDS = ("ambiguous", "bonus", "count_unclear", "multiply_unclear")   # 중량 표기는 있으나 총중량 확정 불가
UNUSABLE_SOURCES = tuple(WEIGHT_SOURCE[k] for k in UNUSABLE_TITLE_KINDS)

# 2026-11-03 p39: 개수의 적용 범위가 불명확한 표기 — 개당 가격을 계산하지 않는다.
#   'ambiguous'(옵션 목록 '1kg … 2개, 500g')·'multiply_unclear'(소수·여러 번 곱하기)는 가격이 어느 구성의 것인지 모른다.
#   개수 표기가 서로 다른 값으로 여러 개('2개 … 3개')여도 같다.
#   'count_unclear'('100g 10팩')는 중량이 개당인지 전체인지가 불명확할 뿐, 개수는 상품명에 하나로 적혀 있어 개당 가격은 계산한다.
UNIT_UNCLEAR_KINDS = ("ambiguous", "bonus", "multiply_unclear")


def unit_scope(title: str) -> dict:
    """개수의 적용 범위 판정: {'clear': bool, 'found': [표기들]} (p39)."""
    text = title or ""
    counts = [m.group(0).replace(" ", "") for m in _UNIT_RE.finditer(text)]
    parsed = parse_weight(text)
    distinct = {int(m.group(1)) for m in _UNIT_RE.finditer(text)}
    clear = parsed["kind"] not in UNIT_UNCLEAR_KINDS and len(distinct) <= 1
    return {"clear": clear, "found": parsed["found"] + [c for c in counts if c not in parsed["found"]]}


def per_unit_price(card: dict, unit: int | None) -> int | None:
    """개당 가격 — 개수가 2 이상이고 적용 범위가 분명할 때만 (p39)."""
    basis = _basis(card)
    if not (unit and unit > 1 and basis):
        return None
    return round(basis / unit) if unit_scope(card.get("title") or "")["clear"] else None


ROLE_LABEL = {"value": "가성비", "lowest": "최저가", "fast": "빠른 배송", "ample": "넉넉한 양",
              "gift": "선물용", "sweet": "당도 표기", "house": "가정용 양", "alt": "다른 선택"}
MAX_PICKS = 4

_CLAIMS = (
    # 2026-11-12: 당도 문구는 모두 판매자 주장 — '고당도'뿐 아니라 당도선별·비파괴·브릭스 숫자·당도 보장까지 한 표기로
    ("당도 표기", re.compile(r"고당도|꿀\s*당도|당도\s*(?:선별|보장|\d+)|비파괴|광센서|"
                             r"(?<![\d.])\d{1,2}(?:\.\d)?\s*(?:brix|브릭스|bx)(?![a-z])", re.I)),
    ("맛 보장·환불 표기", re.compile(r"맛없으면\s*(?:100%\s*)?환불|맛\s*보장|환불\s*보장")),
    ("등급 표기", re.compile(r"1\+\+|1\+\s*등급|투뿔|1등급|특등급")),
    ("국내산 표기", re.compile(r"국내산|(?<![가-힣])국산(?!화)|우리\s*농산물")),
    ("평점 표기", re.compile(r"평점\s*\d|별점\s*\d|만족도\s*\d|리뷰\s*\d|후기\s*\d")),
    ("산지직송", re.compile(r"산지\s*직송|산지직배송|농장\s*직송")),
    ("프리미엄", re.compile(r"프리미엄|명품|최상급|특상|특품|로얄")),
    ("유기농·무농약", re.compile(r"유기농|무농약|친환경|무항생제")),
    ("선물용·세트 표기", re.compile(r"선물\s*세트|선물세트|선물용|보자기|선물\s*포장|쇼핑백")),
    # 2026-11-04: '흠과 혼합 10kg'처럼 품질 등급을 낮춘 표기도 고객이 알아야 할 판매자 표기로 보여 준다
    ("흠과·못난이 표기", re.compile(r"흠과|못난이|B급|비품|파지|상처\s*과|가정용\s*혼합")),
    ("HACCP", re.compile(r"HACCP|해썹", re.I)),
)
_BLEMISH = re.compile(r"흠과|못난이|B급|비품|파지|상처\s*과|가정용\s*혼합")   # 판매자 표기 '흠과·못난이'와 같은 말
_GIFT_TITLE = re.compile(r"선물\s*세트|선물세트|선물용|명절|보자기|쇼핑백|선물\s*포장")
_GIFT_ASK = re.compile(r"선물|부모님|명절|추석|설날|답례|집들이|어버이")


def won(v: int | float | None) -> str:
    return "미확인" if v is None else f"{int(round(v)):,}원"


def card_key(card: dict) -> str:
    # p46: UCP 카드는 판매자 옵션 출처(호스트·상품·옵션 ID)로 — 상품명이 바뀌어도 같은 옵션이면 같은 key
    u = card.get("ucp") if isinstance(card.get("ucp"), dict) else None
    if u and u.get("host") and (u.get("variant_id") or u.get("product_id")):
        raw = f"ucp|{u['host']}|{u.get('product_id') or ''}|{u.get('variant_id') or ''}"
    else:
        raw = "|".join(str(card.get(k) or "") for k in ("mall", "pid", "url", "title"))
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]


def seller_claims(title: str) -> list[str]:
    return [label for label, rx in _CLAIMS if rx.search(title or "")]


def trust_upstream_weight() -> bool:
    """상위 결과의 weight_g(DB 대체 경로 snapshot)를 중량으로 쓸지 (2026-11-03 p31, p33).
    기본은 끔.  켜도(CHAT_TRUST_UPSTREAM_WEIGHT=1) 행별로 상품·옵션·가격 연결을 확인했다는 표시
    (item['weight_verified'] is True)가 있는 값만 쓴다 — 원천 단위 일괄 허용은 하지 않는다."""
    import os

    return (os.getenv("CHAT_TRUST_UPSTREAM_WEIGHT") or "0").strip() == "1"


def _amount(card: dict, item: dict) -> tuple[float | None, int | None, str | None]:
    """(중량 g, 개입 수, 중량 출처).  출처: 'title'(상품명 표기) · 'upstream'(상위 weight_g) · None."""
    unit, _w = parse_units(card.get("title") or "")
    parsed = parse_weight(card.get("title") or "")
    w2 = parsed["weight"]
    weight, source = None, None
    # 2026-11-03 p33: 설정을 켜도 행별로 확인 표시(weight_verified=True)가 있는 값만 쓴다 — 일괄 복구 방지
    if trust_upstream_weight() and item.get("weight_verified") is True:
        try:
            up = item.get("weight_g")
            weight = float(up) if up not in (None, "") else None
        except (TypeError, ValueError):
            weight = None
        source = "upstream" if weight else None
    if not weight and w2:
        weight, source = w2, WEIGHT_SOURCE[parsed["kind"]]
    elif not weight and parsed["kind"] in UNUSABLE_TITLE_KINDS:
        source = WEIGHT_SOURCE[parsed["kind"]]   # 중량을 쓰지 않음 — 근거에 이유(옵션 목록·개수 불명)를 남긴다
    if weight is not None and not (1 <= weight <= 200_000):
        weight, source = None, None
    return weight, unit, source


def _basis(card: dict) -> int:
    return card["total"] if card.get("total") is not None else card.get("price") or 0


def _flag(item: dict, *names) -> bool | None:
    for n in names:
        v = item.get(n)
        if isinstance(v, bool):
            return v
    return None


# 2026-11-13 배송비 원칙(설계 v2, 사용자 11-11 결정): 배송비는 멤버십·주문 금액·판매 업체·배송지에 따라 달라 검색 단계에서
#   확정하지 않는다. 상태로만 기록한다 —
#     confirmed  주문 단계에서 판매자가 배송지 기준으로 계산한 금액 (지금은 이런 출처 없음 — 자리만 둔다)
#     free_label 판매처가 '무료배송'이라고 표시 (조건은 모름 — 0원으로 바꾸지 않음)
#     fee_label  판매처·업체가 적은 배송비 금액 (주문 때 달라질 수 있음)
#     unknown    정보 없음
#   총액(total)은 confirmed 일 때만. 최저가·예산·100g당은 그 외에는 상품가 기준.
SHIPPING_STATUSES = ("confirmed", "free_label", "fee_label", "unknown")


def shipping_fields(card: dict, free: bool | None) -> dict:
    """card 의 shipping_fee·free 표시로 {shipping_status, shipping_fee, total} 을 정한다."""
    if card.get("shipping_status") == "confirmed" and card.get("total") is not None:
        return {"shipping_status": "confirmed", "shipping_fee": card.get("shipping_fee"), "total": card["total"]}
    fee = card.get("shipping_fee")
    try:
        fee = None if fee in (None, "") else int(float(fee))
    except (TypeError, ValueError):
        fee = None
    if free is True or fee == 0:          # 예전 저장 카드(무료 표시를 0원으로 바꿔 둔 것)도 여기로
        return {"shipping_status": "free_label", "shipping_fee": None, "total": None}
    if fee is not None and fee > 0:
        return {"shipping_status": "fee_label", "shipping_fee": fee, "total": None}
    return {"shipping_status": "unknown", "shipping_fee": None, "total": None}


def shipping_note(card: dict) -> str:
    """예산·비교 문구 뒤에 붙이는 배송비 상태 한 마디."""
    st = card.get("shipping_status") or "unknown"
    if st == "free_label":
        return "무료배송 표시 (조건은 판매처에서 확인)"
    if st == "fee_label" and card.get("shipping_fee"):
        return f"배송비 {won(card['shipping_fee'])} 표시 (주문 때 확인)"
    return "배송비는 미확인"


def enrich(card: dict, item: dict) -> dict:
    """사실만 붙인다: 키 · 중량/개수 · 100g당 · 로켓/무료배송 표시 · 판매자 문구 · 판매처 확인 안내."""
    weight, unit, weight_source = _amount(card, item)
    rocket = _flag(item, "is_rocket", "isRocket")
    free = _flag(item, "is_free_shipping", "isFreeShipping")
    card.update(shipping_fields(card, free))   # 2026-11-13: 무료배송 표시를 0원·총액으로 바꾸지 않는다
    card.update(
        key=card_key(card),
        weight_g=weight,
        weight_source=weight_source,           # 2026-11-03 p31: 실제로 쓴 중량의 출처 (화면 응답에는 안 나감)
        # p34: 상위 중량을 썼을 때 그 근거(행별 확인 표시) — 저장 후보를 다시 고를 때 같은 조건을 다시 적용
        weight_verified=True if weight_source == "upstream" else None,
        # 2026-11-03 p32: 상품명에서 읽은 방식 (계산식·여러 중량) — 사유 문구·근거용, 화면 응답에는 안 나감
        weight_formula=parse_weight(card.get("title") or "")["formula"] if weight_source == "title_multiplied" else None,
        weight_found=(parse_weight(card.get("title") or "")["found"]
                      if weight_source in UNUSABLE_SOURCES else None),
        unit_count=unit,
        per100g=round(_basis(card) / weight * 100) if weight and _basis(card) else None,
        per_unit=per_unit_price(card, unit),   # p39: 개수 적용 범위가 불명확하면 None
        rocket=rocket,
        free_shipping=free,
        seller_claims=seller_claims(card.get("title") or ""),
        weight_note=weight_note(card.get("title") or ""),   # 2026-11-11: 중량 옵션·증정분 안내 (화면에 나감)
        check_at_mall=True,
        delivery_hint="로켓배송 표시" if rocket else ("무료배송 표시" if free else None),
    )
    _set_volume(card, weight)
    return _blocked(card)


def _blocked(card: dict) -> dict:
    """p45: 가격 비교 금지 카드(UCP 판매자 단위가격 등)는 상품명으로 중량·100g당·개당을 다시 채우지 않는다.
    p47: 상품명 개수(unit_count)도 비운다 — 공통 모델 근거에서 '상품명 표기 기준 비교 허용'으로 나가지 않게."""
    if card.get("price_compare_blocked"):
        card.update(weight_g=None, per100g=None, per_unit=None, weight_source=None, weight_formula=None,
                    weight_found=None, unit_count=None, weight_note=None)
        for k in VOLUME_KEYS:
            card.pop(k, None)
    return card


def reweigh(card: dict) -> dict:
    """저장 카드의 중량을 지금 규칙으로 다시 계산한 사본 (p31, p32 보완).
    출처 기록이 없거나(p31 이전) 상품명에서 읽은 중량이면 상품명으로 다시 계산한다 — 상품명 해석 규칙이 바뀌어도
    (p32: 옵션 목록·곱하기) 예전 값이 남지 않게.  상위 weight_g('upstream')로 기록된 카드는 지금도 허용 조건
    (CHAT_TRUST_UPSTREAM_WEIGHT=1 + weight_verified)을 만족할 때만 그대로 두고, 아니면 상품명으로 다시 계산한다 (p34)."""
    # p34: 저장된 상위 중량도 지금의 허용 조건(설정 켬 + 행별 확인 표시)을 다시 확인한다 — 아니면 상품명으로 재계산
    if not card.get("shipping_status") and (card.get("free_shipping") is True or card.get("shipping_fee") == 0):
        card = dict(card, **shipping_fields(card, card.get("free_shipping")))   # 2026-11-13: 예전 저장 카드의 '무료=0원' 정리
    if card.get("weight_source") == "upstream" and trust_upstream_weight() and card.get("weight_verified") is True:
        return card
    unit, w = parse_units(card.get("title") or "")
    parsed = parse_weight(card.get("title") or "")
    weight = w if w is not None and 1 <= w <= 200_000 else None
    source = WEIGHT_SOURCE.get(parsed["kind"]) if (weight or parsed["kind"] in UNUSABLE_TITLE_KINDS) else None
    out = dict(card, weight_g=weight, weight_source=source, unit_count=unit, weight_verified=None,
               weight_formula=parsed["formula"] if source == "title_multiplied" else None,
               weight_found=parsed["found"] if source in UNUSABLE_SOURCES else None)
    basis = _basis(out)
    out["per100g"] = round(basis / weight * 100) if weight and basis else None
    out["per_unit"] = per_unit_price(out, unit)   # p39: 저장 카드의 예전 개당 가격도 남기지 않는다
    out["weight_note"] = weight_note(card.get("title") or "")   # 2026-11-11
    _set_volume(out, weight)                                     # 2026-11-12: 액체 100ml당
    return _blocked(out)


def _weight_text(g: float) -> str:
    return f"{g / 1000:g}kg" if g >= 1000 else f"{g:g}g"


def _alt_text(c: dict, ref: dict | None) -> str:
    """'다른 선택'의 사유 (2026-11-04): 양이 다른 상품끼리 총액만 견주면 '10kg보다 56,100원 저렴'처럼 오해가 생긴다.
    둘 다 중량 표기가 있으면 100g당으로, 같은 중량이면 총액으로, 아니면 견줄 수 없다고 말한다."""
    if ref is None:
        return "다른 구성으로 비교해 볼 만한 후보예요"
    label = ROLE_LABEL[ref["role"]]
    if c.get("per100g") and ref.get("per100g"):
        diff = c["per100g"] - ref["per100g"]
        if not diff:
            return f"{label} 상품과 100g당 가격이 같아요 ({won(c['per100g'])}/100g)"
        return f"100g당 {won(c['per100g'])}으로 {label} 상품보다 100g당 {won(abs(diff))} {'비싸요' if diff > 0 else '저렴해요'}"
    if c.get("per100ml") and ref.get("per100ml"):
        diff = c["per100ml"] - ref["per100ml"]
        if not diff:
            return f"{label} 상품과 100ml당 가격이 같아요 ({won(c['per100ml'])}/100ml)"
        return f"100ml당 {won(c['per100ml'])}으로 {label} 상품보다 100ml당 {won(abs(diff))} {'비싸요' if diff > 0 else '저렴해요'}"
    if c.get("weight_g") and c.get("weight_g") == ref.get("weight_g"):
        diff = _basis(c) - _basis(ref)
        if diff:
            return f"같은 중량인 {label} 상품보다 {won(abs(diff))} {'비싸요' if diff > 0 else '저렴해요'}"
    return "상품명에 중량·용량 표기가 없어 양 기준 가격은 견주지 못했어요 · 판매처에서 양을 확인해 주세요"


# 2026-11-12 사용자 결정 — 가정 기준 양: 과일·채소·식료품은 가정에서 1~2kg 수준, 10kg 등은 식당·업소용.
#   대용량은 고객이 요청할 때만 함께 견준다. 요청이 없으면 추천(역할)에서 빼고 '다른 후보' 맨 뒤에 이유와 함께 둔다.
#   예외: 쌀·물처럼 한 번에 10~20kg 사는 품목은 기준을 따로 둔다.
BULK_G = 5000                    # 이보다 무거우면 대용량 (5kg 상자까지는 가정용으로 봄)
BULK_ML = 5000                   # 액체
BULK_EXCEPTIONS = (              # (품목 말, 중량 기준 g, 용량 기준 ml)
    (re.compile(r"(?<![가-힣])(?:쌀|백미|현미|찹쌀)(?![가-힣])|햅쌀|쌀\s*\d"), 20000, None),
    (re.compile(r"생수|먹는\s*샘물|(?<![가-힣])물(?![가-힣])|삼다수|에비앙|아이시스|백산수"), None, 24000),
    # 2026-11-13 사용자 결정(e2 사람 평가 5명 중 3명이 두 질의 모두 10kg 선택): 귤은 겨울에 상자로 산다 — 10kg 까지 가정용
    (re.compile(r"귤|밀감|만다린"), 10000, None),
)
BULK_TITLE = re.compile(r"업소용|대용량|벌크|식자재|업장용|도매용|대포장")
BULK_ASK = re.compile(r"대용량|업소|식당|가게|매장|단체|대가족|행사|급식|도매|벌크|박스\s*단위|넉넉|많이|대량")


# 2026-11-13 사용자 결정 — 1위(가성비)는 가정용 양(3kg·3L 이하)에서 고른다. 3~5kg 은 '넉넉한 양' 자리.
#   고객이 양을 직접 말했거나('귤 5kg') 대용량을 찾으면 적용하지 않는다. 쌀·물은 대용량 기준의 절반.
HOUSE_G = 3000
HOUSE_ML = 3000


def _house_limits(ask: str, title: str) -> tuple[float, float]:
    for rx, g, ml in BULK_EXCEPTIONS:
        if rx.search(ask or "") or rx.search(title or ""):
            return (g or BULK_G) / 2 if g else HOUSE_G, (ml or BULK_ML) / 2 if ml else HOUSE_ML
    return HOUSE_G, HOUSE_ML


def _amount_asked(ask: str) -> bool:
    return bool(parse_weight(ask or "")["weight"] or parse_volume(ask or "")["volume"])


# 2026-11-13 사용자 결정 — '당도 표기' 자리: 판매자가 상품명에 당도 숫자(11Brix·15brix)를 적은 상품.
#   우리가 당도를 확인하거나 보장하지 않는다 — 표기가 있다는 사실만 알린다 ('선물용' 자리가 판매자 표기로 고르는 것과 같은 방식).
#   '최대·최고 15brix'는 상한 주장이라 이 자리에 넣지 않는다. '고당도'라는 말만 있는 상품은 너무 흔해(e2 과일 후보 65%) 쓰지 않는다.
_BRIX_NUM = re.compile(r"(\d{1,2}(?:\.\d)?)\s*(?:brix|브릭스|bx)(?![a-z])", re.I)
_BRIX_CAP = re.compile(r"(?:최대|최고|max|MAX|Max)\s*$")


def brix_stated(title: str) -> str | None:
    """상품명에 적힌 당도 숫자('15') — 상한 주장('최대 15brix')은 None."""
    for m in _BRIX_NUM.finditer(title or ""):
        if not _BRIX_CAP.search((title or "")[max(0, m.start() - 4):m.start()]):
            return m.group(1)
    return None


def wants_bulk(ask: str) -> bool:
    """고객이 대용량을 찾는가 — 낱말('대용량'·'식당' …) 또는 기준보다 큰 중량·용량을 직접 말했을 때."""
    text = ask or ""
    if BULK_ASK.search(text):
        return True
    w, v = parse_weight(text)["weight"], parse_volume(text)["volume"]
    limit_g, limit_ml = _bulk_limits(text, "")
    return bool((w and w > limit_g) or (v and v > limit_ml))


def _bulk_limits(ask: str, title: str) -> tuple[float, float]:
    for rx, g, ml in BULK_EXCEPTIONS:
        if rx.search(ask or "") or rx.search(title or ""):
            return (g or BULK_G), (ml or BULK_ML)
    return BULK_G, BULK_ML


def bulk_size(card: dict, ask: str = "") -> str | None:
    """대용량이면 그 표기('10kg' · '업소용 표기'), 아니면 None.
    중량·용량을 알면 그 값으로만 판단한다('2kg 대용량'은 가정용 양 — 판매자 문구보다 표기 중량).  모를 때만 낱말로."""
    title = card.get("title") or ""
    limit_g, limit_ml = _bulk_limits(ask, title)
    if card.get("weight_g"):
        return _wtext(card["weight_g"]) if card["weight_g"] > limit_g else None
    if card.get("volume_ml"):
        return _vtext(card["volume_ml"]) if card["volume_ml"] > limit_ml else None
    m = BULK_TITLE.search(title)
    return f"{m.group(0)} 표기" if m else None


def choose(cards: list[dict], *, budget: dict | None = None, ask: str = "") -> dict:
    """역할별로 고르고 사유를 단다.

    Returns {"picks": [...], "others": [...], "pool": n, "total": n, "budget_miss": bool}
    """
    priced = [c for c in cards if (c.get("price") or 0) > 0]
    pool = [c for c in priced if fits(_basis(c), budget)]
    budget_miss = bool(budget and not budget.get("none") and priced and not pool)
    if budget_miss:          # 예산 안에 없으면: 예산에 가까운(싼) 순으로, 그렇다고 말한다
        pool = sorted(priced, key=_basis)
    # 2026-11-12: 대용량은 요청할 때만 — 가정용 후보가 하나라도 있으면 대용량은 고르지 않는다
    bulk_keys: dict[str, str] = {}
    bulk_ok = wants_bulk(ask)
    if not bulk_ok:
        bulk_keys = {c["key"]: s for c in pool if (s := bulk_size(c, ask))}
        if bulk_keys and len(bulk_keys) < len(pool):
            pool = [c for c in pool if c["key"] not in bulk_keys]
        else:
            bulk_keys = {}   # 전부 대용량이면 빼지 않는다 (보여 줄 것이 없어지지 않게)
    # 2026-11-13 (e2 사람 평가 '부모님 선물 사과'): 선물을 찾는데 '못난이 사과'가 가성비 1위였다 —
    # 선물 질의에서는 흠과·못난이 표기(판매자 표기) 상품을 고르지 않고 다른 후보 뒤에 둔다. 전부 그렇다면 빼지 않는다.
    blemish_keys: set[str] = set()
    if _GIFT_ASK.search(ask or ""):
        blemish_keys = {c["key"] for c in pool if _BLEMISH.search(c.get("title") or "")}
        if blemish_keys and len(blemish_keys) < len(pool):
            pool = [c for c in pool if c["key"] not in blemish_keys]
        else:
            blemish_keys = set()
    n = len(pool)
    picks: list[dict] = []

    def take(card, role, text, basis):
        card = dict(card, role=role, role_label=ROLE_LABEL[role], why=[{"text": text, "basis": basis}])
        picks.append(card)
        return card

    def free_(c):
        return all(p["key"] != c["key"] for p in picks)

    # 1) 가성비 — 100g당 비교가 가능한 후보가 2개 이상일 때만 '가성비'라고 부른다
    # p45: 가격 비교 금지 카드는 가성비·넉넉한 양·개당 비교에서 뺀다 (값이 남아 있어도)
    weighed = [c for c in pool if c.get("per100g") and not c.get("price_compare_blocked")]
    counted = [c for c in pool if c.get("per_unit") and not c.get("price_compare_blocked")]
    # 2026-11-13 (e2 사람 평가 '우유'): 180ml 18개와 1L 묶음을 개당 가격으로 견주면 작은 것이 늘 '가성비'가 된다 —
    # 한 개 크기가 서로 다르거나, 크기를 아는 상품과 모르는 상품이 섞이면 개당 비교를 하지 않는다
    known = [round(a / c["unit_count"]) for c in counted
             if c.get("unit_count") and (a := c.get("weight_g") or c.get("volume_ml"))]
    if known and (len(set(known)) > 1 or len(known) < len(counted)):
        counted = []
    # 2026-11-12: 액체는 100ml당 — 중량 비교가 안 될 때만, 용량끼리만 견준다 (g 와 ml 를 섞지 않음)
    volumed = [c for c in pool if c.get("per100ml") and not c.get("price_compare_blocked")]
    value = None
    # 2026-11-13: 가정용 양 안에서 먼저 견준다 (후보가 2개 이상일 때만 — 아니면 전체)
    # 선물은 집에서 먹을 양이 아니다 — 선물 질의에는 가정용 양 기준을 쓰지 않는다 (d6: '부모님 선물 망고'의 선물용 자리가 사라졌다)
    band = not bulk_ok and not _amount_asked(ask) and not _GIFT_ASK.search(ask or "")
    house_w = [c for c in weighed if c["weight_g"] <= _house_limits(ask, c.get("title"))[0]] if band else []
    house_v = [c for c in volumed if c["volume_ml"] <= _house_limits(ask, c.get("title"))[1]] if band else []
    if len(house_w) >= 2 and len(house_w) < len(weighed):   # 가정용 양 밖 후보가 있을 때만 범위를 나눠 말한다
        lim = _wtext(max(_house_limits(ask, c.get("title"))[0] for c in house_w))
        best = min(house_w, key=lambda c: c["per100g"])
        value = take(best, "value", f"가정용 양({lim} 이하) 후보 {len(house_w)}개 중 100g당 가장 저렴해요 "
                                    f"({won(best['per100g'])}/100g)", "calc")
    elif len(weighed) >= 2:
        best = min(weighed, key=lambda c: c["per100g"])
        if len(house_w) == 1 and house_w[0]["key"] != best["key"]:
            # 가정용 양 상품이 하나뿐 — 그 상품을 먼저 보이고, 가성비(전체 100g당 최저)는 그다음
            h = house_w[0]
            take(h, "house", f"가정용 양({_wtext(_house_limits(ask, h.get('title'))[0])} 이하) 후보예요 "
                             f"({_wtext(h['weight_g'])}, 100g당 {won(h['per100g'])})", "calc")
        value = take(best, "value", f"후보 {len(weighed)}개 중 100g당 가장 저렴해요 ({won(best['per100g'])}/100g)", "calc")
    elif len(house_v) >= 2 and len(house_v) < len(volumed):
        lim = _vtext(max(_house_limits(ask, c.get("title"))[1] for c in house_v))
        best = min(house_v, key=lambda c: c["per100ml"])
        value = take(best, "value", f"가정용 양({lim} 이하) 후보 {len(house_v)}개 중 100ml당 가장 저렴해요 "
                                    f"({won(best['per100ml'])}/100ml)", "calc")
    elif len(volumed) >= 2:
        best = min(volumed, key=lambda c: c["per100ml"])
        value = take(best, "value", f"후보 {len(volumed)}개 중 100ml당 가장 저렴해요 ({won(best['per100ml'])}/100ml)", "calc")
    elif len(counted) >= 2:
        best = min(counted, key=lambda c: c["per_unit"])
        value = take(best, "value", f"후보 {len(counted)}개 중 개당 가격이 가장 낮아요 (개당 {won(best['per_unit'])})", "calc")
    elif pool:
        best = min(pool, key=_basis)
        value = take(best, "lowest", f"후보 {n}개 중 가격이 가장 낮아요" if n > 1 else "조건에 맞는 후보가 이 상품 하나예요", "calc")

    # 1-2) 당도 표기 — 판매자가 당도 숫자를 적은 상품 (가정용 양 안에서 먼저, 100g당 → 가격 순)
    sweet = [c for c in pool if free_(c) and brix_stated(c.get("title") or "")]
    if band:
        in_house = [c for c in sweet if not c.get("weight_g") or c["weight_g"] <= _house_limits(ask, c.get("title"))[0]]
        sweet = in_house or sweet
    if sweet:
        best = min(sweet, key=lambda c: (c.get("per100g") is None, c.get("per100g") or 0, _basis(c)))
        take(best, "sweet", f"판매자가 당도 {brix_stated(best['title'])}brix라고 적은 상품이에요 (판매자 주장)", "mall")

    # 2) 빠른 배송 — 판매처의 '로켓배송' 표시 (도착일 약속은 아님)
    rockets = [c for c in pool if c.get("rocket") and free_(c)]
    if rockets:
        best = min(rockets, key=_basis)
        others = sum(1 for c in pool if c.get("rocket"))
        take(best, "fast", "쿠팡이 로켓배송으로 표시한 상품" + (" 중 가장 저렴해요" if others > 1 else "이에요"), "mall")

    # 3) 넉넉한 양
    if value and value.get("weight_g"):
        bigger = [c for c in weighed if free_(c) and c["weight_g"] >= value["weight_g"] * 1.3]
        if bigger:
            best = max(bigger, key=lambda c: (c["weight_g"], -c["per100g"]))
            take(best, "ample", f"후보 중 양이 가장 많아요 ({_weight_text(best['weight_g'])}, 100g당 {won(best['per100g'])})", "calc")
    elif value and value.get("volume_ml") and value.get("per100ml"):
        bigger = [c for c in volumed if free_(c) and c["volume_ml"] >= value["volume_ml"] * 1.3]
        if bigger:
            best = max(bigger, key=lambda c: (c["volume_ml"], -c["per100ml"]))
            take(best, "ample", f"후보 중 양이 가장 많아요 ({_vtext(best['volume_ml'])}, 100ml당 {won(best['per100ml'])})", "calc")

    # 4) 선물용 — 고객이 선물을 찾을 때만, 판매자 표기임을 밝힌다
    if _GIFT_ASK.search(ask or ""):
        gifts = [c for c in pool if free_(c) and _GIFT_TITLE.search(c.get("title") or "")]
        if gifts:
            best = min(gifts, key=_basis)
            take(best, "gift", "상품명에 선물용·세트 표기가 있어요 (판매자 표기)", "mall")

    # 5) 남은 자리 — 원래 검색 순서대로
    for c in pool:
        if len(picks) >= MAX_PICKS:
            break
        if free_(c):
            text = _alt_text(c, picks[0] if picks else None)
            take(c, "alt", text, "calc")

    picks = picks[:MAX_PICKS]
    for p in picks:
        extra = []
        if budget and not budget.get("none") and not budget_miss:
            if p.get("shipping_status") == "confirmed" and p.get("total") is not None:
                extra.append({"text": f"예산 {budget['label']} 안이에요 (배송비 포함 {won(p['total'])})", "basis": "you"})
            else:
                extra.append({"text": f"상품가 기준 예산 {budget['label']} 안이에요 · {shipping_note(p)}", "basis": "you"})
        if p.get("weight_g") and p["role"] not in ("value", "ample", "house"):
            per = f", 100g당 {won(p['per100g'])}" if p.get("per100g") else ""
            basis_note = (f"상품명 표기 {p['weight_formula']} 계산" if p.get("weight_formula") else "상품명 표기 기준")
            extra.append({"text": f"{_weight_text(p['weight_g'])}{per} ({basis_note})", "basis": "calc"})
        if p.get("volume_ml") and p["role"] not in ("value", "ample"):
            per = f", 100ml당 {won(p['per100ml'])}" if p.get("per100ml") else ""
            basis_note = (f"상품명 표기 {p['volume_formula']} 계산" if p.get("volume_formula") else "상품명 표기 기준")
            extra.append({"text": f"{_vtext(p['volume_ml'])}{per} ({basis_note})", "basis": "calc"})
        if p.get("rocket") and p["role"] != "fast":
            extra.append({"text": "쿠팡 로켓배송 표시 상품", "basis": "mall"})
        if p.get("free_shipping") and not p.get("rocket"):
            extra.append({"text": "무료배송 표시 상품 (조건은 판매처에서 확인)", "basis": "mall"})
        p["why"] = (p["why"] + extra)[:3]
        p["reason"] = p["why"][0]["text"]
        p["evidence"] = []          # 근거 없는 설명 문구(판매 주장 포함)는 ✓ 근거로 내보내지 않는다

    chosen = {p["key"] for p in picks}
    others = []
    for c in cards:
        if c["key"] in chosen:
            continue
        why = []
        if budget and not budget.get("none") and not budget_miss and not fits(_basis(c), budget):
            basis_word = "" if c.get("shipping_status") == "confirmed" and c.get("total") is not None else "상품가 "
            why = [{"text": f"예산 {budget['label']} 밖이에요 ({basis_word}{won(_basis(c))})", "basis": "you"}]
        if c["key"] in blemish_keys:
            why = why + [{"text": "선물을 찾으셔서 흠과·못난이 표기 상품은 먼저 고르지 않았어요 (판매자 표기)", "basis": "you"}]
        if c["key"] in bulk_keys:
            size = bulk_keys[c["key"]]
            head = f"상품명에 {size}가 있어" if size.endswith("표기") else f"대용량({size})이라"
            why = why + [{"text": f"{head} 업소·대가족용으로 보고 먼저 고르지 않았어요 · "
                                  "'대용량'이라고 하시면 함께 견줘요", "basis": "calc"}]
        others.append(dict(c, role=None, role_label=None, why=why, reason=why[0]["text"] if why else "", evidence=[]))
    others.sort(key=lambda c: (c["key"] in blemish_keys, c["key"] in bulk_keys))   # 흠과(선물)·대용량은 맨 뒤로
    for rank, c in enumerate(picks + others, 1):
        c["rank"] = rank
    return {"picks": picks, "others": others, "pool": n, "total": len(priced), "budget_miss": budget_miss,
            "bulk_held": len(bulk_keys)}


def criteria_line(picks: list[dict], budget: dict | None) -> str:
    used = []
    roles = {p["role"] for p in picks}
    if "house" in roles:
        used.append("가정용 양")
    if "value" in roles:
        value = next(p for p in picks if p["role"] == "value")
        used.append("100ml당 가격" if value.get("per100ml") and not value.get("per100g") else "100g당 가격")
    elif "lowest" in roles:
        used.append("가격")
    if "fast" in roles:
        used.append("로켓배송 표시")
    if "ample" in roles:
        used.append("용량")
    if "gift" in roles:
        used.append("선물 표기")
    if "sweet" in roles:
        used.append("당도 표기(판매자)")
    if budget and not budget.get("none"):
        used.append(f"예산 {budget['label']}")
    return " · ".join(used)
