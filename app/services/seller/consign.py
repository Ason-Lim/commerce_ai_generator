"""정식 위탁판매 셀러 지원 (창 5, 2026-11-26) — 로드맵 '입점 심사·상품 등록 규칙·운영 지표, 직접 재고 셀러 먼저 받고
지표 관리 준비 후 개방'.

* **입점 심사표.** 위탁판매 셀러는 심사표가 모두 '확인'이어야 입점 승인(active)할 수 있다. 확인은 운영자만 —
  AI·규칙은 체크하지 않는다. 서류 원본은 받지 않고 운영자가 본 뒤 메모만 남긴다. '공급사 등록'만 셀러 센터 기록으로 자동 확인.
* **상품 등록 규칙.** 위탁판매 셀러의 상품은 공급사(직접 출고가 아닌)를 붙여야 검수 승인된다.
  소매몰(쿠팡·스마트스토어 등)을 공급사로 적는 것은 모든 셀러에게 막는다(차익거래 불허 — 고정 원칙).
* **운영 지표.** 최근 30일 주문(셀러가 올린 판매처 주문)으로 출고 지연율·평균 출고 영업일·출고 대기·품절률·공급사별 지연.
  주문 30건 미만은 '관찰'(판정하지 않음). 기준값은 기본값(정할 것). 지표는 운영자·셀러가 보고 판단하는 자료이고
  자동으로 정지·제재하지 않는다(정지는 운영자만 — 고정 원칙).
"""

from __future__ import annotations

import re
from datetime import date, datetime, timedelta

from sqlalchemy import Boolean, Column, DateTime, MetaData, PrimaryKeyConstraint, String, Table, and_, select, update

from app.services.seller import products, scm, store

meta = MetaData()
t_check = Table(
    "seller_consign_check",
    meta,
    Column("seller_id", String(12), nullable=False),
    Column("item", String(24), nullable=False),
    Column("ok", Boolean, nullable=False, default=False),
    Column("note", String(200)),
    Column("by", String(48)),
    Column("at", DateTime(timezone=True)),
    PrimaryKeyConstraint("seller_id", "item"),
)

# 심사 항목 — (이름, 운영자가 볼 것). supplier_registered 는 셀러 센터 기록으로 자동.
ITEMS: dict[str, tuple[str, str]] = {
    "supplier_contract": (
        "공급사 위탁(공급) 계약",
        "셀러와 공급사의 계약서 — 공급 품목·기간·직접 배송 의무. 원본은 받지 않고 본 뒤 메모",
    ),
    "supplier_registered": ("공급사 등록", "셀러 센터에 공급사 1곳 이상 (자동 확인)"),
    "supplier_ships": ("공급사 직접 배송·송장", "공급사가 손님에게 직접 보내고 송장을 셀러에게 돌려주는 방식"),
    "no_arbitrage": (
        "소매몰 되팔기 아님",
        "공급사가 쿠팡·네이버 같은 소매몰이 아니고, 소매몰에서 사서 보내는 방식이 아님",
    ),
    "return_policy": ("반품·교환 주체·주소", "반품지 주소, 반품비·교환 기준, 누가 받는지"),
    "ship_exception": ("배송 예외 처리 담당·기한", "지연·오배송·파손·분실 때 셀러·공급사 중 누가 언제까지 처리하는지"),
}
AUTO = {"supplier_registered"}
RETAIL_RE = re.compile(
    r"쿠팡|coupang|스마트\s*스토어|smartstore|네이버\s*쇼핑|11\s*번가|11st|g\s*마켓|gmarket|옥션|auction|위메프|티몬|"
    r"ssg|쓱|마켓\s*컬리|컬리|kurly|오늘의\s*집|알리\s*익스프레스|aliexpress|테무|temu|아마존|amazon",
    re.I,
)
WINDOW_DAYS = 30
MIN_ORDERS = 30  # 미만이면 '관찰'
WARN_DELAY = 0.10  # 지연율 10% 넘으면 '주의' (기본값 — 정할 것)
BAD_DELAY = 0.20  # 20% 넘으면 '경고'


def engine(url: str | None = None):
    eng = scm.engine(url)
    meta.create_all(eng)
    return eng


# ── 상품 등록 규칙 ──────────────────────────────────────────────────────
def check_supplier_name(name: str) -> None:
    """소매몰을 공급사로 적지 못하게 — 모든 셀러(차익거래 불허)."""
    if RETAIL_RE.search(name or ""):
        raise store.SellerError(
            "쿠팡·스마트스토어 같은 소매몰은 공급사로 등록할 수 없어요 (소매몰에서 사서 되파는 판매는 받지 않아요)"
        )


