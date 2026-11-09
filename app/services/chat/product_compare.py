"""추천 상품 비교 (2026-11-06 p35) — '굴 상품 비교' 칩.

레시피 후보 비교처럼, 방금 보여 준 상품 후보(state['seen'])를 새 검색 없이 같은 기준으로 한 표에 견준다.

* 값은 서버가 보여 준 후보에서만 가져온다(브라우저가 보낸 값은 받지 않는다). 가격은 확인 시각을 함께 적는다.
* 포장 용량은 상품 제목에 적힌 값만 쓴다(pack_fit.package). 제목에 없으면 '용량 미확인'이고 100g당 가격을 계산하지 않는다.
* 100g당 가격은 같은 단위(g)끼리만, 용량을 확인한 상품끼리만 비교한다.
* 필요량이 있으면(굴전·굴국밥 몇 kg) pack_fit 과 같은 기준으로 '필요량 충족 · 부족 · 대용량'을 적는다.
* 판매자 표기(프리미엄·최상급 …)는 확인하지 않은 판매자 주장으로만 적는다.
* 제휴 여부는 행마다 표시하고, 비교 순서·'가장 낮은 가격' 표시에 제휴 가산점은 없다.
* 판매처 이동은 /go/… (또는 쇼핑커넥트 발급 링크 그대로) — 일반 상품 카드와 같은 최상위 새 탭 이동.
"""
from __future__ import annotations

import math
import re
from decimal import Decimal

from app.services.recipe_chat import pack_fit

COMPARE_RE = re.compile(r"^\s*(.{1,20}?)\s*상품\s*(후보\s*)?비교(\s*해\s*(줘|주세요)|\s*하기)?\s*[.?!]?\s*$")

# 손질 상태가 먹는 양을 크게 바꾸는 재료 — 표기만 읽는다(확인한 사실 아님)
PREP_MARKS = {
    "굴": (re.compile(r"깐\s*(대|중|소)?\s*굴|알\s*굴|굴\s*알|탈각|(?<![가-힣])깐(?![가-힣])"), re.compile(r"각\s*굴|석화|껍질\s*(굴|째)|하프\s*셸"),
          "깐굴 표기", "껍질째 표기", "손질 상태 미표기"),
}
PREP_CTA = {"굴": "깐굴 표기"}      # 비교 카드 한 줄 설명에 넣는 손질 표기 이름


def cta(name: str, count: int, need: dict | None) -> dict:
    """목록 끝 비교 카드 (A안) — 무엇을 비교하는지 한 줄로."""
    from app.services.chat import blocks as B

    key = re.sub(r"\s+", "", name)
    parts = ["총가격", "100g당 가격"]
    if need and need.get("display"):
        parts.append(f"필요량 {need['display']} 대비")
    if key in PREP_CTA:
        parts.append(PREP_CTA[key])
    return B.compare_cta(f"{name} 상품 {count}개, 한눈에 비교하기", " · ".join(parts), f"{name} 상품 비교")


FIT_SHORT = {"fits": "필요량 충족", "partial": None, "unknown": "용량 미확인", "bulk": "대용량"}


def asked_name(text: str) -> str | None:
    m = COMPARE_RE.match(text or "")
    if not m:
        return None
    name = m.group(1).strip()
    if re.search(r"관심|찜|레시피", name):
        return None
    return name or None


def find_set(state: dict, name: str) -> dict | None:
    flat = re.sub(r"\s+", "", name)
    for s in reversed(state.get("seen") or []):
        if re.sub(r"\s+", "", s.get("query") or "") == flat:
            return s
    return None


def need_for(state: dict, name: str) -> dict | None:
    dp = state.get("dish_purchase") or {}
    need = dp.get("need")
    if need and re.sub(r"\s+", "", need.get("name") or "") == re.sub(r"\s+", "", name):
        return dict(need)
    return None


def _prep(name: str, title: str) -> str | None:
    marks = PREP_MARKS.get(re.sub(r"\s+", "", name))
    if not marks:
        return None
    peeled, shell, yes, shell_label, unknown = marks
    if peeled.search(title or ""):
        return yes
    if shell.search(title or ""):
        return shell_label
    return unknown


