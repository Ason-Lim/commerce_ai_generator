"""행사별 매출·매입 정산 (2026-11-24) — 설계 claude/b2b_stage2_settle_2026-11-24.md.

commerce_ai 가 발주처(회사)에 팔고 공급사에서 사는 구조에서, 폐쇄몰 하나(행사 하나)의 돈을 한 화면에.

* 매출(발주처): 계약값 — 1인 금액 · 부가세 기준 · 청구 기준(계약 인원 / 실제 주문 수) · 계약 인원. 몰 설정 ``contract``.
  문의에서 만든 몰은 문의의 인원·1인 예산이 처음 값('확정 전' 표시) — 운영자가 계약서대로 고친다.
* 매입(공급사): 취소 안 된 정식 발주서 합계. 아직 발주서로 안 묶인 주문은 상품 매입 단가 × 수량으로 **추정**하고
  따로 표시한다. 단가가 없는 상품이 있으면 그 금액은 '확인 필요'로 두고 합에 넣지 않는다(0원으로 치지 않음).
* 마진 = 매출 공급가액 − 매입 공급가액 (부가세 빼고 비교). 매입에 확인 필요가 있으면 마진도 '확정 아님'.
* 세금계산서: 매출 발행(날짜·메모) / 발주서별 매입 수취(날짜·메모) 체크.
* 금액은 모두 원 단위 정수. 부가세 포함 금액의 공급가액은 ÷1.1 반올림.
"""

from __future__ import annotations

from datetime import date

from sqlalchemy import and_, func, select, update

from app.services.corpmall import store

BASES = {"headcount": "계약 인원", "orders": "실제 주문 수(고른 사람 + 기본 선물)"}


def _split(amount: int, vat_mode: str) -> tuple[int, int, int]:
    """(공급가액, 부가세, 합계)."""
    if vat_mode == "included":
        supply = round(amount / 1.1)
        return supply, amount - supply, amount
    vat = round(amount * 0.1)
    return amount, vat, amount + vat


def set_contract(eng, mall_id: str, raw: dict, *, by: str = "operator") -> dict:
    """계약값 저장 — 1인 금액·부가세 기준·청구 기준·계약 인원·세금계산서 발행."""
    m = store.get_mall(eng, mall_id=mall_id)
    if m is None:
        raise store.MallError("없는 몰")
    cur = dict(m.get("contract") or {})

    def _int(k, lo, hi, what):
        v = raw.get(k, cur.get(k))
        if v in (None, ""):
            return None
        try:
            n = int(str(v).replace(",", ""))
        except ValueError as e:
            raise store.MallError(f"{what}은(는) 숫자로 적어 주세요") from e
        if not lo <= n <= hi:
            raise store.MallError(f"{what}이(가) 너무 크거나 작아요")
        return n

    out = {
        "unit_price": _int("unit_price", 0, 10_000_000, "1인 금액"),
        "headcount": _int("headcount", 1, 1_000_000, "계약 인원"),
        "vat_mode": raw.get("vat_mode", cur.get("vat_mode") or "included"),
        "basis": raw.get("basis", cur.get("basis") or "headcount"),
        "source": "계약값(운영자 입력)",
        "invoice_issued_on": raw.get("invoice_issued_on", cur.get("invoice_issued_on")) or None,
        "invoice_memo": " ".join(str(raw.get("invoice_memo", cur.get("invoice_memo")) or "").split())[:200] or None,
    }
    if out["vat_mode"] not in ("included", "excluded") or out["basis"] not in BASES:
        raise store.MallError("부가세 기준·청구 기준을 다시 골라 주세요")
    if out["invoice_issued_on"]:
        try:
            out["invoice_issued_on"] = date.fromisoformat(out["invoice_issued_on"]).isoformat()
        except ValueError as e:
            raise store.MallError("세금계산서 발행일을 날짜로 골라 주세요") from e
    with eng.begin() as c:
        r = c.execute(select(store.t_mall.c.payload).where(store.t_mall.c.mall_id == mall_id)).scalar()
        c.execute(update(store.t_mall).where(store.t_mall.c.mall_id == mall_id).values(payload={**r, "contract": out}))
        store._event(c, mall_id, "contract", {"by": by, "invoice": bool(out["invoice_issued_on"])})
    return out


def set_po_invoice(
    eng, mall_id: str, po_no: str, *, received_on: str | None, memo: str = "", by: str = "operator"
) -> None:
    """발주서별 매입 세금계산서 받음 표시(날짜) — 비우면 표시 지움."""
    from datetime import datetime

    at = None
    if received_on:
        try:
            d = date.fromisoformat(received_on)
        except ValueError as e:
            raise store.MallError("받은 날을 날짜로 골라 주세요") from e
        at = datetime(d.year, d.month, d.day, tzinfo=store.KST)
    with eng.begin() as c:
        n = c.execute(
            update(store.t_po)
            .where(
                and_(store.t_po.c.po_no == po_no, store.t_po.c.mall_id == mall_id, store.t_po.c.status != "cancelled")
            )
            .values(invoice_received_at=at, invoice_memo=" ".join((memo or "").split())[:200] or None)
        ).rowcount
        if not n:
            raise store.MallError("없거나 취소된 발주서예요")
        store._event(c, mall_id, "po_invoice", {"po_no": po_no, "received": bool(at), "by": by})


