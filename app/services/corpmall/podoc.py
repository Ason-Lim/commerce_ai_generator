"""정식 발주서와 공급사 수신 확인 (2026-11-24) — 설계 claude/b2b_supplier_po_2026-11-24.md.

발주 묶음(po.create_batch)을 만들 때 공급사마다 발주서 하나(`{묶음}-{순번}`)를 만든다.
* 금액: 품목별 매입 단가 × 수량. 거래처 단가 기준이 부가세 별도면 공급가액 = 합, 부가세 = 10%(원 단위 반올림),
  포함이면 합계 = 합, 공급가액 = 합 ÷ 1.1(반올림), 부가세 = 합계 − 공급가액. 단가가 없는 품목이 있으면 금액은 비우고
  '단가 확인 필요'로 둔다(0원으로 계산하지 않음).
* 납기: 몰 매뉴얼의 출고 예정일 → 없으면 발주일 + 거래처 기본 납기(영업일) → 둘 다 없으면 '협의'.
* 금액·조건은 만들 때 값으로 고정된다(나중에 단가를 바꿔도 이미 낸 발주서는 그대로).
* 수신 확인: 운영자가 만든 확인 링크(`/corp/po/{발주 번호}#k=…`, 해시만 저장, 새로 만들면 옛 링크 무효)로 공급사가
  확인자·출고 예정일·메모를 남기거나, 운영자가 메일 답장 등을 보고 직접 표시한다. 확인 화면에는 배송 정보가 없다.
"""

from __future__ import annotations

import hashlib
import re
import secrets
from datetime import date, datetime

from sqlalchemy import and_, select, update

from app.services.corpmall import store

STATUS_LABEL = {"issued": "보냄 · 확인 전", "acknowledged": "공급사 확인", "cancelled": "취소"}


def _money(lines: list[dict], vat_mode: str) -> tuple[int | None, int | None, int | None]:
    if any(ln.get("unit_cost") is None for ln in lines):
        return None, None, None
    s = sum(ln["amount"] for ln in lines)
    if vat_mode == "included":
        supply = round(s / 1.1)
        return supply, s - supply, s
    vat = round(s * 0.1)
    return s, vat, s + vat


def _due(m: dict, lead_days: int | None, issued: datetime) -> str | None:
    plan = (m.get("manual") or {}).get("ship_plan")
    if plan:
        return plan
    if lead_days is not None:
        from app.services.cs import bizdays

        return bizdays.add_bizdays(issued, lead_days).date().isoformat()
    return None


def issue_for_batch(c, m: dict, batch_id: str, take: list) -> list[dict]:
    """create_batch 안(같은 트랜잭션)에서 공급사마다 발주서. take = [(주문 행, 상품)]."""
    from app.services.corpmall import suppliers as sup

    ids = sorted({it.get("supplier_id") for _, it in take if it.get("supplier_id")})
    masters = {}
    if ids:
        for r in c.execute(select(sup.t_supplier).where(sup.t_supplier.c.supplier_id.in_(ids))).mappings():
            masters[r["supplier_id"]] = r
    groups: dict[str, list] = {}
    for r, it in take:
        groups.setdefault(it["supplier"], []).append((r, it))
    out = []
    issued = store.now()
    for k, (name, rows) in enumerate(sorted(groups.items()), start=1):
        sid = rows[0][1].get("supplier_id")
        ms = masters.get(sid) if sid else None
        qty: dict[str, dict] = {}
        for _, it in rows:
            q = qty.setdefault(
                it["id"],
                {
                    "item_id": it["id"],
                    "name": it.get("name"),
                    "sku": it.get("supplier_sku"),
                    "qty": 0,
                    "unit_cost": it.get("unit_cost"),
                },
            )
            q["qty"] += 1
        lines = []
        for q in qty.values():
            q["amount"] = q["unit_cost"] * q["qty"] if q["unit_cost"] is not None else None
            lines.append(q)
        vat_mode = ms["vat_mode"] if ms else "excluded"
        supply, vat, total = _money(lines, vat_mode)
        po_no = f"{batch_id}-{k:02d}"
        rec = {
            "po_no": po_no,
            "batch_id": batch_id,
            "mall_id": m["mall_id"],
            "supplier_id": sid,
            "supplier_name": name,
            "issued_at": issued,
            "due_date": _due(m, ms["lead_days"] if ms else None, issued),
            "payment_terms": ms["payment_terms"] if ms else None,
            "vat_mode": vat_mode,
            "lines": lines,
            "supply_amount": supply,
            "vat": vat,
            "total": total,
            "status": "issued",
        }
        c.execute(store.t_po.insert().values(**rec))
        out.append(rec)
    return out


