"""예산 — 클릭 대신 고객의 말에서 읽는다 (2026-11-01).

    parse_budget("3만원 이하")   → {"max": 30000, "min": None, "soft": False, "label": "3만원 이하"}
    parse_budget("5만원 정도")   → {"max": 55000, "min": None, "soft": True,  "label": "5만원 정도"}
    parse_budget("10만원대")     → {"min": 100000, "max": 199999, ...}
    parse_budget("2~3만원")      → {"min": 20000, "max": 30000, ...}
    parse_budget("예산 상관없어") → {"none": True, "label": "예산 상관없음"}

금액에는 반드시 '원'·'만'·'천' 중 하나가 붙어야 한다 ('800g', '3인분'은 예산이 아님).
"""
from __future__ import annotations

import re

_NUM = r"(\d[\d,]*(?:\.\d+)?)"
_UNIT = r"\s*(만|천)?\s*원?"
_RANGE = re.compile(_NUM + r"\s*(만|천)?\s*원?\s*(?:~|-|에서)\s*" + _NUM + r"\s*(만|천)?\s*원")
_RANGE_MAN = re.compile(_NUM + r"\s*(?:~|-)\s*" + _NUM + r"\s*(만|천)\s*원?")
_DAE = re.compile(_NUM + r"\s*(만|천)\s*원\s*대")
_ONE = re.compile(_NUM + r"\s*(?:(만|천)\s*원?|원)")
_HARD_MAX = re.compile(r"^\s*(이하|이내|안쪽|안으로|안에서|안|까지|미만|밑|아래|넘지\s*않)")
_MIN = re.compile(r"^\s*(이상|넘는|넘게|부터)")
_SOFT = re.compile(r"^\s*(정도|쯤|내외|안팎|선|전후|언저리)")
_NONE = re.compile(r"예산\s*(은|는)?\s*(상관\s*없|없어|없음|무관)|상관\s*없|가격\s*(은|는)?\s*상관|아무\s*거나|무관해")


def _won(num: str, unit: str | None) -> int | None:
    try:
        v = float(num.replace(",", ""))
    except ValueError:
        return None
    v *= {"만": 10_000, "천": 1_000}.get(unit or "", 1)
    return int(round(v)) if 1_000 <= v <= 100_000_000 else None


def _man(v: int) -> str:
    if v >= 10_000:
        m = v / 10_000
        return f"{m:g}만원"
    return f"{v:,}원"


def parse_budget(text: str) -> dict | None:
    t = text or ""
    if _NONE.search(t):
        return {"none": True, "min": None, "max": None, "soft": False, "label": "예산 상관없음", "span": None}
    m = _RANGE.search(t) or _RANGE_MAN.search(t)
    if m:
        if m.re is _RANGE_MAN:
            lo, hi = _won(m.group(1), m.group(3)), _won(m.group(2), m.group(3))
        else:
            lo, hi = _won(m.group(1), m.group(2) or m.group(4)), _won(m.group(3), m.group(4))
        if lo and hi and lo < hi:
            return {"min": lo, "max": hi, "soft": False, "label": f"{_man(lo)}~{_man(hi)}", "span": m.span()}
    m = _DAE.search(t)
    if m:
        lo = _won(m.group(1), m.group(2))
        if lo:
            digits = len(str(int(float(m.group(1).replace(",", "")))))
            step = 10 ** (digits - 1) * {"만": 10_000, "천": 1_000}[m.group(2)]
            return {"min": lo, "max": lo + step - 1, "soft": False, "label": f"{_man(lo)}대", "span": m.span()}
    m = _ONE.search(t)
    if not m:
        return None
    v = _won(m.group(1), m.group(2))
    if not v:
        return None
    rest = t[m.end():]
    q = _HARD_MAX.match(rest)
    if q:
        return {"min": None, "max": v, "soft": False, "label": f"{_man(v)} 이하", "span": (m.start(), m.end() + q.end())}
    q = _MIN.match(rest)
    if q:
        return {"min": v, "max": None, "soft": False, "label": f"{_man(v)} 이상", "span": (m.start(), m.end() + q.end())}
    q = _SOFT.match(rest)
    end = m.end() + (q.end() if q else 0)
    # '5만원' / '5만원 정도' — 조금 넘는 것(10%)까지 함께 본다
    return {"min": None, "max": int(v * 1.1), "soft": True, "label": f"{_man(v)} 정도", "span": (m.start(), end)}


_FILLER = re.compile(r"(?:해\s*줘|해\s*주세요|해\s*주실래요|부탁(?:해|드려)?(?:요)?|골라\s*줘|보여\s*줘|찾아\s*줘|다시|맞춰서?|안에서|안으로|대로)|예산|은|는|이|가|으로|로|요|이요|에요|예요|입니다|이에요|생각|해요|하고\s*있어|있어|정도|쯤|까지|만|원|[\s.,!~?]")


def is_budget_answer(text: str) -> bool:
    """'3만원 이하요', '예산은 5만원 정도' — 예산만 말한 짧은 답 (새 상품 검색이 아님)."""
    b = parse_budget(text)
    if not b:
        return False
    if b.get("none"):
        return len(text.strip()) <= 20
    s, e = b["span"]
    rest = _FILLER.sub("", text[:s] + text[e:])
    return len(rest) <= 1


def strip_budget(text: str) -> str:
    """검색어에서 예산 표현을 뺀다 ('5만원 이하 한우 등심' → '한우 등심')."""
    b = parse_budget(text)
    if not b or not b.get("span"):
        return text
    s, e = b["span"]
    out = (text[:s] + " " + text[e:])
    out = re.sub(r"(예산\s*(은|는)?\s*)", " ", out)
    out = re.sub(r"^\s*(으로|로|에|의|짜리|선에서|에서)\s+", "", out.strip())
    return re.sub(r"\s+", " ", out).strip() or text


def fits(price_basis: int, budget: dict | None) -> bool:
    if not budget or budget.get("none"):
        return True
    if budget.get("max") is not None and price_basis > budget["max"]:
        return False
    if budget.get("min") is not None and price_basis < budget["min"]:
        return False
    return True
