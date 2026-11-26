"""홈 '해외 직구' 칸과 직구 검색 — 부를 때마다 Shopify 에 새로 묻고 저장하지 않는다 (2026-11-26)."""
from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict

from app.services.direct_buy import catalog, rules
from app.services.public_price import fx

NOTICE = ("해외 판매처(Shopify 상점) 상품이에요. trendguide는 판매 당사자가 아니며 주문·결제·배송·환불은 판매처가 맡아요. "
          "가격은 방금 조회한 값이고, 배송비·세금은 결제 화면에서 확인해 주세요.")


def _fx() -> dict | None:
    try:
        return fx.usd_krw()
    except Exception:  # noqa: BLE001 — 환율이 없어도 화면은 달러로
        return None


def _card(o: catalog.Offer, item_status: str, rate: dict | None) -> dict:
    d = asdict(o)
    d["duty"] = rules.duty(o.price, o.currency)
    r = (rate or {}).get("rate")
    d["krw_estimate"] = round(o.price / 100 * r, -2) if (r and o.price is not None and (o.currency or "").upper() == "USD") else None
    d["quarantine"] = item_status != "ok"
    return d


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
    return {"enabled": catalog.enabled(), "notice": NOTICE, "checked_at": int(time.time()), "sections": sections, "fx": rate,
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
            "checked_at": int(time.time()), "products": products, "fx": rate,
            "quarantine_note": ("축산물·생과일 같은 검역 품목은 직구로 들여오기 어려워 상품을 보여 드리지 않아요."
                                if blocked and not rules.show_quarantine() else None),
            "checklist": rules.checklist("quarantine" if blocked else "ok")}
