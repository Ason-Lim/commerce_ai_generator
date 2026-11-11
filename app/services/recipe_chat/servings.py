"""인분 변경 — scale the source ingredient amounts to another number of servings.

Rules (2026-10-30, 3순위):
* the base is the source's own servings ("2인분"); without one, nothing is scaled
* numeric amounts are multiplied with exact fractions; the unit is kept as written
  (컵 stays 컵 — the source never says how big its cup is, so no mL)
* vague amounts ("약간", "적당량", "기호에 따라") and anything that cannot be read
  are shown unchanged and marked as not scaled
* steps, times and calories are the source's — they are not scaled
* nothing here touches stock answers or sufficiency
"""
from __future__ import annotations

import re
from fractions import Fraction

MAX_SERVINGS = 20
_KO_NUM = {"한": 1, "두": 2, "세": 3, "네": 4, "다섯": 5, "여섯": 6, "일곱": 7, "여덟": 8, "아홉": 9, "열": 10}
_UNICODE = {"½": Fraction(1, 2), "⅓": Fraction(1, 3), "⅔": Fraction(2, 3), "¼": Fraction(1, 4), "¾": Fraction(3, 4)}
_REQUEST_RE = re.compile(r"(\d{1,2}|" + "|".join(sorted(_KO_NUM, key=len, reverse=True)) + r")\s*(인분|명|사람)")
_PEOPLE_WORDS = re.compile(r"먹|분량|기준|양으로|양\s|양$|양만|만들")
_PRODUCT_WORDS = re.compile(r"상품|구매|선물|과자|사고|살래|주문|추천|돌릴")
_NUMBER = r"(?:\d+\s*과\s*\d+/\d+|\d+(?:\.\d+)?/\d+|\d+[½⅓⅔¼¾]|[½⅓⅔¼¾]|\d+(?:\.\d+)?)"
_AMOUNT_RE = re.compile(r"^\s*(약\s*)?(" + _NUMBER + r")(?:\s*(~|-)\s*(" + _NUMBER + r"))?\s*(.*?)\s*$")
_VAGUE = re.compile(r"^(약간|적당량?|적량|조금|소량|기호에\s*따라|취향껏|넉넉히)")
# units written with fractions in Korean recipes; others (g, mL…) use decimals
_FRACTION_UNITS = ("컵", "큰술", "작은술", "스푼", "숟가락", "개", "장", "쪽", "줄", "토막", "줌", "꼬집", "모", "봉", "팩", "마리", "알",
                   "뿌리", "대", "송이", "잎", "단", "공기", "포기", "줄기", "톨", "통")
_KO_AMOUNT_WORDS = {"한": 1, "두": 2, "세": 3, "네": 4, "반": Fraction(1, 2)}


# 2026-10-30: a servings mention is classified before anything changes —
#   change ("2인분으로 바꿔 줘"), correction ("1인분 말고 2인분으로"), question ("1인분이면 충분할까요?"),
#   unclear (several numbers, or no change / question wording) → ask, never guess.
_NEGATED = re.compile(r"\s*(?:이|가|은|는)?\s*(?:말고|말구|아니고|아니라|아닌|대신|빼고)")
_CHANGE = re.compile(r"바꿔|바꾸|바꿀|변경|기준으로|맞춰|계산해|알려|보여|만들어|만들래|만들게|먹을\s*양|"
                     r"(?:으로|로)\s*(?:해|하자|할게|할래|부탁|주세요|줘|요|$)")
_QUESTION = re.compile(r"\?|까요|을까|ㄹ까|할까|될까|되나|되나요|인가요|나요\b|괜찮|충분|모자라|부족|몇\s*인분")
_CONDITIONAL = re.compile(r"(?:하|바꾸|이|라|으로|로)면")
_BARE = re.compile(r"\s*(\d{1,2}|" + "|".join(sorted(_KO_NUM, key=len, reverse=True)) + r")\s*인분\s*(?:으로|로)?\s*(?:요)?[.!]?\s*")


def _value(raw: str) -> int | None:
    n = int(raw) if raw.isdigit() else _KO_NUM.get(raw)
    return n if n and 1 <= n <= MAX_SERVINGS else None


