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
      'count_unclear' 곱하기 없이 개수가 붙음 ('100g 10팩') → weight = None (개당·전체 불명, p33)
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
    singles = [_grams(a, u) for m in _WEIGHT_RE.finditer(text)
               if not any(a0 <= m.start() < b0 for a0, b0 in spans)
               for a, u in [m.groups()]]
    values = totals + singles
    found = [_wtext(v) for v in values]
    if not values:
        return {"weight": None, "kind": "none", "formula": None, "found": []}
    if len({round(v, 6) for v in values}) > 1:
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
              "gift": "선물용", "alt": "다른 선택"}
MAX_PICKS = 4

_CLAIMS = (
    ("고당도", re.compile(r"고당도|꿀\s*당도|당도\s*\d+\s*(?:brix|브릭스)?", re.I)),
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


def enrich(card: dict, item: dict) -> dict:
    """사실만 붙인다: 키 · 중량/개수 · 100g당 · 로켓/무료배송 표시 · 판매자 문구 · 판매처 확인 안내."""
    weight, unit, weight_source = _amount(card, item)
    rocket = _flag(item, "is_rocket", "isRocket")
    free = _flag(item, "is_free_shipping", "isFreeShipping")
    if free is True and card.get("shipping_fee") is None:
        card["shipping_fee"] = 0
        card["total"] = card.get("price")
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
    return _blocked(card)


def _blocked(card: dict) -> dict:
    """p45: 가격 비교 금지 카드(UCP 판매자 단위가격 등)는 상품명으로 중량·100g당·개당을 다시 채우지 않는다.
    p47: 상품명 개수(unit_count)도 비운다 — 공통 모델 근거에서 '상품명 표기 기준 비교 허용'으로 나가지 않게."""
    if card.get("price_compare_blocked"):
        card.update(weight_g=None, per100g=None, per_unit=None, weight_source=None, weight_formula=None,
                    weight_found=None, unit_count=None, weight_note=None)
    return card


def reweigh(card: dict) -> dict:
    """저장 카드의 중량을 지금 규칙으로 다시 계산한 사본 (p31, p32 보완).
    출처 기록이 없거나(p31 이전) 상품명에서 읽은 중량이면 상품명으로 다시 계산한다 — 상품명 해석 규칙이 바뀌어도
    (p32: 옵션 목록·곱하기) 예전 값이 남지 않게.  상위 weight_g('upstream')로 기록된 카드는 지금도 허용 조건
    (CHAT_TRUST_UPSTREAM_WEIGHT=1 + weight_verified)을 만족할 때만 그대로 두고, 아니면 상품명으로 다시 계산한다 (p34)."""
    # p34: 저장된 상위 중량도 지금의 허용 조건(설정 켬 + 행별 확인 표시)을 다시 확인한다 — 아니면 상품명으로 재계산
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
    if c.get("weight_g") and c.get("weight_g") == ref.get("weight_g"):
        diff = _basis(c) - _basis(ref)
        if diff:
            return f"같은 중량인 {label} 상품보다 {won(abs(diff))} {'비싸요' if diff > 0 else '저렴해요'}"
    return "상품명에 중량 표기가 없어 양 기준 가격은 견주지 못했어요 · 판매처에서 양을 확인해 주세요"


def choose(cards: list[dict], *, budget: dict | None = None, ask: str = "") -> dict:
    """역할별로 고르고 사유를 단다.

    Returns {"picks": [...], "others": [...], "pool": n, "total": n, "budget_miss": bool}
    """
    priced = [c for c in cards if (c.get("price") or 0) > 0]
    pool = [c for c in priced if fits(_basis(c), budget)]
    budget_miss = bool(budget and not budget.get("none") and priced and not pool)
    if budget_miss:          # 예산 안에 없으면: 예산에 가까운(싼) 순으로, 그렇다고 말한다
        pool = sorted(priced, key=_basis)
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
    value = None
    if len(weighed) >= 2:
        best = min(weighed, key=lambda c: c["per100g"])
        value = take(best, "value", f"후보 {len(weighed)}개 중 100g당 가장 저렴해요 ({won(best['per100g'])}/100g)", "calc")
    elif len(counted) >= 2:
        best = min(counted, key=lambda c: c["per_unit"])
        value = take(best, "value", f"후보 {len(counted)}개 중 개당 가격이 가장 낮아요 (개당 {won(best['per_unit'])})", "calc")
    elif pool:
        best = min(pool, key=_basis)
        value = take(best, "lowest", f"후보 {n}개 중 가격이 가장 낮아요" if n > 1 else "조건에 맞는 후보가 이 상품 하나예요", "calc")

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
            if p.get("total") is not None:
                extra.append({"text": f"예산 {budget['label']} 안이에요 (배송비 포함 {won(p['total'])})", "basis": "you"})
            else:
                extra.append({"text": f"상품가 기준 예산 {budget['label']} 안이에요 · 배송비는 미확인", "basis": "you"})
        if p.get("weight_g") and p["role"] not in ("value", "ample"):
            per = f", 100g당 {won(p['per100g'])}" if p.get("per100g") else ""
            basis_note = (f"상품명 표기 {p['weight_formula']} 계산" if p.get("weight_formula") else "상품명 표기 기준")
            extra.append({"text": f"{_weight_text(p['weight_g'])}{per} ({basis_note})", "basis": "calc"})
        if p.get("rocket") and p["role"] != "fast":
            extra.append({"text": "쿠팡 로켓배송 표시 상품", "basis": "mall"})
        if p.get("free_shipping") and not p.get("rocket"):
            extra.append({"text": "무료배송 표시 상품", "basis": "mall"})
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
            why = [{"text": f"예산 {budget['label']} 밖이에요 ({won(_basis(c))})", "basis": "you"}]
        others.append(dict(c, role=None, role_label=None, why=why, reason=why[0]["text"] if why else "", evidence=[]))
    for rank, c in enumerate(picks + others, 1):
        c["rank"] = rank
    return {"picks": picks, "others": others, "pool": n, "total": len(priced), "budget_miss": budget_miss}


def criteria_line(picks: list[dict], budget: dict | None) -> str:
    used = []
    roles = {p["role"] for p in picks}
    if "value" in roles:
        used.append("100g당 가격")
    elif "lowest" in roles:
        used.append("가격")
    if "fast" in roles:
        used.append("로켓배송 표시")
    if "ample" in roles:
        used.append("용량")
    if "gift" in roles:
        used.append("선물 표기")
    if budget and not budget.get("none"):
        used.append(f"예산 {budget['label']}")
    return " · ".join(used)
