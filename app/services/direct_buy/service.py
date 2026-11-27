"""해외 직구 검색 — 부를 때마다 Shopify 에 새로 묻고 저장하지 않는다 (2026-11-26).

2026-11-27: 홈 칸은 화면에서 뺌(사용자 결정) — 대화 검색어가 품목표(items.py)에 맞을 때 결과 아래 칸이 search_item 을 부른다.
가격은 판매처 통화 그대로 + 관세청 과세환율로 바꾼 원화·달러(면세 한도 비교) — 출처·기준일 함께."""
from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict

from app.services.direct_buy import catalog, items, rules, savings
from app.services.public_price import fx

NOTICE = ("해외 판매처(Shopify 상점) 상품이에요. trendguide는 판매 당사자가 아니며 주문·결제·배송·환불은 판매처가 맡아요. "
          "가격은 방금 조회한 값이고, 배송비·세금은 결제 화면에서 확인해 주세요.")


# 통화별 소수 자리 (Shopify 금액은 최소 단위 정수) — ISO 4217 에서 소수 없는 통화
ZERO_DECIMAL = frozenset({"KRW", "JPY", "VND", "CLP", "ISK", "UGX", "PYG", "XAF", "XOF"})


def _fx() -> dict | None:
    """{rate, source, date, kind, stale, table} — table 은 관세청 표가 있을 때만(다른 통화 환산용)."""
    try:
        usd = fx.usd_krw()
    except Exception:  # noqa: BLE001 — 환율이 없어도 화면은 판매처 통화로
        usd = None
    if not usd:
        return None
    table = None
    if usd.get("kind") == "customs":
        try:
            t = fx.customs_table()
            table = (t or {}).get("rates")
        except Exception:  # noqa: BLE001
            table = None
    return {**usd, "table": table}


def _krw(price: int | None, cur: str | None, rate: dict | None) -> float | None:
    if price is None or not cur:
        return None
    cur = cur.upper()
    amount = price if cur in ZERO_DECIMAL else price / 100
    if cur == "KRW":
        return float(amount)
    per = ((rate or {}).get("table") or {}).get(cur) or ((rate or {}).get("rate") if cur == "USD" else None)
    return amount * per if per else None


def _card(o: catalog.Offer, item_status: str, rate: dict | None) -> dict:
    d = asdict(o)
    krw = _krw(o.price, o.currency, rate)
    usd_rate = (rate or {}).get("rate")
    usd = (krw / usd_rate) if (krw is not None and usd_rate and (o.currency or "").upper() != "USD") else None
    d["duty"] = rules.duty(o.price, o.currency, usd)
    d["krw_estimate"] = round(krw, -2) if (krw is not None and (o.currency or "").upper() != "KRW") else None
    d["quarantine"] = item_status != "ok"
    return d


def _public_fx(rate: dict | None) -> dict | None:
    return {k: v for k, v in rate.items() if k != "table"} if rate else None


def _section(item: dict, *, limit: int, http, rate: dict | None = None) -> dict:
    sec = {k: item.get(k) for k in ("key", "label", "status", "note")}
    sec["products"], sec["error"] = [], None
    if item["status"] == "blocked" or not item.get("query") or (item["status"] == "quarantine" and not rules.show_quarantine()):
        return sec
    res = catalog.search(item["query"], limit=limit + 4, http=http)
    if not res.ok:
        sec["error"] = res.error
        return sec
    sec["products"] = [_card(o, item["status"], rate) for o in res.offers if rules.keep(o.title, item_status=item["status"])][:limit]
    return sec


def home(*, limit: int = 6, http=None) -> dict:
    http = http or catalog.requests
    rate = _fx()
    with ThreadPoolExecutor(max_workers=3) as ex:
        sections = list(ex.map(lambda it: _section(it, limit=limit, http=http, rate=rate), rules.HOME_ITEMS))
    return {"enabled": catalog.enabled(), "notice": NOTICE, "checked_at": int(time.time()), "sections": sections, "fx": _public_fx(rate),
            "checklist": rules.checklist(), "source": "Shopify Global Catalog"}


