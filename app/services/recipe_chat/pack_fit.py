"""부족 재료 상품의 포장 용량 확인 (2026-11-01, 고객 사용 검증 후).

부족한 재료 상품에 업소용 대용량(카다이프 1kg·피스타치오 스프레드 3kg …)이 섞여 나오고, 용량을 모르는 상품도
같은 줄에 '추천'처럼 보였다. 상품 제목에서 포장 용량을 읽어 고객이 필요한 양과 비교한다.

* 용량을 제목에서 확인한 상품만 '필요량에 맞음'이라고 말한다. 확인하지 못한 상품은 '용량 미확인'으로 따로 표시하고
  적합하다고 하지 않는다.
* 순서: 필요량을 채우는 가정용 소포장(작은 것부터) → 필요량보다 작은 포장 → 용량 미확인 → 대용량·업소용.
* 재료 형태가 다르면 같은 재료가 아니다: '피스타치오 페이스트'에 '피스타치오 스프레드'·'피스타치오 크림'을,
  '카다이프'에 '카다이프 초콜릿'을 같은 재료로 보지 않는다(목록에서 빼고 몇 개 뺐는지 말한다).
* 값은 제목에 적힌 그대로만 쓴다. 가격·배송비는 판매처 정보이고 여기서 바꾸지 않는다.
"""
from __future__ import annotations

import math
import re
from decimal import Decimal, InvalidOperation

# 재료의 '형태' — 이름에 있는 형태와 상품 제목의 형태가 다르면 다른 상품이다
FORMS = {
    "페이스트": r"페이스트|paste", "스프레드": r"스프레드|spread", "크림": r"(?<!생)(?<!휘핑)크림(?!치즈)",
    "가루": r"가루|분말|파우더|powder", "분태": r"분태|다이스|슬라이스", "시럽": r"시럽|syrup", "소스": r"소스|sauce",
    "오일": r"오일|(?<![가-힣])유(?![가-힣])|oil", "잼": r"(?<![가-힣])잼|jam", "퓨레": r"퓨레|퓌레|puree",
    "음료": r"음료|라떼|드링크|주스|티백|(?<=[가-힣])차(?![가-힣])",   # '볶은 보리차' is not 보리 (2026-11-01) "완제품 과자": r"쿠키|과자|스낵|케이크|타르트|마카롱|초콜릿바|쫀득쿠키|아이스크림",
    "초콜릿": r"초콜릿|초코(?!칩)",
}
_FORM_RX = {k: re.compile(v, re.I) for k, v in FORMS.items()}
BULK_RE = re.compile(r"업소용|대용량|벌크|식자재|업장용|도매|대포장|박스\s*단위")
_SIZE_RE = re.compile(r"(\d+(?:[.,]\d+)?)\s*(kg|킬로그램|킬로|g|그램|ml|mL|ML|리터|L|l)(?![a-zA-Z])")
_COUNT_RE = re.compile(r"(?:[x×X*]\s*(\d{1,3})(?!\s*(?:g|kg|ml|l)))|(\d{1,3})\s*(?:개입|팩|봉|병|통|입|ea|EA)(?![가-힣])")
_TO_BASE = {"kg": ("g", 1000), "킬로그램": ("g", 1000), "킬로": ("g", 1000), "g": ("g", 1), "그램": ("g", 1),
            "ml": ("mL", 1), "리터": ("mL", 1000), "l": ("mL", 1000)}


def forms_of(text: str) -> set[str]:
    return {k for k, rx in _FORM_RX.items() if rx.search(text or "")}


def _core(name: str) -> str:
    return re.sub(r"\s*\(.*?\)\s*", "", name or "").strip()


def package(title: str) -> dict | None:
    """{'each': Decimal, 'count': int, 'total': Decimal, 'unit': 'g'|'mL'} from the title, or None when the title
    does not say one clear size ('100g/200g/500g 중 택1' → None)."""
    sizes = []
    for m in _SIZE_RE.finditer(title or ""):
        unit = _TO_BASE.get(m.group(2).lower())
        if unit is None:
            continue
        try:
            value = Decimal(m.group(1).replace(",", "")) * unit[1]
        except InvalidOperation:
            continue
        sizes.append((value, unit[0], m.end()))
    if not sizes or len({(v, u) for v, u, _e in sizes}) > 1:
        return None
    each, unit, end = sizes[0]
    count = 1
    # Coupang option text: '…, 500g, 2개' / '…, 2개, 500g' — a comma part that is only 'N개' is the number of packs
    parts = [p.strip() for p in (title or "").split(",")]
    plain = [int(x.group(1)) for x in (re.fullmatch(r"(\d{1,3})\s*개", p) for p in parts[1:]) if x]
    m = _COUNT_RE.search(title[end:end + 12]) or _COUNT_RE.search(title)
    if plain:
        count = plain[-1]
    elif m:
        count = int(m.group(1) or m.group(2))
    if not 1 <= count <= 100:
        count = 1
    return {"each": each, "count": count, "total": each * count, "unit": unit}


