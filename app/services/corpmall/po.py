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
import secrets

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


def _row(ws, values: list, text_cols: set[int]) -> None:
    """한 줄 쓰기 — 주문 번호·휴대폰·우편번호·품번·송장 칸은 **텍스트 셀**(앞자리 0·긴 번호가 숫자로 바뀌지 않게)."""
    ws.append([v if (isinstance(v, int) and k not in text_cols) else _safe(v) for k, v in enumerate(values)])
    r = ws.max_row
    for k in text_cols:
        cell = ws.cell(row=r, column=k + 1)
        cell.number_format = "@"
        if cell.value is not None and not isinstance(cell.value, str):
            cell.value = str(cell.value)


# 개별 배송 시트 칸: 0 주문 번호 · 1 상품 · 2 품번 · 3 수량 · 4 받는 분 · 5 휴대폰 · 6 우편번호 · 7 주소 · 8 메모 · 9 송장
IND_COLS = ["주문 번호", "상품", "공급사 품번", "수량", "받는 분", "휴대폰", "우편번호", "주소", "배송 메모", "송장"]
IND_TEXT = {0, 2, 5, 6, 9}
BULK_COLS = ["상품", "공급사 품번", "수량", "수령지 (발주처와 확인해 적기)", "송장"]
BULK_TEXT = {1, 4}


def _qty(lines) -> dict[tuple, int]:
    out: dict[tuple, int] = {}
    for ln in lines:
        k = (ln["item_id"], ln["sku"])
        out[k] = out.get(k, 0) + (ln["qty"] or 1)
    return out


def create_batch(eng, mall_id: str, *, by: str) -> dict:
    """발주 묶음 만들기 — 넣을 주문을 정하고 '발송 준비'로 바꾸고 묶음에 기록한다. **파일은 따로 받는다**(render).

    제외(상태 그대로 남음): 공급사 미지정 상품, 받는 곳이 없는 주문. 사유별 건수를 돌려준다.
    """
    m = store.get_mall(eng, mall_id=mall_id)
    if m is None:
        raise store.MallError("없는 몰")
    bulk = m["delivery_mode"] != "individual"
    if bulk and m["status"] != "closed":
        raise store.MallError("회사 일괄 배송 몰은 마감한 뒤 수량이 확정되면 발주서를 만들어요")
    items = {i["id"]: i for i in m["items"]}
    want = ("none",) if bulk else ("requested",)
    excluded = {"공급사 미지정": 0, "받는 곳 없음": 0}
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
        take = []
        for r in rows:
            it = items.get(r["item_id"], {})
            if not it.get("supplier"):
                excluded["공급사 미지정"] += 1
            elif not bulk and not r["ship_enc"]:
                excluded["받는 곳 없음"] += 1
            else:
                take.append((r, it))
        if not take:
            why = ", ".join(f"{k} {v}건" for k, v in excluded.items() if v)
            raise store.MallError(
                "발주서에 넣을 주문이 없어요"
                + (f" (제외: {why})" if why else " (이미 발주 묶음에 넣은 주문은 다시 나오지 않아요)")
            )
        batch_id = f"PO{store.now():%y%m%d}-{secrets.token_hex(2).upper()}"
        per: dict[str, dict] = {}
        for r, it in take:
            g = per.setdefault(it["supplier"], {"orders": 0, "qty": {}})
            g["orders"] += 1
            name = it.get("name") or r["item_id"]
            g["qty"][name] = g["qty"].get(name, 0) + 1
            c.execute(
                store.t_po_line.insert().values(
                    batch_id=batch_id,
                    order_id=r["order_id"],
                    supplier=it["supplier"],
                    item_id=r["item_id"],
                    sku=it.get("supplier_sku"),
                    qty=1,
                )
            )
        c.execute(
            update(store.t_order)
            .where(
                and_(
                    store.t_order.c.order_id.in_([r["order_id"] for r, _ in take]),
                    store.t_order.c.ship_status.in_(want),
                )
            )
            .values(ship_status="exported", updated_at=store.now())
        )
        summary = {"orders": len(take), "suppliers": per, "excluded": {k: v for k, v in excluded.items() if v}}
        c.execute(
            store.t_po_batch.insert().values(
                batch_id=batch_id, mall_id=mall_id, created_at=store.now(), created_by=by, summary=summary
            )
        )
        store._event(
            c,
            mall_id,
            "po_batch",
            {
                "batch_id": batch_id,
                "orders": len(take),
                "suppliers": len(per),
                "excluded": sum(excluded.values()),
                "by": by,
            },
        )
    return {"batch_id": batch_id, **summary}


def list_batches(eng, mall_id: str) -> list[dict]:
    with eng.connect() as c:
        rows = (
            c.execute(
                select(store.t_po_batch)
                .where(store.t_po_batch.c.mall_id == mall_id)
                .order_by(store.t_po_batch.c.created_at.desc())
            )
            .mappings()
            .all()
        )
    return [
        {
            "batch_id": r["batch_id"],
            "created_at": r["created_at"].isoformat() if r["created_at"] else None,
            "created_by": r["created_by"],
            **(r["summary"] or {}),
        }
        for r in rows
    ]


