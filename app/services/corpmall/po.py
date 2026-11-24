"""폐쇄몰 공급사별 발주서와 송장 회수 (2026-11-24) — 설계 claude/b2b_corp_po_2026-11-24.md.

* 몰 상품마다 공급사(이름)·공급사 품번을 운영자가 붙인다(직원·발주처 화면에는 안 보임).
* 발주서(엑셀 한 파일): '요약' 시트(공급사·품목·수량) + 공급사마다 시트 하나.
  - 직원 집 배송 몰: 발송 요청 주문을 한 줄씩(주문 번호·상품·품번·받는 분·휴대폰·주소·메모·**송장 빈칸**).
  - 회사 일괄 배송 몰: **마감 뒤에만**, 품목별 수량. 수령지는 발주처와 확인해 적는 빈칸(회사 주소·담당자를 저장하지 않음).
  - 넣은 주문은 '발송 준비'(exported)로 바뀌어 다시 나오지 않는다. 기록에는 건수·공급사 수만.
  - 파일은 서버에 남기지 않는다(내려받기만). 공급사 전달 뒤 운영자 컴퓨터의 파일은 지운다.
* 송장 회수: 공급사가 '송장' 칸을 채워 돌려준 엑셀(또는 CSV)을 올리면 주문 번호로 송장을 넣는다(store.set_tracking).
* 엑셀 수식 주입 막기: =,+,-,@ 로 시작하는 글자는 앞에 ' 를 붙여 글자로만 넣는다.
"""

from __future__ import annotations

import csv
import io
import re

from openpyxl import Workbook, load_workbook
from sqlalchemy import and_, select, update
from openpyxl.styles import Font, PatternFill

from app.services.corpmall import store

UNASSIGNED = "공급사 미지정"
_BAD_SHEET = re.compile(r"[\[\]:*?/\\]")
HEAD_FILL = PatternFill("solid", fgColor="EEF2EA")


def _safe(v) -> str | int:
    if isinstance(v, int):
        return v
    s = "" if v is None else str(v)
    return "'" + s if s[:1] in ("=", "+", "-", "@", "\t", "\r") else s


def set_suppliers(eng, mall_id: str, mapping: dict) -> list[dict]:
    """{item_id: {supplier, sku}} → 몰 상품에 공급사·품번. 모르는 상품 id 는 거부."""
    m = store.get_mall(eng, mall_id=mall_id)
    if m is None:
        raise store.MallError("없는 몰")
    ids = {i["id"] for i in m["items"]}
    unknown = set(mapping) - ids
    if unknown:
        raise store.MallError("몰에 없는 상품이에요: " + ", ".join(sorted(unknown)))
    items = []
    for i in m["items"]:
        v = mapping.get(i["id"])
        if v is not None:
            i = {
                **i,
                "supplier": " ".join(str(v.get("supplier") or "").split())[:40] or None,
                "supplier_sku": " ".join(str(v.get("sku") or "").split())[:40] or None,
            }
        items.append(i)
    with eng.begin() as c:
        r = c.execute(select(store.t_mall.c.payload).where(store.t_mall.c.mall_id == mall_id)).scalar()
        c.execute(update(store.t_mall).where(store.t_mall.c.mall_id == mall_id).values(payload={**r, "items": items}))
        store._event(c, mall_id, "suppliers", {"n": sum(1 for i in items if i.get("supplier"))})
    return [
        {"id": i["id"], "name": i.get("name"), "supplier": i.get("supplier"), "sku": i.get("supplier_sku")}
        for i in items
    ]


def _sheet_name(name: str, used: set) -> str:
    base = _BAD_SHEET.sub(" ", name).strip()[:28] or "공급사"
    n, out = 2, base
    while out in used or out == "요약":
        out, n = f"{base[:25]}({n})", n + 1
    used.add(out)
    return out


def _head(ws, cols: list[str]) -> None:
    ws.append(cols)
    for cell in ws[1]:
        cell.font = Font(bold=True)
        cell.fill = HEAD_FILL
    ws.freeze_panes = "A2"


