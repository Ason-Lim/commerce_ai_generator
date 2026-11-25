"""셀러 대시보드 (창 5, 2026-11-25) — 셀러가 한눈에 보는 판매 현황·상품 상태. 스마트스토어 '판매 관리' 첫 화면을 참고했다.

* 셀러 코드로만 자기 자료를 본다(격리). 받는 분 정보는 쓰지 않는다(주문 수·수량·날짜만).
* 판매 현황 = 셀러가 올린 판매처 주문(seller_order) 기준. 주문 금액은 주문 파일에 없어서 **현재 판매가 × 수량으로 추정**하고
  그렇게 밝힌다(정산 금액 아님). 판매가가 없는 상품은 금액에서 빠진 수를 함께 알린다.
* 방문·클릭은 아직 재지 않는다(health.clicks_for = None) → '측정 준비 중'으로 보이고 0 으로 꾸미지 않는다.
* 기간: day(오늘·어제) · week(최근 7일·그 전 7일) · month(최근 30일·그 전 30일). 날짜는 주문일(없으면 올린 날, KST).
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta

from sqlalchemy import select

from app.services.seller import health, products, scm, store

PERIODS = {"day": (1, "오늘", "어제"), "week": (7, "최근 7일", "그 전 7일"), "month": (30, "최근 30일", "그 전 30일")}
SERIES_DAYS = {"day": 7, "week": 14, "month": 30}  # 막대 그래프에 보이는 날 수


def _day(r) -> date | None:
    if r["ordered_on"]:
        try:
            return date.fromisoformat(r["ordered_on"])
        except ValueError:
            pass
    t = r["created_at"]
    if t is None:
        return None
    t = t if t.tzinfo else t.replace(tzinfo=store.KST)
    return t.astimezone(store.KST).date()


def _change(cur: int | None, prev: int | None) -> int | None:
    """전 기간 대비 % (전 기간이 0 이면 None — '비교할 판매 없음')."""
    if cur is None or not prev:
        return None
    return round((cur - prev) * 100 / prev)


def build(eng, seller_id: str, *, period: str = "week", at: datetime | None = None) -> dict:
    if period not in PERIODS:
        raise store.SellerError("기간은 day·week·month 중 하나예요")
    at = at or store.now()
    today = at.astimezone(store.KST).date()
    n, cur_label, prev_label = PERIODS[period]
    cur_from = today - timedelta(days=n - 1)
    prev_from, prev_to = cur_from - timedelta(days=n), cur_from - timedelta(days=1)

    with eng.connect() as c:
        prods = (
            c.execute(select(products.t_product).where(products.t_product.c.seller_id == seller_id)).mappings().all()
        )
        orders = c.execute(select(scm.t_order).where(scm.t_order.c.seller_id == seller_id)).mappings().all()
    on = products.listing_of(eng, seller_id)
    stock = scm.stock_of(scm.engine(), seller_id)
    price = {p["product_id"]: p["price"] for p in prods}
    name = {p["product_id"]: p["name"] + (f" {p['volume']}" if p["volume"] else "") for p in prods}

    # ── 상품 상태 (스마트스토어 '상품 관리' 칸) ──
    states: dict[str, int] = defaultdict(int)
    state_of = {}
    for p in prods:
        st = products.sale_state(
            p["status"], on.get(p["product_id"], True) and p["status"] != "withdrawn",
            stock.get(p["product_id"], {}).get("sold_out", False),
        )  # fmt: skip
        state_of[p["product_id"]] = st
        states[st] += 1

    # ── 주문 상태 ──
    flow = {"new": 0, "po": 0, "shipped": 0}
    delayed = 0
    for o in orders:
        flow[o["status"]] = flow.get(o["status"], 0) + 1
        if o["status"] != "shipped" and scm._delayed(o, at):
            delayed += 1

    # ── 판매 현황 (기간 · 전 기간) ──
    def window(lo: date, hi: date) -> dict:
        rows = [o for o in orders if (d := _day(o)) and lo <= d <= hi]
        amount, unpriced = 0, 0
        for o in rows:
            if price.get(o["product_id"]) is None:
                unpriced += 1
            else:
                amount += price[o["product_id"]] * o["qty"]
        return {"orders": len({o["store_order_no"] for o in rows}), "lines": len(rows),
                "qty": sum(o["qty"] for o in rows), "amount": amount, "unpriced": unpriced, "rows": rows}  # fmt: skip

    cur, prev = window(cur_from, today), window(prev_from, prev_to)

    # ── 날짜별 (막대) ──
    days = SERIES_DAYS[period]
    by_day: dict[date, dict] = {today - timedelta(days=i): {"orders": set(), "qty": 0} for i in range(days)}
    for o in orders:
        d = _day(o)
        if d in by_day:
            by_day[d]["orders"].add(o["store_order_no"])
            by_day[d]["qty"] += o["qty"]
    series = [{"day": d.isoformat(), "orders": len(v["orders"]), "qty": v["qty"]} for d, v in sorted(by_day.items())]

    # ── 상품별 판매 (이번 기간) — 판매 0 인 판매 중 상품도 아래에 보인다 ──
    per: dict[str, dict] = {}
    for o in cur["rows"]:
        x = per.setdefault(o["product_id"], {"qty": 0, "orders": set()})
        x["qty"] += o["qty"]
        x["orders"].add(o["store_order_no"])
    prev_qty: dict[str, int] = defaultdict(int)
    for o in prev["rows"]:
        prev_qty[o["product_id"]] += o["qty"]
    table = []
    for p in prods:
        pid = p["product_id"]
        x = per.get(pid, {"qty": 0, "orders": set()})
        st = stock.get(pid, {})
        table.append(
            {
                "product_id": pid,
                "name": name[pid],
                "state": state_of[pid],
                "state_label": products.SALE_STATES[state_of[pid]],
                "price": price[pid],
                "qty": x["qty"],
                "orders": len(x["orders"]),
                "amount": price[pid] * x["qty"] if price[pid] is not None else None,
                "prev_qty": prev_qty.get(pid, 0),
                "stock": st.get("stock"),
                "restock_on": st.get("restock_on"),
            }
        )
    table.sort(key=lambda r: (-r["qty"], r["state"] != "on_sale", r["name"]))

    since = datetime.combine(cur_from, datetime.min.time(), tzinfo=store.KST)
    clicks = health.clicks_for(seller_id, since)
    out = {
        "period": period,
        "labels": {"current": cur_label, "previous": prev_label},
        "range": {"from": cur_from.isoformat(), "to": today.isoformat()},
        "sales": {
            "orders": cur["orders"],
            "qty": cur["qty"],
            "amount": cur["amount"],
            "unpriced": cur["unpriced"],
            "prev": {"orders": prev["orders"], "qty": prev["qty"], "amount": prev["amount"]},
            "change": {
                "orders": _change(cur["orders"], prev["orders"]),
                "qty": _change(cur["qty"], prev["qty"]),
                "amount": _change(cur["amount"], prev["amount"]),
            },
            "amount_note": "주문 금액은 현재 판매가 × 수량으로 계산한 추정이에요(할인·배송비·취소 빼지 않음, 정산 금액 아님).",
        },  # fmt: skip
        "visits": {
            "clicks": clicks,
            "note": None if clicks is not None else "방문·클릭 수는 아직 재지 않아요(준비 중).",
        },
        "orders_flow": {**flow, "delayed": delayed},
        "products": {k: states.get(k, 0) for k in products.SALE_STATES} | {"total": len(prods)},
        "series": series,
        "by_product": table,
        "updated_at": at.astimezone(store.KST).strftime("%Y-%m-%d %H:%M"),
    }
    return out


def my_dashboard(eng, token: str, client: str, *, period: str = "week", at: datetime | None = None) -> dict:
    """셀러 화면 — 대시보드 + 알림·확인 요청·문의 수."""
    from app.services.cs import tickets
    from app.services.seller import chat as seller_chat

    s = store.resolve(eng, token, client)
    d = build(eng, s["seller_id"], period=period, at=at)
    alerts = scm._alerts_for(scm.engine(), s["seller_id"], at or store.now())
    d["alerts"] = {"sold_out": len(alerts["sold_out"]), "delayed": alerts["delayed_orders"],
                   "no_tracking": alerts["no_tracking"], "new_orders": alerts["new_orders"]}  # fmt: skip
    sig = health.signals(eng, dict(s), at or store.now())
    d["confirm"] = {"ask": sig["change_days"] >= health.ASK_DAYS, "change_days": sig["change_days"]}
    try:
        own = seller_chat.owner(s["seller_id"])
        d["asks"] = {"open": tickets.open_count(own),
                     "answered": sum(1 for a in tickets.for_owner(own) if a.get("status") == "answered")}  # fmt: skip
    except Exception:  # noqa: BLE001 — 문의 저장소가 없어도 대시보드는 보인다
        d["asks"] = {"open": None, "answered": None}
    return d