def _row(r) -> dict:
    return {
        "po_no": r["po_no"],
        "batch_id": r["batch_id"],
        "supplier_id": r["supplier_id"],
        "supplier": r["supplier_name"],
        "issued_at": r["issued_at"].isoformat() if r["issued_at"] else None,
        "due_date": r["due_date"],
        "payment_terms": r["payment_terms"],
        "vat_mode": r["vat_mode"],
        "lines": r["lines"] or [],
        "supply_amount": r["supply_amount"],
        "vat": r["vat"],
        "total": r["total"],
        "needs_cost": r["total"] is None,
        "status": r["status"],
        "status_label": STATUS_LABEL.get(r["status"], r["status"]),
        "ack_at": r["ack_at"].isoformat() if r["ack_at"] else None,
        "ack_by": r["ack_by"],
        "ack_ship_date": r["ack_ship_date"],
        "ack_memo": r["ack_memo"],
        "ack_via": r["ack_via"],
    }


def list_pos(eng, mall_id: str, batch_id: str | None = None) -> list[dict]:
    q = select(store.t_po).where(store.t_po.c.mall_id == mall_id)
    if batch_id:
        q = q.where(store.t_po.c.batch_id == batch_id)
    with eng.connect() as c:
        return [_row(r) for r in c.execute(q.order_by(store.t_po.c.po_no)).mappings()]


def get(eng, po_no: str) -> dict | None:
    with eng.connect() as c:
        r = c.execute(select(store.t_po).where(store.t_po.c.po_no == po_no)).mappings().first()
    return _row(r) | {"mall_id": r["mall_id"]} if r else None


def _hash(po_no: str, token: str) -> str:
    return hashlib.sha256(f"{po_no}|ack|{token}".encode()).hexdigest()


def ack_link(eng, mall_id: str, po_no: str, *, by: str = "operator") -> str:
    """수신 확인 링크 — 원문은 이 반환값에만. 새로 만들면 옛 링크는 막힌다."""
    token = secrets.token_urlsafe(18)
    with eng.begin() as c:
        n = c.execute(
            update(store.t_po)
            .where(
                and_(store.t_po.c.po_no == po_no, store.t_po.c.mall_id == mall_id, store.t_po.c.status != "cancelled")
            )
            .values(ack_token_hash=_hash(po_no, token))
        ).rowcount
        if not n:
            raise store.MallError("없거나 취소된 발주서예요")
        store._event(c, mall_id, "po_ack_link", {"po_no": po_no, "by": by})
    return f"/corp/po/{po_no}#k={token}"


def _resolve(eng, po_no: str, token: str, client: str):
    key = "po-ack"
    if store._blocked(client, key):
        raise store.MallError("여러 번 잘못 열어 잠시 막았어요. 10분 뒤에 다시 해 주세요")
    with eng.connect() as c:
        r = c.execute(select(store.t_po).where(store.t_po.c.po_no == po_no)).mappings().first()
    if (
        r is None
        or not r["ack_token_hash"]
        or r["ack_token_hash"] != _hash(po_no, token or "")
        or r["status"] == "cancelled"
    ):
        store._fail(client, key)
        raise store.MallError("링크가 맞지 않거나 사용이 끝났어요. 발주 담당자에게 새 링크를 요청해 주세요")
    return r


def public_view(eng, po_no: str, token: str, client: str) -> dict:
    """공급사 확인 화면 — 발주 번호·발주사·품목·수량·금액·납기·조건만(배송 정보 없음)."""
    from app.admin.b2b.proposal import load_profile

    r = _resolve(eng, po_no, token, client)
    pf = load_profile()
    d = _row(r)
    return {
        "po": {
            k: d[k]
            for k in (
                "po_no",
                "supplier",
                "issued_at",
                "due_date",
                "payment_terms",
                "vat_mode",
                "lines",
                "supply_amount",
                "vat",
                "total",
                "needs_cost",
                "status",
                "status_label",
                "ack_at",
                "ack_by",
                "ack_ship_date",
            )
        },
        "orderer": {"name": pf.get("company_name"), "business_no": pf.get("business_no"), "address": pf.get("address")},
    }


def _ship_date(v: str | None) -> str | None:
    if not v:
        return None
    try:
        return date.fromisoformat(v).isoformat()
    except ValueError as e:
        raise store.MallError("출고 예정일을 날짜로 골라 주세요") from e