def build(eng, mall_id: str, *, by: str) -> tuple[bytes, dict]:
    """발주서 엑셀(bytes)과 요약 {orders, suppliers, unassigned}. 넣은 주문은 'exported'."""
    m = store.get_mall(eng, mall_id=mall_id)
    if m is None:
        raise store.MallError("없는 몰")
    bulk = m["delivery_mode"] != "individual"
    if bulk and m["status"] != "closed":
        raise store.MallError("회사 일괄 배송 몰은 마감한 뒤 수량이 확정되면 발주서를 만들어요")
    items = {i["id"]: i for i in m["items"]}
    want = ("none",) if bulk else ("requested",)
    with eng.begin() as c:
        rows = (
            c.execute(
                select(store.t_order)
                .where(and_(store.t_order.c.mall_id == mall_id, store.t_order.c.ship_status.in_(want)))
                .order_by(store.t_order.c.chosen_at)
            )
            .mappings()
            .all()
        )
        if not rows:
            raise store.MallError("발주서에 넣을 주문이 없어요 (이미 발송 준비로 넘긴 주문은 다시 나오지 않아요)")
        groups: dict[str, list] = {}
        for r in rows:
            it = items.get(r["item_id"], {})
            groups.setdefault(it.get("supplier") or UNASSIGNED, []).append(r)

        wb = Workbook()
        summ = wb.active
        summ.title = "요약"
        _head(summ, ["공급사", "상품", "공급사 품번", "수량"])
        used: set = set()
        for sup, rs in sorted(groups.items(), key=lambda kv: (kv[0] == UNASSIGNED, kv[0])):
            counts: dict[str, int] = {}
            for r in rs:
                counts[r["item_id"]] = counts.get(r["item_id"], 0) + 1
            for iid, n in counts.items():
                summ.append(
                    [
                        _safe(sup),
                        _safe(items.get(iid, {}).get("name") or iid),
                        _safe(items.get(iid, {}).get("supplier_sku")),
                        n,
                    ]
                )
            ws = wb.create_sheet(_sheet_name(sup, used))
            if bulk:
                _head(ws, ["상품", "공급사 품번", "수량", "수령지 (발주처와 확인해 적기)", "송장"])
                for iid, n in counts.items():
                    ws.append(
                        [
                            _safe(items.get(iid, {}).get("name") or iid),
                            _safe(items.get(iid, {}).get("supplier_sku")),
                            n,
                            "",
                            "",
                        ]
                    )
            else:
                _head(
                    ws,
                    [
                        "주문 번호",
                        "상품",
                        "공급사 품번",
                        "수량",
                        "받는 분",
                        "휴대폰",
                        "우편번호",
                        "주소",
                        "배송 메모",
                        "송장",
                    ],
                )
                for r in rs:
                    s = store._dec(r["ship_enc"]) or {}
                    it = items.get(r["item_id"], {})
                    ws.append(
                        [
                            _safe(r["order_id"]),
                            _safe(it.get("name") or r["item_id"]),
                            _safe(it.get("supplier_sku")),
                            1,
                            _safe(s.get("name")),
                            _safe(s.get("phone")),
                            _safe(s.get("zipcode")),
                            _safe(s.get("address")),
                            _safe(s.get("memo")),
                            "",
                        ]
                    )
            for col, w in zip("ABCDEFGHIJ", (14, 24, 14, 6, 10, 15, 9, 40, 20, 18), strict=False):
                ws.column_dimensions[col].width = w
        summ.column_dimensions["A"].width = 18
        summ.column_dimensions["B"].width = 26
        c.execute(
            update(store.t_order)
            .where(store.t_order.c.order_id.in_([r["order_id"] for r in rows]))
            .values(ship_status="exported", updated_at=store.now())
        )
        summary = {"orders": len(rows), "suppliers": len(groups), "unassigned": len(groups.get(UNASSIGNED, []))}
        store._event(c, mall_id, "po_exported", {**summary, "by": by})
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue(), summary


_ORDER_HDR = ("주문 번호", "주문번호", "order_id")
_TRACK_HDR = ("송장", "송장 번호", "송장번호", "운송장", "tracking")


def _cell(v) -> str:
    if isinstance(v, float) and v.is_integer():  # 엑셀이 송장 번호를 숫자로 바꿔 둔 경우
        v = int(v)
    return str(v if v is not None else "").strip().lstrip("'")


def read_tracking(filename: str, data: bytes) -> list[dict]:
    """공급사가 돌려준 엑셀·CSV에서 [{order_id, tracking}] — '주문 번호'와 '송장' 칸이 있는 표만 읽는다(모든 시트)."""
    tables: list[list[list]] = []
    if filename.lower().endswith((".xlsx", ".xlsm")):
        wb = load_workbook(io.BytesIO(data), read_only=True, data_only=True)
        for ws in wb.worksheets:
            tables.append([list(r) for r in ws.iter_rows(values_only=True)])
    else:
        text = data.decode("utf-8-sig", errors="replace")
        tables.append([row for row in csv.reader(io.StringIO(text))])
    out = []
    for t in tables:
        if not t:
            continue
        head = [str(h or "").strip() for h in t[0]]
        oi = next((i for i, h in enumerate(head) if h in _ORDER_HDR), None)
        ti = next((i for i, h in enumerate(head) if h in _TRACK_HDR), None)
        if oi is None or ti is None:
            continue
        for r in t[1:]:
            if len(r) <= max(oi, ti):
                continue
            oid = _cell(r[oi])
            tr = _cell(r[ti])
            if re.fullmatch(r"O[0-9A-F]{10}", oid) and tr:
                out.append({"order_id": oid, "tracking": tr})
    return out


__all__ = ["UNASSIGNED", "set_suppliers", "build", "read_tracking"]