# 2026-11-01: an AI-suggested dessert is made in pieces ("10개 분량"), not servings.  For such a recipe
# "20개 분량으로 바꿔줘" / "20개로 바꿔줘" is the same request as "20인분으로 바꿔줘" (it fell into a product search).
# "달걀 2개 있어요" is never read as servings: only '개 분량' or '개로' + a change word count.
_COUNT_UNIT = "개 분량"
_KO = "|".join(sorted(_KO_NUM, key=len, reverse=True))
_COUNT_SERVINGS = re.compile(r"(\d{1,2}|" + _KO + r")\s*개\s*분량")
_COUNT_CHANGE = re.compile(r"(\d{1,2}|" + _KO + r")\s*개\s*(?=(?:으로|로)\s*(?:바꿔|바꾸|변경|늘려|줄여|만들|맞춰|해|계산))")


def unit(meta: list[str]) -> str:
    """'인분' (default) or '개 분량' when the recipe states its yield in pieces ('10개 분량')."""
    if any(re.fullmatch(r"\s*\d{1,2}\s*인분\s*", m or "") for m in meta or []):
        return "인분"
    if any(re.fullmatch(r"\s*\d{1,3}\s*개(?:\s*분량)?\s*", m or "") for m in meta or []):
        return _COUNT_UNIT
    return "인분"


def interpret(text: str, count: bool = False) -> dict | None:
    """{"kind": "change" | "question" | "unclear", "target": int | None, "mentioned": [ints]} or None
    when the message does not talk about servings at all.  Only "change" may change the state.
    ``count``: the recipe is made in pieces — '20개 분량' is read like '20인분'."""
    t = text or ""
    if count:
        t = _COUNT_CHANGE.sub(lambda m: m.group(1) + "인분", _COUNT_SERVINGS.sub(lambda m: m.group(1) + "인분", t))
    mentions = list(_REQUEST_RE.finditer(t))
    if not mentions or _PRODUCT_WORDS.search(t):
        return None
    if all(m.group(2) != "인분" for m in mentions) and not _PEOPLE_WORDS.search(t):
        return None
    if any(re.search(r"\d\s*[~\-–]\s*$", t[:m.start()]) for m in mentions):   # "2~3인분" — not one number
        return {"kind": "unclear", "target": None, "mentioned": [], "reason": "range"}
    values = [(_value(m.group(1)), bool(_NEGATED.match(t[m.end():]))) for m in mentions]
    if any(v is None for v, _neg in values):
        return {"kind": "unclear", "target": None, "mentioned": [v for v, _ in values if v], "reason": "range"}
    kept = list(dict.fromkeys(v for v, neg in values if not neg))
    negated = [v for v, neg in values if neg]
    mentioned = list(dict.fromkeys(v for v, _ in values))
    question = bool(_QUESTION.search(t))
    change = bool(_CHANGE.search(t)) or bool(_BARE.fullmatch(t))
    if question and (_CONDITIONAL.search(t) or not change):
        return {"kind": "question", "target": kept[-1] if len(kept) == 1 else None, "mentioned": mentioned,
                "asks_enough": bool(re.search(r"충분|부족|모자라", t))}
    if negated and len(kept) == 1:
        return {"kind": "change", "target": kept[0], "mentioned": mentioned, "corrected_from": negated}
    if change and len(kept) == 1:
        return {"kind": "change", "target": kept[0], "mentioned": mentioned}
    return {"kind": "unclear", "target": None, "mentioned": mentioned}


def requested(text: str) -> int | None:
    """Target servings only when the message clearly asks to change them (see interpret())."""
    found = interpret(text)
    return found["target"] if found and found["kind"] == "change" else None


def base(meta: list[str]) -> int | None:
    """'2인분' → 2.  Ranges ('2~3인분') or a missing value → None (cannot scale)."""
    for m in meta or []:
        found = re.fullmatch(r"\s*(\d{1,2})\s*인분\s*", m or "")
        if found:
            return int(found.group(1))
    for m in meta or []:                      # '10개 분량' (AI-suggested dessert) — see unit()
        found = re.fullmatch(r"\s*(\d{1,2})\s*개(?:\s*분량)?\s*", m or "")
        if found:
            return int(found.group(1))
    return None


_KEEP = ("url", "href", "src", "image", "id", "recipe_id", "value", "ref")


def as_unit(value, unit_word: str):
    """Messages and the card are written in 인분; for a recipe made in pieces '20인분' reads '20개 분량'."""
    if unit_word != _COUNT_UNIT:
        return value
    if isinstance(value, str):
        value = re.sub(r"(\d{1,2})\s*인분", r"\1개 분량", value)
        value = value.replace("몇 인분", "몇 개 분량").replace("인분", "분량")
        return re.sub(r"개 분량(\s*)분량", r"개 분량", value)
    if isinstance(value, list):
        return [as_unit(v, unit_word) for v in value]
    if isinstance(value, dict):
        return {k: (v if k in _KEEP else as_unit(v, unit_word)) for k, v in value.items()}
    return value


