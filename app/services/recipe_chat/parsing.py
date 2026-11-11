"""Deterministic message parsing for recipe turns (no LLM, no network)."""
from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

# unit text → (canonical unit, multiplier).  Only exact metric conversions.
_UNITS = {
    "ml": ("mL", Decimal(1)), "밀리리터": ("mL", Decimal(1)), "밀리": ("mL", Decimal(1)), "cc": ("mL", Decimal(1)),
    "l": ("mL", Decimal(1000)), "리터": ("mL", Decimal(1000)),
    "g": ("g", Decimal(1)), "그램": ("g", Decimal(1)),
    "kg": ("g", Decimal(1000)), "킬로그램": ("g", Decimal(1000)), "킬로": ("g", Decimal(1000)),
    "개": ("개", Decimal(1)),
}
_UNIT_ALT = "|".join(sorted((re.escape(u) for u in _UNITS), key=len, reverse=True))
AMOUNT_RE = re.compile(r"(\d+(?:\.\d+)?)\s*(" + _UNIT_ALT + r")(?![a-zA-Z])", re.IGNORECASE)
PERCENT_RE = re.compile(r"(\d+(?:\.\d+)?)\s*(%|퍼센트|프로)")
CUP_RE = re.compile(r"(\d+(?:\.\d+)?|반|한|두|세)\s*(컵|큰술|작은술|스푼|숟가락|T\b|t\b)")

RECIPE_REQUEST_RE = re.compile(
    r"레시피|요리\s*방법|요리법|조리법|조리\s*방법|만드는\s*법|만드는\s*방법|만들어|만들\s*수\s*있|만들까|어떻게\s*만들|해\s*먹|해먹|끓이는\s*법|볶는\s*법")
CORRECTION_RE = re.compile(r"^\s*(아니|아뇨|아니요|아니야|정정|수정|다시)|잘못|틀렸")
PRODUCT_REQUEST_RE = re.compile(r"상품|구매|사고\s*싶|살래|살게|사야|주문|장보기|어디서\s*사|파는\s*곳")
SHOW_RE = re.compile(r"보여|찾아|추천|알려|검색|볼래|줘")
SHORTAGE_PRODUCTS_RE = re.compile(r"부족한\s*재료|없는\s*재료|모자란\s*재료|필요한\s*재료")
QUESTION_RE = re.compile(
    r"\?|어떻게|대신|대체|없으면|몇\s*분|언제|왜|묽|되직|걸쭉|짜|싱거|타요|탔|눌|순서|다음|팁|불\s*세기|약불|센불|삶|볶|간은|넣어도|빼도")
JUDGEMENT_PATTERNS = (
    ("absent", re.compile(r"없어|없음|없다|없네|다\s*떨어|다\s*썼")),
    ("short", re.compile(r"부족|모자라|모자랄|조금밖에|조금\s*밖에")),
    ("enough", re.compile(r"충분|넉넉|많아|있으니\s*됐")),
)
PACK_RE = re.compile(r"팩|통|병|용기|박스|봉지|짜리|중에|중\s")
HALF_RE = re.compile(r"절반|반\s*정도|반쯤|반\s*남")


def normalize_amount(number: str, unit: str) -> tuple[str, str] | None:
    canonical = _UNITS.get(unit.lower()) or _UNITS.get(unit)
    if canonical is None:
        return None
    try:
        value = Decimal(number) * canonical[1]
    except InvalidOperation:
        return None
    if not value.is_finite():
        return None
    text = format(value.normalize(), "f") if value != value.to_integral() else format(value.to_integral(), "f")
    return text, canonical[0]


def amounts(message: str) -> list[tuple[str, str, str]]:
    """[(amount, canonical unit, raw match)]"""
    out = []
    for m in AMOUNT_RE.finditer(message or ""):
        norm = normalize_amount(m.group(1), m.group(2))
        if norm:
            out.append((norm[0], norm[1], m.group(0)))
    return out


# 2026-10-30: cups and spoons are stored as the customer said them ('모시조개 1컵', '된장 반 큰술').
# Their size is not known, so they are never converted and never compared for 충분·부족.
UNCLEAR_UNITS = ("컵", "큰술", "작은술", "숟가락")
_SPOKEN = {"반": "0.5", "한": "1", "두": "2", "세": "3", "네": "4"}
_VOLUME_RE = re.compile(
    r"(\d+\s*과\s*\d+/\d+|\d+/\d+|\d+(?:\.\d+)?|반|한|두|세|네)\s*(컵|큰\s*술|작은\s*술|숟가락|숟갈|스푼|T(?![a-zA-Z])|t(?![a-zA-Z]))"
    r"(\s*반)?")


def _unit_name(raw: str) -> str:
    raw = re.sub(r"\s+", "", raw)
    return {"T": "큰술", "t": "작은술", "숟갈": "숟가락", "스푼": "숟가락"}.get(raw, raw)


