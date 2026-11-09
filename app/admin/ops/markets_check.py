"""판매처 API 상태 점검 — integrated_system /api/debug/markets 를 관리자 기능으로 옮겼다.

판매처(쿠팡 파트너스 · 네이버 쇼핑)마다 같은 검색어로 검색해 건수 · 예시 · 오류를 보여 준다.
키는 서버 .env 에서만 읽고 응답에 넣지 않는다.  오류 본문은 300자까지만 보여 준다.
"""
from __future__ import annotations

import time

from app.admin.shared.config import get_settings
from app.admin.shared.markets.registry import MarketRegistry


def check(query: str, *, registry: MarketRegistry | None = None, limit: int = 10) -> dict:
    reg = registry or MarketRegistry(get_settings())
    out = []
    for a in reg.adapters:
        row = {"code": a.code, "enabled": bool(a.enabled)}
        if not a.enabled:
            row["note"] = "키 미설정 또는 꺼짐"
            out.append(row)
            continue
        started = time.monotonic()
        try:
            got = a.search(query, limit=limit)
            row.update(count=len(got), ms=int((time.monotonic() - started) * 1000),
                       sample=[{"title": o.title[:60], "price": o.price, "shipping_fee": o.shipping_fee,
                                "mall": getattr(o, "mall_label", None) or o.mall} for o in got[:3]])
        except Exception as e:  # noqa: BLE001 — one market's error is the result for that row
            body = getattr(getattr(e, "response", None), "text", "") or ""
            row.update(error=f"{type(e).__name__}: {str(e)[:200]}", body=body[:300],
                       ms=int((time.monotonic() - started) * 1000))
        out.append(row)
    return {"query": query, "markets": out}