def search(q: str, *, limit: int = 12, http=None) -> dict:
    http = http or catalog.requests
    res = catalog.search(q, limit=limit + 4, http=http)
    blocked = bool(rules.QUARANTINE.search(q or ""))
    rate = _fx() if res.ok else None
    products = [_card(o, "quarantine" if blocked else "ok", rate) for o in res.offers
                if rules.keep(o.title, item_status="quarantine" if blocked else "ok")][:limit] if res.ok else []
    if blocked and not rules.show_quarantine():
        products = []
    return {"enabled": catalog.enabled(), "query": q, "ok": res.ok, "error": res.error, "notice": NOTICE,
            "checked_at": int(time.time()), "products": products, "fx": _public_fx(rate),
            "quarantine_note": ("축산물·생과일 같은 검역 품목은 직구로 들여오기 어려워 상품을 보여 드리지 않아요."
                                if blocked and not rules.show_quarantine() else None),
            "checklist": rules.checklist("quarantine" if blocked else "ok")}


def search_item(key: str, *, limit: int = 6, http=None, ref: dict | None = None) -> dict:
    """대화 결과 아래 칸 (2026-11-27) — 품목표의 영어 검색어로 찾는다. blocked 는 부르지 않고 안내만.
    ref: 이번 대화 쿠팡 후보의 100g(ml)당 중간값(savings.parse_ref) — 있으면 '직구 추정 약 n% 저렴'을 붙인다(15% 이상일 때만)."""
    it = items.by_key(key)
    if it is None:
        return {"enabled": catalog.enabled(), "ok": False, "error": "모르는 품목", "products": []}
    base = {"enabled": catalog.enabled(), "key": it.key, "label": it.label, "status": it.status, "note": it.note or None,
            "notice": NOTICE, "source": "Shopify Global Catalog", "checklist": rules.checklist(it.status, it.note or None)}
    if it.status == "blocked" or not it.query:
        return {**base, "ok": True, "error": None, "products": [], "fx": None, "checked_at": int(time.time())}
    http = http or catalog.requests
    res = catalog.search(it.query, limit=limit + 4, http=http)
    rate = _fx() if res.ok else None
    products = [_card(o, it.status, rate) for o in res.offers if rules.keep(o.title, item_status="ok")][:limit] if res.ok else []
    usd_rate = (rate or {}).get("rate")
    for p in products:
        krw = _krw(p.get("price"), p.get("currency"), rate)
        size = p.get("option") if savings.amount(p.get("option")) else p.get("title")   # 가격은 옵션 값 — 옵션 양을 먼저
        p["saving"] = savings.estimate(size or "", krw, ref, usd_rate, label=it.label)
    best = max((p["saving"] for p in products if p.get("saving")), key=lambda s: s["pct"], default=None)
    compare = None
    if ref:
        compare = {"ref": ref, "best": best,
                   "basis": savings.BASIS.format(n=ref["n"], unit="100g" if ref["unit"] == "g" else "100ml")}
    return {**base, "ok": res.ok, "error": res.error, "products": products, "fx": _public_fx(rate), "compare": compare,
            "checked_at": int(time.time())}


def recheck(variant_id: str, price: int | None = None, currency: str | None = None, *, http=None) -> dict:
    """판매처로 가기 전 재확인 (2026-11-27) — 지금 가격·재고를 다시 묻고 화면 값과 견준다. 저장 없음.
    lookup 결과에 같은 옵션이 없으면 첫 판매 가능 옵션을 쓴다(Global Catalog 가 상품 단위로 돌려줄 수 있음)."""
    res = catalog.lookup(variant_id, http=http or catalog.requests)
    base = {"checked_at": int(time.time()), "variant_id": variant_id}
    if not res.ok:
        return {**base, "ok": False, "state": "unknown", "error": res.error,
                "text": "지금 다시 확인하지 못했어요. 판매처 화면에서 가격·재고를 꼭 확인해 주세요."}
    o = next((x for x in res.offers if x.variant_id == variant_id), res.offers[0] if res.offers else None)
    if o is None or o.available is False:
        return {**base, "ok": True, "state": "sold_out", "text": "방금 다시 확인해 보니 한국 배송으로 살 수 없거나 품절이에요."}
    same_cur = (currency or "").upper() == (o.currency or "").upper()
    state = "same" if (price is not None and same_cur and o.price == price) else ("changed" if price is not None and same_cur else "unknown")
    text = {"same": "방금 다시 확인했어요 — 가격이 그대로예요.",
            "changed": "방금 다시 확인해 보니 가격이 바뀌었어요. 아래 새 가격을 보세요.",
            "unknown": "방금 다시 확인했어요. 판매처 화면의 최종 금액을 확인해 주세요."}[state]
    return {**base, "ok": True, "state": state, "text": text, "price": o.price, "currency": o.currency,
            "url": o.url, "checkout_url": o.checkout_url}