def volume_amounts(message: str) -> list[tuple[str, str, str]]:
    """[(decimal amount, unit, the customer's own words)] for cups / spoons: '1과1/2컵' → ('1.5','컵','1과1/2컵')."""
    out = []
    for m in _VOLUME_RE.finditer(message or ""):
        number, unit, half = m.group(1), _unit_name(m.group(2)), m.group(3)
        try:
            flat = re.sub(r"\s+", "", number)
            if flat in _SPOKEN:
                value = Decimal(_SPOKEN[flat])
            elif "과" in flat:
                whole, part = flat.split("과")
                n, d = part.split("/")
                value = Decimal(whole) + Decimal(n) / Decimal(d)
            elif "/" in flat:
                n, d = flat.split("/")
                value = Decimal(n) / Decimal(d)
            else:
                value = Decimal(flat)
        except (InvalidOperation, ValueError, ZeroDivisionError):
            continue
        if half:                       # '1컵 반'
            value += Decimal("0.5")
        if not value.is_finite() or value <= 0 or value > 100:
            continue
        text = format(value.normalize(), "f")
        out.append((text, unit, m.group(0).strip()))
    return out


def stock_display(stock: dict) -> str:
    """How a stored amount is shown: the customer's words for cups / spoons, else amount + unit as stored."""
    if stock.get("said"):
        return stock["said"]
    if stock["unit"] in UNCLEAR_UNITS:
        from fractions import Fraction
        value = Fraction(Decimal(stock["amount"])).limit_denominator(8)
        whole, part = divmod(value.numerator, value.denominator)
        text = str(whole) if not part else (f"{whole}과{part}/{value.denominator}" if whole else f"{part}/{value.denominator}")
        return text + stock["unit"]
    return f"{stock['amount']}{stock['unit']}"


def stock_amounts(message: str) -> list[tuple[str, str, str]]:
    """Metric amounts and cup / spoon amounts together, in message order."""
    return amounts(message) + volume_amounts(message)


_NOT_THIS = re.compile(r"\s*(?:이|가|은|는)?\s*(?:말고|말구|아니고|아니라|대신)")


def drop_negated(message: str, found: list[tuple[str, str, str]]) -> list[tuple[str, str, str]]:
    """'50g 말고 30g이에요' → only 30g: an amount the customer takes back is not a second amount (2026-11-01)."""
    text, pos, kept = message or "", 0, []
    for item in found:
        at = text.find(item[2], pos)
        if at < 0:
            kept.append(item)
            continue
        pos = at + len(item[2])
        if not _NOT_THIS.match(text[pos:]):
            kept.append(item)
    return kept or found


def _core(name: str) -> str:
    return re.sub(r"\s*\([^)]*\)\s*", "", name or "").strip() or (name or "")


def mentioned_materials(message: str, materials: list[dict]) -> list[dict]:
    """Recipe materials named in the message (longest names win, no overlaps)."""
    text = message or ""
    found: list[dict] = []
    taken: list[tuple[int, int]] = []
    for m in sorted(materials, key=lambda x: len(x["name"]), reverse=True):
        start = text.find(m["name"])
        if start < 0:
            continue
        end = start + len(m["name"])
        if any(not (end <= a or start >= b) for a, b in taken):
            continue
        taken.append((start, end))
        found.append(m)
    if found:
        return found
    # 2026-10-30: a shorter everyday name that ends one ingredient name — '된장' → '순창콩된장', '고기' → '쇠고기'.
    # Only when exactly one ingredient fits (never a guess between two).
    for word in re.findall(r"[가-힣]{2,}", text):
        word = re.sub(r"(은|는|이|가|을|를|도|만|으로|로|이랑|랑|하고)$", "", word)
        if len(word) < 2:
            continue
        # 2026-11-01: '카다이프' → '카다이프(면실)' — a note in brackets is not part of the name ('버터' still fits two)
        hits = [m for m in materials if m["name"] != word and _core(m["name"]).endswith(word)]
        if len(hits) == 1 and hits[0] not in found:
            found.append(hits[0])
    return found if len(found) == 1 else []


def ambiguous_materials(message: str, materials: list[dict]) -> tuple[str, list[dict]] | None:
    """('버터', [무염버터(반죽용), 무염버터(카다이프용)]) when a word in the message fits two or more ingredients and no
    ingredient is named in full (2026-11-01: the customer is asked which one — never a guess)."""
    if mentioned_materials(message, materials):
        return None
    for word in re.findall(r"[가-힣]{2,}", message or ""):
        word = re.sub(r"(은|는|이|가|을|를|도|만|으로|로|이랑|랑|하고|보유량|남은양)$", "", word)
        if len(word) < 2:
            continue
        hits = [m for m in materials if word in _core(m["name"]) or word == m["name"]]
        if len(hits) >= 2:
            return word, hits
    return None