def _fmt(value: Decimal, unit: str) -> str:
    if unit == "g" and value >= 1000:
        v, u = value / 1000, "kg"
    elif unit == "mL" and value >= 1000:
        v, u = value / 1000, "L"
    else:
        v, u = value, unit
    text = format(v.normalize(), "f") if v != v.to_integral() else format(v.to_integral(), "f")
    return text + u


def size_text(pack: dict) -> str:
    each = _fmt(pack["each"], pack["unit"])
    return each if pack["count"] == 1 else f"{each}×{pack['count']} (총 {_fmt(pack['total'], pack['unit'])})"


# the same thing spelled the way sellers spell it ('모차렐라 치즈' recipe vs '모짜렐라 피자치즈' — 2026-11-01 real run)
SPELLINGS = {"모짜렐라": "모차렐라", "모짜렐라치즈": "모차렐라치즈", "카타이피": "카다이프", "카다이피": "카다이프",
             "파마산": "파르메산", "파마산치즈": "파르메산치즈", "리코타": "리코타", "마스카포네": "마스카르포네",
             "마시멜로우": "마시멜로", "머랭": "머랭", "꾸스꾸스": "쿠스쿠스", "퀴노와": "퀴노아", "올리브오일": "올리브유"}


def _spell(text: str) -> str:
    out = text or ""
    for a, b in SPELLINGS.items():
        out = out.replace(a, b)
    return out


def same_ingredient(ingredient: str, title: str) -> tuple[bool, str | None]:
    """(same?, the other form when not).  Every word of the ingredient name must be in the title (spelling variants
    allowed) and the title must not be another form of it ('피스타치오 페이스트' ≠ '피스타치오 스프레드')."""
    core = _spell(_core(ingredient))
    flat_t = re.sub(r"\s+", "", _spell(title or ""))
    forms = set(FORMS) | {"페이스트", "스프레드"}
    words = [w for w in re.split(r"\s+", core) if len(w) >= 2 and w not in forms] or [re.sub(r"\s+", "", core)]
    if not all(w in flat_t for w in words):
        return False, None
    if len(re.sub(r"\s+", "", core)) == 1:
        # one-letter names ('굴'): '생굴·깐굴·대굴·굴(…' yes, '굴비·굴소스' no (2026-11-06)
        ch = re.escape(re.sub(r"\s+", "", core))
        if not re.search(rf"(?:(?<![가-힣])|(?<=[생깐햇알중대소석봉])){ch}(?![가-힣])", _spell(title or "")):
            return False, None
    mine, theirs = forms_of(core), forms_of(title)
    extra = theirs - mine
    if mine and not (mine & theirs):
        return False, sorted(theirs)[0] if theirs else "형태 미표기"
    if extra:
        return False, sorted(extra)[0]
    return True, None