def gate_approve(c, seller_id: str, product_id: str) -> None:
    """검수 승인 전 — 위탁판매 셀러 상품은 공급사가 붙어 있어야 한다(같은 트랜잭션 c)."""
    kind = c.execute(select(store.t_seller.c.kind).where(store.t_seller.c.seller_id == seller_id)).scalar()
    if kind != "consign":
        return
    try:
        sup = c.execute(select(scm.t_supply.c.supplier_id).where(scm.t_supply.c.product_id == product_id)).scalar()
    except Exception:  # noqa: BLE001 — 표가 없으면 공급사도 없다
        sup = None
    if not sup:
        raise store.SellerError(
            "위탁판매 셀러 상품은 공급사를 붙여야 승인할 수 있어요 (셀러 센터 '주문·발주·송장' → 상품별 공급사)"
        )


# ── 입점 심사표 ─────────────────────────────────────────────────────────
def _suppliers(eng, seller_id: str) -> int:
    with eng.connect() as c:
        return len(c.execute(select(scm.t_supplier.c.supplier_id).where(scm.t_supplier.c.seller_id == seller_id)).all())


def checklist(eng, seller_id: str) -> dict:
    r = store._row(eng, seller_id)
    if r is None:
        raise store.SellerError("없는 셀러예요")
    with eng.connect() as c:
        rows = {x["item"]: x for x in c.execute(select(t_check).where(t_check.c.seller_id == seller_id)).mappings()}
    n_sup = _suppliers(eng, seller_id)
    items = []
    for key, (label, what) in ITEMS.items():
        if key in AUTO:
            items.append({"item": key, "label": label, "what": what, "ok": n_sup > 0, "auto": True,
                          "note": f"공급사 {n_sup}곳", "by": "", "at": None})  # fmt: skip
            continue
        x = rows.get(key)
        items.append({"item": key, "label": label, "what": what, "ok": bool(x and x["ok"]), "auto": False,
                      "note": (x and x["note"]) or "", "by": (x and x["by"]) or "",
                      "at": x["at"].isoformat() if x and x["at"] else None})  # fmt: skip
    missing = [i["label"] for i in items if not i["ok"]]
    return {"seller_id": seller_id, "name": r["name"], "kind": r["kind"], "status": r["status"],
            "items": items, "ready": not missing, "missing": missing}  # fmt: skip


def set_check(eng, seller_id: str, item: str, ok: bool, *, by: str, note: str = "") -> dict:
    by = store._operator(by)
    if item not in ITEMS or item in AUTO:
        raise store.SellerError("운영자가 확인하는 항목이 아니에요")
    r = store._row(eng, seller_id)
    if r is None or r["kind"] != "consign":
        raise store.SellerError("정식 위탁판매 셀러만 심사표가 있어요")
    note = " ".join((note or "").split())[:200]
    if ok and not note:
        raise store.SellerError("무엇을 보고 확인했는지 메모를 남겨 주세요 (예: 계약서 2026-11-26 확인, 1년)")
    with eng.begin() as c:
        vals = dict(ok=bool(ok), note=note or None, by=by, at=store.now())
        q = update(t_check).where(and_(t_check.c.seller_id == seller_id, t_check.c.item == item)).values(**vals)
        if c.execute(q).rowcount == 0:
            c.execute(t_check.insert().values(seller_id=seller_id, item=item, **vals))
        store._event(c, seller_id, "consign_check", by, {"item": item, "ok": bool(ok)})
    return checklist(eng, seller_id)


def gate_activate(eng, seller_id: str) -> None:
    """입점 승인(active) 전 — 위탁판매 셀러는 심사표가 다 확인돼야 한다."""
    r = store._row(eng, seller_id)
    if r is None or r["kind"] != "consign":
        return
    meta.create_all(eng)
    cl = checklist(eng, seller_id)
    if not cl["ready"]:
        raise store.SellerError(
            "정식 위탁판매 셀러는 입점 심사표를 모두 확인해야 승인할 수 있어요: " + ", ".join(cl["missing"])
        )


# ── 운영 지표 ───────────────────────────────────────────────────────────
def _bizdays(d0: date, d1: date) -> int:
    return scm.biz_days_between(d0, d1)