# 2026-11-10 (customer check): "귤 10kg 박스로 사려는데 크기별로 뭐가 맛있어?" was read as a stock sentence —
# '맛있어' contains '있어', and '10kg' is an amount. '있어' means "I have" only when it is not part of
# 맛있어·멋있어·재미있어·상관있어·의미있어·관계있어·…수 있어, and a buying sentence is never a stock sentence.
HAVE_RE = re.compile(r"(?<![맛멋수])(?<!재미)(?<!상관)(?<!의미)(?<!관계)(?<!수\s)있어|남았|남아")
BUYING_RE = re.compile(r"사\s*려|살\s*까|사고\s*싶|사\s*야|구매|구입|주문|장\s*보")


def says_have(message: str) -> bool:
    """'우유 200mL 있어요' / '버터 남았어' — the person tells what they have (not 맛있어, not 사려는데)."""
    text = message or ""
    return bool(HAVE_RE.search(text)) and not BUYING_RE.search(text)


# 2026-11-01 (customer check): "카다이프 보유량 얼마로 기록돼 있어요?" was answered with the requirement.
# A question about the *recorded* amount is answered with the stored amount first.
STOCK_QUERY_RE = re.compile(
    r"(보유량|남은\s*양|남은\s*거|재고|기록|저장|입력).{0,15}(얼마|몇|뭐|무엇|어떻게|확인|맞|돼\s*있|되어\s*있)"
    r"|(얼마|몇).{0,10}(기록|저장|입력|남아\s*있다고|있다고\s*(?:했|돼|되))"
    r"|(기록|저장)된\s*(양|보유량|거)")


def is_stock_query(message: str) -> bool:
    text = message or ""
    return bool(STOCK_QUERY_RE.search(text)) and not stock_amounts(text)


def judgement(message: str) -> str | None:
    for name, pattern in JUDGEMENT_PATTERNS:
        if pattern.search(message or ""):
            return name
    return None


def is_pack_ratio(message: str) -> bool:
    text = message or ""
    if PERCENT_RE.search(text) or HALF_RE.search(text):
        return True
    return len(amounts(text)) >= 2 and bool(PACK_RE.search(text))


def percent(message: str) -> str | None:
    m = PERCENT_RE.search(message or "")
    if m:
        return m.group(1)
    if HALF_RE.search(message or ""):
        return "50"
    return None


def is_recipe_request(message: str) -> bool:
    return bool(RECIPE_REQUEST_RE.search(message or ""))


def is_correction(message: str) -> bool:
    return bool(CORRECTION_RE.search(message or ""))


def is_product_request(message: str) -> bool:
    text = message or ""
    return bool(PRODUCT_REQUEST_RE.search(text)) and bool(SHOW_RE.search(text) or "사" in text)


def is_shortage_products_request(message: str) -> bool:
    text = message or ""
    return bool(SHORTAGE_PRODUCTS_RE.search(text)) and is_product_request(text)


COOKING_WORDS_RE = re.compile(
    r"대신|대체|없으면|몇\s*분|묽|되직|걸쭉|짜요|짜게|짜다|싱거|탔|타요|눌|순서|다음\s*단계|팁|불\s*세기|약불|센불|삶|볶|간은|간을|소스|면이|면은|끓|분리|넣어도|빼도|"
    # 2026-10-30: other cooking methods (찜·구이·조림·재우기·데치기·부침·튀김) and "언제 넣어요"
    r"쪄|찌[나는면요]|굽|구워|구우|재워|재우|재울|조려|졸여|졸이|데쳐|데치|부쳐|부치|튀겨|튀기|언제\s*넣|넣어요|넣나요|얼마나\s*익")


def is_question(message: str) -> bool:
    return bool(QUESTION_RE.search(message or ""))


def is_cooking_question(message: str, named: list) -> bool:
    """A question about the current recipe: names a recipe material or uses cooking words."""
    text = message or ""
    if COOKING_WORDS_RE.search(text):
        return True
    return bool(named) and is_question(text)


def has_cup_amount(message: str) -> bool:
    return bool(CUP_RE.search(message or ""))


def requirement_amount(raw: str) -> tuple[str, str] | None:
    """Leading metric amount of a source requirement.

    '200g' → ('200','g'), '(20g)' → ('20','g'), '300ml(1½컵)' → ('300','mL'), '(46g, 3장)' → ('46','g').
    Cups, spoons, vague amounts and fractions of pieces ('1/2개') → None.
    """
    m = re.match(r"\s*\(?\s*(\d+(?:\.\d+)?)\s*(" + _UNIT_ALT + r")(?![a-zA-Z가-힣/])", raw or "", re.IGNORECASE)
    if not m:
        return None
    return normalize_amount(m.group(1), m.group(2))