def summary(eng, mall_id: str) -> dict:
    m = store.get_mall(eng, mall_id=mall_id)
    if m is None:
        raise store.MallError("없는 몰")
    ct = m.get("contract") or {}
    items = {i["id"]: i for i in m["items"]}
    with eng.connect() as c:
        orders = dict(
            c.execute(
                select(store.t_order.c.item_id, func.count())
                .where(store.t_order.c.mall_id == mall_id)
                .group_by(store.t_order.c.item_id)
            ).all()
        )
        in_po = dict(
            c.execute(
                select(store.t_po_line.c.item_id, func.count())
                .join(store.t_po_batch, store.t_po_batch.c.batch_id == store.t_po_line.c.batch_id)
                .where(store.t_po_batch.c.mall_id == mall_id)
                .group_by(store.t_po_line.c.item_id)
            ).all()
        )
        pos = (
            c.execute(
                select(store.t_po)
                .where(and_(store.t_po.c.mall_id == mall_id, store.t_po.c.status != "cancelled"))
                .order_by(store.t_po.c.po_no)
            )
            .mappings()
            .all()
        )
    n_orders = sum(orders.values())
    # 매출
    revenue = None
    count = ct.get("headcount") if ct.get("basis", "headcount") == "headcount" else n_orders
    if ct.get("unit_price") is not None and count:
        s, v, t = _split(ct["unit_price"] * count, ct.get("vat_mode") or "included")
        revenue = {"count": count, "supply": s, "vat": v, "total": t}
    # 매입: 발주서 + 아직 안 묶인 주문 추정
    po_rows, po_supply, po_total, po_unknown = [], 0, 0, 0
    for p in pos:
        po_rows.append(
            {
                "po_no": p["po_no"],
                "supplier": p["supplier_name"],
                "supply": p["supply_amount"],
                "vat": p["vat"],
                "total": p["total"],
                "status": p["status"],
                "invoice_received_on": p["invoice_received_at"].date().isoformat()
                if p["invoice_received_at"]
                else None,
                "invoice_memo": p["invoice_memo"],
            }
        )
        if p["total"] is None:
            po_unknown += 1
        else:
            po_supply += p["supply_amount"]
            po_total += p["total"]
    est_supply, est_unknown, est_lines = 0, 0, []
    for iid, n in orders.items():
        left = n - in_po.get(iid, 0)
        if left <= 0:
            continue
        it = items.get(iid, {})
        cost = it.get("unit_cost")
        if cost is None:
            est_unknown += left
            est_lines.append({"item": it.get("name") or iid, "qty": left, "supply": None})
            continue
        from app.services.corpmall import suppliers as sup

        vat_mode = "excluded"
        if it.get("supplier_id"):
            ms = sup.get(eng, it["supplier_id"])
            vat_mode = (ms or {}).get("vat_mode", "excluded")
        s, _, _ = _split(cost * left, vat_mode)
        est_supply += s
        est_lines.append({"item": it.get("name") or iid, "qty": left, "supply": s})
    cost_complete = po_unknown == 0 and est_unknown == 0
    margin = None
    if revenue is not None:
        margin = {
            "amount": revenue["supply"] - po_supply - est_supply,
            "rate": round((revenue["supply"] - po_supply - est_supply) / revenue["supply"], 4)
            if revenue["supply"]
            else None,
            "final": cost_complete and est_supply == 0,
        }
    return {
        "mall_id": mall_id,
        "slug": m["slug"],
        "client": m.get("client"),
        "title": m.get("title"),
        "status": m["status"],
        "contract": ct,
        "basis_label": BASES.get(ct.get("basis", "headcount")),
        "orders": n_orders,
        "issued": store.stats(eng, mall_id)["issued"],
        "revenue": revenue,
        "cost": {
            "po": po_rows,
            "po_supply": po_supply,
            "po_total": po_total,
            "po_unknown": po_unknown,
            "estimate": est_lines,
            "estimate_supply": est_supply,
            "estimate_unknown_qty": est_unknown,
            "complete": cost_complete,
        },
        "margin": margin,
        "invoices": {
            "sales_issued_on": ct.get("invoice_issued_on"),
            "purchase_received": sum(1 for p in po_rows if p["invoice_received_on"]),
            "purchase_total": len(po_rows),
        },
    }


def overview(eng) -> list[dict]:
    """모든 몰의 정산 요약(관리자 B2B > 정산)."""
    out = []
    for m in store.list_malls(eng):
        s = summary(eng, m["mall_id"])
        out.append(
            {
                k: s[k]
                for k in ("mall_id", "slug", "client", "title", "status", "orders", "revenue", "margin", "invoices")
            }
            | {
                "cost_complete": s["cost"]["complete"],
                "cost_supply": s["cost"]["po_supply"] + s["cost"]["estimate_supply"],
            }
        )
    return out


__all__ = ["BASES", "set_contract", "set_po_invoice", "summary", "overview"]