def metrics(eng, seller_id: str, *, at: datetime | None = None) -> dict:
    """최근 30일 — 주문 수·출고·지연율·평균 출고 영업일·출고 대기(지연 포함)·품절률·공급사별 지연. 받는 분 정보 없음."""
    at = at or store.now()
    since = (at - timedelta(days=WINDOW_DAYS)).date()
    sup = scm.supply_of(eng, seller_id)
    with eng.connect() as c:
        orders = c.execute(select(scm.t_order).where(scm.t_order.c.seller_id == seller_id)).mappings().all()
        names = {
            r["supplier_id"]: r["name"]
            for r in c.execute(select(scm.t_supplier).where(scm.t_supplier.c.seller_id == seller_id)).mappings()
        }
        prods = c.execute(select(products.t_product.c.product_id, products.t_product.c.status)
                          .where(products.t_product.c.seller_id == seller_id)).mappings().all()  # fmt: skip
    rows = [o for o in orders if o["ordered_on"] and date.fromisoformat(o["ordered_on"]) >= since]
    shipped = [o for o in rows if o["status"] == "shipped" and o["shipped_at"]]
    ship_days = [_bizdays(date.fromisoformat(o["ordered_on"]), o["shipped_at"].date()) for o in shipped]
    late_shipped = sum(1 for d in ship_days if d > scm.DELAY_BIZ_DAYS)
    late_open = sum(1 for o in rows if scm._delayed(o, at))
    n = len(rows)
    delay_rate = (late_shipped + late_open) / n if n else None
    by_sup: dict[str, dict] = {}
    for o in rows:
        sid = (sup.get(o["product_id"]) or {}).get("supplier_id")
        key = names.get(sid, "직접 출고") if sid else "직접 출고"
        d = by_sup.setdefault(key, {"supplier": key, "orders": 0, "late": 0})
        d["orders"] += 1
        late = scm._delayed(o, at) or (o["status"] == "shipped" and o["shipped_at"]
                                       and _bizdays(date.fromisoformat(o["ordered_on"]), o["shipped_at"].date()) > scm.DELAY_BIZ_DAYS)  # fmt: skip
        d["late"] += 1 if late else 0
    stocks = scm.stock_of(eng, seller_id)
    approved = [p["product_id"] for p in prods if p["status"] == "approved"]
    sold = sum(1 for pid in approved if (stocks.get(pid) or {}).get("sold_out"))
    if n < MIN_ORDERS:
        level, label = "watch", f"관찰 (주문 {n}건 — {MIN_ORDERS}건부터 판정)"
    elif delay_rate > BAD_DELAY:
        level, label = "bad", f"경고 — 출고 지연 {delay_rate:.0%}"
    elif delay_rate > WARN_DELAY:
        level, label = "warn", f"주의 — 출고 지연 {delay_rate:.0%}"
    else:
        level, label = "ok", f"좋음 — 출고 지연 {delay_rate:.0%}"
    return {
        "seller_id": seller_id, "window_days": WINDOW_DAYS, "orders": n, "shipped": len(shipped),
        "late": late_shipped + late_open, "late_open": late_open, "delay_rate": None if delay_rate is None else round(delay_rate, 3),
        "avg_ship_bizdays": round(sum(ship_days) / len(ship_days), 1) if ship_days else None,
        "waiting": sum(1 for o in rows if o["status"] != "shipped"),
        "approved": len(approved), "sold_out": sold, "sold_out_rate": round(sold / len(approved), 3) if approved else None,
        "by_supplier": sorted(by_sup.values(), key=lambda x: -x["late"]), "level": level, "level_label": label,
        "rule": {"delay_biz_days": scm.DELAY_BIZ_DAYS, "min_orders": MIN_ORDERS, "warn": WARN_DELAY, "bad": BAD_DELAY},
    }  # fmt: skip


def my_metrics(eng, token: str, client: str, *, at: datetime | None = None) -> dict:
    s = store.resolve(eng, token, client)
    return metrics(eng, s["seller_id"], at=at)


def board(eng, *, at: datetime | None = None) -> list[dict]:
    """운영자 화면 — 위탁판매 셀러 먼저: 심사표 상태 + 지표. 직접 재고 셀러는 지표만."""
    out = []
    for s in store.list_sellers(eng):
        if s["status"] == "ended":
            continue
        row = {"seller_id": s["seller_id"], "name": s["name"], "kind": s["kind"], "kind_label": s["kind_label"],
               "status": s["status"], "status_label": s["status_label"], "metrics": metrics(eng, s["seller_id"], at=at)}  # fmt: skip
        if s["kind"] == "consign":
            cl = checklist(eng, s["seller_id"])
            row.update(ready=cl["ready"], missing=cl["missing"], items=cl["items"])
        out.append(row)
    return sorted(out, key=lambda x: (x["kind"] != "consign", x["name"]))


__all__ = ["ITEMS", "board", "check_supplier_name", "checklist", "engine", "gate_activate", "gate_approve", "metrics",
           "my_metrics", "set_check"]  # fmt: skip