def _price(card: dict) -> int | None:
    v = card.get("total") if card.get("total") is not None else card.get("price")
    try:
        v = int(v)
    except (TypeError, ValueError):
        return None
    return v if v > 0 else None


def build(name: str, seen_set: dict, need: dict | None, go_for) -> dict:
    """seen_set: {'query','at','cards'}.  go_for(card) -> '/go/…' path.  Returns the product_compare block data."""
    # 업체 제공 상품(partner)은 같은 기준으로 견주지 않는다고 안내한 상품이라 비교 표에서 뺀다
    cards = [dict(c) for c in seen_set.get("cards") or [] if c.get("title") and not c.get("partner")]
    dropped_line = None
    if need:
        cards, dropped_line = pack_fit.arrange(cards, need)
    want = None
    if need and need.get("amount") and need.get("unit") in ("g", "mL"):
        want = Decimal(str(need["amount"]))
    rows = []
    for c in cards:
        pack = pack_fit.package(c.get("title") or "")
        price = _price(c)
        per100 = None
        if pack and price and pack["unit"] == "g" and pack["total"] > 0:
            per100 = int((Decimal(price) * 100 / pack["total"]).quantize(Decimal(1)))
        fit = c.get("fit")
        if fit == "partial" and pack and want:
            fit_text = (f"필요량의 약 {(pack['total'] / want).quantize(Decimal(1))}배" if pack["total"] > want
                        else f"{math.ceil(want / pack['total'])}개 필요")
        else:
            fit_text = FIT_SHORT.get(fit) if fit else None
        rows.append({
            "key": c.get("key"), "rank": c.get("rank"), "title": c.get("title"), "image": c.get("image"),
            "mall": c.get("mall") or c.get("source"), "go": go_for(c), "url": c.get("url"), "direct": bool(c.get("direct")),
            "affiliate": bool(c.get("affiliate")), "affiliate_program": c.get("affiliate_program"),
            "total": price, "shipping_included": c.get("total") is not None, "free_shipping": c.get("free_shipping"),
            "pack": pack_fit.size_text(pack) if pack else None,
            "per100g": per100, "per100g_unit": "100g" if per100 is not None else None,
            "fit": fit, "fit_text": fit_text,
            "prep": _prep(name, c.get("title") or ""),
            "seller_claims": list(c.get("seller_claims") or []),
        })
    # '가장 낮은' 표시 — 같은 기준끼리만. 필요량이 있으면 필요량을 채우는 상품 중에서.
    pool = [r for r in rows if r["total"] is not None and (not need or r["fit"] in ("fits", "partial"))]
    if need:
        pool = [r for r in pool if r["fit"] == "fits"] or pool
    best_total = min(pool, key=lambda r: r["total"])["key"] if len(pool) > 1 else None
    per_pool = [r for r in rows if r["per100g"] is not None]
    best_per = min(per_pool, key=lambda r: r["per100g"])["key"] if len(per_pool) > 1 else None
    notes = []
    unknown = sum(1 for r in rows if r["pack"] is None)
    if unknown:
        notes.append(f"제목에 용량이 없는 {unknown}개는 100g당 가격을 계산하지 않았어요.")
    if any(r["prep"] == "손질 상태 미표기" for r in rows):
        notes.append("'깐굴' 표기가 없는 상품은 껍질 무게가 섞였을 수 있어 100g당 가격을 그대로 견주기 어려워요.")
    if any(r["seller_claims"] for r in rows):
        notes.append("판매자 표기(프리미엄·최상급 등)는 판매자 주장이며 확인하지 않았어요.")
    notes.append("평점·후기·도착일은 판매처 검색 API가 주지 않아 비교하지 않았어요. 판매처 페이지에서 확인해 주세요.")
    if dropped_line and "뺐어요" in dropped_line:
        notes.append("같은 재료로 볼 수 없는 상품은 비교에서 뺐어요.")
    return {
        "title": f"{name} 추천 상품 비교",
        "need": ({"display": need.get("display"), "basis": need.get("basis")} if need else None),
        "seen_at": seen_set.get("at"),
        "rows": rows, "best_total": best_total, "best_per100g": best_per, "notes": notes,
    }