def render(eng, mall_id: str, batch_id: str, *, supplier: str | None = None, by: str = "operator") -> tuple[bytes, str]:
    """발주 묶음 파일. supplier 가 없으면 운영자용 통합본(요약 + 공급사별 시트), 있으면 **그 공급사 것만** 든 전달용 파일.

    같은 묶음은 몇 번이든 다시 받을 수 있다(다운로드 실패 대비). 배송 정보는 그때 주문에서 복호화한다
    (보존 기간이 지나 지워졌으면 그렇게 표시).
    """
    m = store.get_mall(eng, mall_id=mall_id)
    with eng.connect() as c:
        b = (
            c.execute(
                select(store.t_po_batch).where(
                    and_(store.t_po_batch.c.batch_id == batch_id, store.t_po_batch.c.mall_id == mall_id)
                )
            )
            .mappings()
            .first()
        )
        if b is None or m is None:
            raise store.MallError("없는 발주 묶음이에요")
        q = (
            select(store.t_po_line, store.t_order.c.ship_enc)
            .join(store.t_order, store.t_order.c.order_id == store.t_po_line.c.order_id)
            .where(store.t_po_line.c.batch_id == batch_id)
        )
        if supplier is not None:
            q = q.where(store.t_po_line.c.supplier == supplier)
        lines = c.execute(q.order_by(store.t_po_line.c.supplier, store.t_po_line.c.order_id)).mappings().all()
    if not lines:
        raise store.MallError("그 공급사는 이 묶음에 없어요")
    bulk = m["delivery_mode"] != "individual"
    names = {i["id"]: i.get("name") for i in m["items"]}
    groups: dict[str, list] = {}
    for ln in lines:
        groups.setdefault(ln["supplier"], []).append(ln)
    wb = Workbook()
    first = wb.active
    used: set = set()
    if supplier is None:
        first.title = "요약"
        _head(first, ["발주 묶음", "공급사", "상품", "공급사 품번", "수량"])
        for sup, ls in groups.items():
            for (iid, sku), n in _qty(ls).items():
                _row(first, [batch_id, sup, names.get(iid, iid), sku, n], {0, 3})
        first.column_dimensions["B"].width = 18
        first.column_dimensions["C"].width = 26
    for k, (sup, ls) in enumerate(groups.items()):
        ws = first if (supplier is not None and k == 0) else wb.create_sheet()
        ws.title = _sheet_name(sup, used)
        if bulk:
            _head(ws, BULK_COLS)
            for (iid, sku), n in _qty(ls).items():
                _row(ws, [names.get(iid, iid), sku, n, "", ""], BULK_TEXT)
        else:
            _head(ws, IND_COLS)
            for ln in ls:
                s = (store._dec(ln["ship_enc"]) if ln["ship_enc"] else None) or {"name": "(보존 기간이 지나 지워짐)"}
                _row(
                    ws,
                    [
                        ln["order_id"],
                        names.get(ln["item_id"], ln["item_id"]),
                        ln["sku"],
                        ln["qty"] or 1,
                        s.get("name"),
                        s.get("phone"),
                        s.get("zipcode"),
                        s.get("address"),
                        s.get("memo"),
                        "",
                    ],
                    IND_TEXT,
                )
        for col, w in zip("ABCDEFGHIJ", (14, 24, 14, 6, 10, 15, 9, 40, 20, 18), strict=False):
            ws.column_dimensions[col].width = w
    with eng.begin() as c:  # 누가 어떤 파일을 받았는지 (배송 정보 없음)
        store._event(c, mall_id, "po_download", {"batch_id": batch_id, "supplier": supplier or "(통합본)", "by": by})
    buf = io.BytesIO()
    wb.save(buf)
    tag = "통합본" if supplier is None else _BAD_SHEET.sub(" ", supplier)
    return buf.getvalue(), f"{m['slug']}_{batch_id}_{tag}.xlsx"


_ORDER_HDR = ("주문 번호", "주문번호", "order_id")
_TRACK_HDR = ("송장", "송장 번호", "송장번호", "운송장", "tracking")


_SCI = re.compile(r"^\d+(\.\d+)?[eE]\+\d+$")


def _text(v) -> str:
    return str(v if v is not None else "").strip().lstrip("'")


def read_tracking(filename: str, data: bytes) -> tuple[list[dict], list[dict]]:
    """공급사가 돌려준 엑셀·CSV → ([{order_id, tracking}], [문제]).

    '주문 번호'와 '송장' 칸이 있는 표만 읽는다(모든 시트). 송장이 **숫자 셀**이거나 1.2E+11 같은 모양이면
    앞자리 0·긴 번호가 이미 바뀌었을 수 있어 **자동으로 고치지 않고 문제로** 돌려준다. 한 파일에 같은 주문이
    다른 송장으로 두 번 있으면 둘 다 문제.
    """
    tables: list[list[list]] = []
    if filename.lower().endswith((".xlsx", ".xlsm")):
        wb = load_workbook(io.BytesIO(data), read_only=True, data_only=True)
        for ws in wb.worksheets:
            tables.append([list(r) for r in ws.iter_rows(values_only=True)])
    else:
        text = data.decode("utf-8-sig", errors="replace")
        tables.append([row for row in csv.reader(io.StringIO(text))])
    seen: dict[str, str] = {}
    problems: list[dict] = []
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
            oid, raw = _text(r[oi]), r[ti]
            if not re.fullmatch(r"O[0-9A-F]{10}", oid) or raw in (None, ""):
                continue
            if isinstance(raw, (int, float)) or _SCI.fullmatch(_text(raw)):
                problems.append(
                    {
                        "order_id": oid,
                        "why": "송장이 숫자로 바뀌어 있어요(앞자리 0·긴 번호가 바뀌었을 수 있음) — 텍스트로 다시 적어 주세요",
                    }
                )
                continue
            tr = _text(raw)
            if oid in seen and seen[oid] != tr:
                problems.append({"order_id": oid, "why": "한 파일에 같은 주문이 다른 송장으로 두 번 있어요"})
                seen[oid] = ""
                continue
            seen.setdefault(oid, tr)
    rows = [{"order_id": o, "tracking": tr} for o, tr in seen.items() if tr]
    return rows, problems


__all__ = ["UNASSIGNED", "set_suppliers", "create_batch", "list_batches", "render", "read_tracking"]