def _num(text: str) -> Fraction:
    text = re.sub(r"\s+", "", text)
    if "과" in text:
        whole, part = text.split("과")
        return Fraction(int(whole)) + Fraction(part)
    if text[-1] in _UNICODE:
        return (Fraction(text[:-1]) if len(text) > 1 else 0) + _UNICODE[text[-1]]
    return Fraction(text)


def _fmt(value: Fraction, unit: str) -> str:
    if value.denominator == 1:
        return str(value.numerator)
    if unit.startswith(_FRACTION_UNITS) and value.denominator in (2, 3, 4, 8):
        whole, part = divmod(value.numerator, value.denominator)
        frac = f"{part}/{value.denominator}"
        return f"{whole}과{frac}" if whole else frac
    text = f"{float(value):.2f}".rstrip("0").rstrip(".")
    return text


def scale(amount: str, factor: Fraction) -> str | None:
    """'200g' ×1/2 → '100g', '1과1/2컵' → '3/4컵', '약간' → None (keep), unreadable → None."""
    a = (amount or "").strip()
    if a.startswith("(") and a.endswith(")") and a.count("(") == 1:
        a = a[1:-1].strip()
    if not a or _VAGUE.match(a):
        return None
    word = re.match(r"^(한|두|세|네|반)\s*([가-힣]{1,3})$", a)    # '한줌', '반 컵', '두 쪽'
    if word and word.group(2) not in ("약간", "적당"):
        value = Fraction(_KO_AMOUNT_WORDS[word.group(1)]) * factor
        return _fmt(value, word.group(2)) + word.group(2)
    m = _AMOUNT_RE.match(a)
    if not m:
        return None
    about, lo, sep, hi, unit = m.groups()
    if re.search(r"\d", unit or ""):   # '300ml(1½컵)' and other compound texts: keep as written
        return None
    try:
        low = _num(lo) * factor
        high = _num(hi) * factor if hi else None
    except (ValueError, ZeroDivisionError):
        return None
    text = _fmt(low, unit) + (f"{sep}{_fmt(high, unit)}" if high is not None else "")
    return f"{'약 ' if about else ''}{text}{unit}"


LLM_PROMPT = """너는 레시피 대화에서 고객 문장이 '인분 변경 요청'인지 판단한다. JSON 하나만 출력한다.
{"kind": "change" | "question" | "none", "target": 정수 또는 null}
- change: 레시피 분량을 그 인분으로 바꿔 달라는 요청. target은 바꿀 인분.
- question: 인분에 대해 묻기만 하는 문장(바꾸라는 요청 아님). target은 물어본 인분 또는 null.
- none: 인분과 관계없음.
target은 반드시 문장에 나온 숫자 중 하나여야 한다. 확실하지 않으면 question 또는 none."""


def llm_interpreter(env=None):
    """DeepSeek fallback for unclear servings messages (same server-side key rule as the stock interpreter).
    The caller still validates: kind ∈ {change, question}, target ∈ the numbers in the message."""
    from app.services.nlu.llm_client import LLMClient

    client = LLMClient(LLM_PROMPT, provider="deepseek", env=env, cache="recipe_servings", cache_days=90)

    def interpret_llm(text: str) -> dict:
        return client.chat_json(text, temperature=0)
    return interpret_llm


def validated(proposal, found: dict) -> dict | None:
    """Accept an LLM proposal only when it names a servings number from the message itself."""
    if not isinstance(proposal, dict) or proposal.get("kind") not in ("change", "question"):
        return None
    target = proposal.get("target")
    if proposal["kind"] == "change":
        if not isinstance(target, int) or target not in found.get("mentioned", []):
            return None
        return {"kind": "change", "target": target, "mentioned": found["mentioned"], "by": "llm"}
    return {"kind": "question", "target": target if target in found.get("mentioned", []) else None,
            "mentioned": found["mentioned"], "by": "llm"}


_STOCK_WORDS = re.compile(r"재료|있는|가진|가지고|남은|남아|보유|냉장고|만들\s*수|될까요.*재료|이걸로|이거로")


def asks_about_stock(text: str) -> bool:
    """'지금 있는 재료로 1인분 만들 수 있어요?' — about the customer's ingredients, not about how much to eat."""
    return bool(_STOCK_WORDS.search(text or ""))