def arrange(cards: list[dict], need: dict) -> tuple[list[dict], str]:
    """Cards re-ordered and labelled for one ingredient; and one line saying what was checked.

    need = {'name', 'amount': '260'|None, 'unit': 'g'|'mL'|None, 'display': '260g', 'basis': '20개 분량'}"""
    name = need["name"]
    want = None
    if need.get("amount") and need.get("unit") in ("g", "mL"):
        try:
            want = Decimal(str(need["amount"]))
        except InvalidOperation:
            want = None
    kept, other_forms, other_items = [], {}, 0
    for card in cards:
        same, form = same_ingredient(name, card.get("title") or "")
        if not same:
            if form:
                other_forms[form] = other_forms.get(form, 0) + 1
            else:
                other_items += 1
            continue
        title = card.get("title") or ""
        pack = package(title)
        bulk_word = bool(BULK_RE.search(title))
        if pack is None or (want is not None and pack["unit"] != need["unit"]):
            group, label = 2, "용량 미확인 — 판매처에서 용량을 확인해 주세요"
            if bulk_word:
                group, label = 3, "대용량·업소용 표기(용량 미확인)"
        else:
            total, unit = pack["total"], pack["unit"]
            big = Decimal(2000) if want is None else max(Decimal(1000), want * 5)
            if bulk_word or total >= big:
                group = 3
                times = f"의 약 {(total / want).quantize(Decimal(1))}배라" if want else "라"
                label = (f"대용량 {size_text(pack)} — 필요량 {need['display']}{times} 가정에서 쓰기엔 많아요(업소·대가족용)"
                         if want else f"대용량 {size_text(pack)} — 업소·대가족용 포장")
            elif want is None:
                group, label = 2, f"포장 {size_text(pack)} · 필요량이 정해지지 않아 비교하지 않았어요"
            elif want <= total <= max(want * 3, Decimal(500)):
                group, label = 0, f"필요 {need['display']} · 포장 {size_text(pack)} — 필요량을 채우는 가정용 소포장"
            elif total > want:
                times = (total / want).quantize(Decimal(1))
                group, label = 1, f"필요 {need['display']} · 포장 {size_text(pack)} — 필요량의 약 {times}배로 넉넉해요"
            else:
                k = math.ceil(want / total)
                group, label = 1, f"필요 {need['display']} · 포장 {size_text(pack)} — 이 포장 {k}개가 필요해요"
            card["_size"] = float(total)
        card["fit"] = {0: "fits", 1: "partial", 2: "unknown", 3: "bulk"}[group]
        card["fit_label"] = label
        card["fit_size_known"] = pack is not None
        card["_group"] = group
        kept.append(card)
    # 2026-11-12 사용자 결정: 레시피 재료는 오늘·내일 요리하려고 찾는 것 — 같은 양 적합 단계 안에서는 빠른 배송
    # (판매처의 로켓배송 표시) 상품을 먼저. 양 적합 단계(필요량 → 작은 포장 → 미확인 → 대용량)는 그대로 우선한다.
    kept.sort(key=lambda c: (c["_group"], c["_group"] != 3 and c.get("rocket") is not True,
                             c.get("_size", 0) if c["_group"] in (0, 3) else -c.get("_size", 0)))
    for c in kept:
        c.pop("_group", None)
        c.pop("_size", None)
    basis = f"{need['basis']} 기준 " if need.get("basis") else ""
    head = (f"**{name}** — {basis}필요량 **{need['display']}**. 포장 용량을 확인해 필요량을 채우는 가정용 소포장부터 보여 드려요."
            if want is not None else
            f"**{name}** — 레시피에 비교할 수 있는 필요량이 없어(예: 약간·컵), 포장 용량만 표시했어요.")
    fits = sum(1 for c in kept if c["fit"] == "fits")
    unknown = sum(1 for c in kept if c["fit"] == "unknown")
    notes = []
    if want is not None and not fits:
        notes.append("필요량에 맞는 가정용 포장은 찾지 못했어요")
    if unknown:
        notes.append(f"용량이 제목에 없는 {unknown}개는 적합 여부를 판단하지 않았어요")
    if other_forms:
        forms = ", ".join(f"{f} {n}개" for f, n in other_forms.items())
        notes.append(f"다른 형태 상품({forms})은 같은 재료로 보지 않아 뺐어요")
    if other_items:
        notes.append(f"재료 이름이 제목에 없는 상품 {other_items}개는 뺐어요")
    return kept, head + (" " + ". ".join(notes) + "." if notes else "")


def _search_word(need_key: str) -> str:
    return re.sub(r"\s+", "", need_key or "")


def apply(blocks: list[dict], needs: dict | None) -> list[dict]:
    """Recipe shortage products (chat service hook): each product list is matched to the ingredient it was searched
    for, re-ordered and labelled by package size, and preceded by one line saying what was checked.
    Without needs (an ordinary shopping turn) the blocks are returned unchanged."""
    if not needs:
        return blocks
    out = []
    keys = list(needs)
    # the chat service adds exactly one block per search word, in order (a list, a 'not found' line or a warning)
    by_order = len(blocks) == len(keys)
    for n, block in enumerate(blocks):
        if block.get("type") != "product_list" or not isinstance(block.get("data"), dict):
            out.append(block)
            continue
        items = block["data"].get("items") or []
        if by_order:
            key = keys[n]
            if needs[key].get("skip"):     # 2026-11-12: 필요량이 없는 검색어(손님이 말한 상품)는 그대로 — 다른 재료 머리말이 붙지 않게
                out.append(block)
                continue
        else:
            flat_titles = [re.sub(r"\s+", "", it.get("title") or "") for it in items]
            key = max(keys, key=lambda k: sum(_search_word(k) in t for t in flat_titles))
        kept, line = arrange([dict(it) for it in items], needs[key])
        for it in kept:
            # 2026-11-01 (after the p22 card work): the screen shows `why` first ('왜 추천했나요'), else `reason`.
            # A size read from the title is a calculation ('비교 계산'); an unknown size is a plain line, never a why.
            label = it.pop("fit_label")
            known = it.pop("fit_size_known")
            it["reason"] = label
            it.pop("reasoning", None)
            # 2026-11-12: 대용량은 추천 이유가 아니라 주의 — '왜 추천했나요'에 넣지 않고 한 줄로만
            it["why"] = [{"text": label, "basis": "calc"}] if known and it.get("fit") != "bulk" else []
            if it.get("rocket") is True and it.get("fit") != "bulk":   # 2026-11-12: 빠른 배송 표시 (도착일 약속은 아님)
                it["why"].append({"text": "쿠팡 로켓배송 표시 — 요리 날짜에 맞춰 받기 쉬운 편 · 도착일은 판매처에서 확인",
                                  "basis": "mall"})
            it["role"] = it["role_label"] = None
        from app.services.chat import blocks as B

        out.append(B.text(line))
        if kept:
            out.append(dict(block, data=dict(block["data"], items=kept)))
        else:
            out.append(B.text(f"'{key}' 상품 중 같은 재료로 볼 수 있는 상품을 찾지 못했어요."))
    return out