def acknowledge(
    eng, po_no: str, token: str, client: str, *, name: str, ship_date: str | None = None, memo: str = ""
) -> dict:
    """공급사가 링크로 수신 확인. 이미 확인한 뒤 다시 누르면 출고 예정일·메모만 고친다(확인 시각은 처음 값)."""
    from app.services.privacy import pii

    r = _resolve(eng, po_no, token, client)
    who = " ".join((name or "").split())[:30]
    if len(who) < 1:
        raise store.MallError("확인하시는 분 이름(또는 부서)을 적어 주세요")
    note, _ = pii.mask(" ".join((memo or "").split())[:300])
    vals = {
        "ack_by": who,
        "ack_ship_date": _ship_date(ship_date),
        "ack_memo": note or None,
        "ack_via": "link",
        "status": "acknowledged",
    }
    if r["ack_at"] is None:
        vals["ack_at"] = store.now()
    with eng.begin() as c:
        c.execute(update(store.t_po).where(store.t_po.c.po_no == po_no).values(**vals))
        store._event(c, r["mall_id"], "po_ack", {"po_no": po_no, "via": "link", "again": r["ack_at"] is not None})
    return get(eng, po_no)


def mark_ack(eng, mall_id: str, po_no: str, *, by: str, note: str = "", ship_date: str | None = None) -> dict:
    """운영자가 직접 '공급사 확인' 표시(메일 답장·전화 등). 무엇을 근거로 했는지 메모."""
    vals = {
        "status": "acknowledged",
        "ack_at": store.now(),
        "ack_by": f"운영자 표시({by})"[:30],
        "ack_via": "operator",
        "ack_memo": " ".join((note or "").split())[:300] or None,
        "ack_ship_date": _ship_date(ship_date),
    }
    with eng.begin() as c:
        n = c.execute(
            update(store.t_po)
            .where(and_(store.t_po.c.po_no == po_no, store.t_po.c.mall_id == mall_id, store.t_po.c.status == "issued"))
            .values(**vals)
        ).rowcount
        if not n:
            raise store.MallError("확인 전 상태의 발주서만 표시할 수 있어요")
        store._event(c, mall_id, "po_ack", {"po_no": po_no, "via": "operator", "by": by})
    return get(eng, po_no)


def cancel(eng, mall_id: str, po_no: str, *, by: str, reason: str) -> dict:
    """발주서 취소 — 그 발주서의 주문을 '발송 요청'(개별)·'없음'(일괄)으로 되돌려 다시 묶을 수 있게. 송장이 들어간 주문이 있으면 거부."""
    reason = " ".join((reason or "").split())[:200]
    if not reason:
        raise store.MallError("취소 이유를 적어 주세요")
    m = store.get_mall(eng, mall_id=mall_id)
    with eng.begin() as c:
        r = (
            c.execute(select(store.t_po).where(and_(store.t_po.c.po_no == po_no, store.t_po.c.mall_id == mall_id)))
            .mappings()
            .first()
        )
        if r is None or r["status"] == "cancelled":
            raise store.MallError("없거나 이미 취소된 발주서예요")
        oids = list(
            c.execute(
                select(store.t_po_line.c.order_id).where(
                    and_(store.t_po_line.c.batch_id == r["batch_id"], store.t_po_line.c.supplier == r["supplier_name"])
                )
            ).scalars()
        )
        busy = c.execute(
            select(store.t_order.c.order_id).where(
                and_(
                    store.t_order.c.order_id.in_(oids),
                    (store.t_order.c.tracking.is_not(None))
                    | (store.t_order.c.ship_status.in_(("shipped", "delivered"))),
                )
            )
        ).first()
        if busy:
            raise store.MallError("송장이 들어갔거나 출고된 주문이 있어 취소할 수 없어요 — 공급사와 확인해 주세요")
        back = "none" if m and m["delivery_mode"] != "individual" else "requested"
        c.execute(
            update(store.t_order)
            .where(and_(store.t_order.c.order_id.in_(oids), store.t_order.c.ship_status == "exported"))
            .values(ship_status=back)
        )
        c.execute(
            store.t_po_line.delete().where(
                and_(store.t_po_line.c.batch_id == r["batch_id"], store.t_po_line.c.supplier == r["supplier_name"])
            )
        )
        c.execute(
            update(store.t_po)
            .where(store.t_po.c.po_no == po_no)
            .values(status="cancelled", ack_token_hash=None, ack_memo=f"취소: {reason}")
        )
        store._event(c, mall_id, "po_cancel", {"po_no": po_no, "orders": len(oids), "by": by})
    return get(eng, po_no)


def won(v: int | None) -> str:
    return "단가 확인 필요" if v is None else f"{v:,}원"


_PO_NO = re.compile(r"^PO\d{6}-[0-9A-F]{4}-\d{2}$")

__all__ = [
    "STATUS_LABEL",
    "issue_for_batch",
    "list_pos",
    "get",
    "ack_link",
    "public_view",
    "acknowledge",
    "mark_ack",
    "cancel",
    "won",
]
