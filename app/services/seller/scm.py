"""셀러 SCM 기본 ③ (창 5, 2026-11-25) — 설계 claude/stage5_seller_design_2026-11-25.md · 로드맵 '정식 위탁판매 셀러와 발주 자동화'.

* **재고·품절.** 상품마다 재고(관리 안 하면 비움)·품절·입고 예정일. 재고 0 이면 품절로 본다.
* **셀러의 공급사.** 위탁판매 셀러가 자기 공급사를 적고 상품마다 공급사·품번을 붙인다. 직접 재고 셀러는 '직접 출고'.
  우리 회사(운영사)의 공급 거래처(B2B)와는 다른 표다 — 셀러 간에도, 운영사 거래처와도 섞이지 않는다.
* **주문.** 1단계 결제 구조에서 주문은 셀러 판매처(스마트스토어 등)에 있다. 커머스API 주문 조회(⑥) 전에는
  셀러가 판매처 주문을 CSV 로 올린다. commerce_ai 는 주문을 **접수·변경하지 않고** 발주서로 옮겨 적기만 한다.
  - 받는 분 정보는 셀러의 수탁자로서 처리 — 올릴 때 위탁 확인(``entrust_ok``)이 있어야 한다. 필요한 항목만
    (받는 분·휴대폰·우편번호·주소·메모), **암호화** 저장. 화면 목록에는 가려서.
  - 송장이 들어가면(출고) 30일 뒤, 출고되지 않은 주문은 올린 뒤 90일 뒤 받는 분 정보를 지운다(매일 보존 작업 — 설계안).
* **발주서.** 새 주문을 묶어 엑셀 한 파일(공급사마다 시트 — 폐쇄몰 발주서 서식 재사용). 파일은 서버에 남기지 않고
  셀러가 내려받아 **직접** 공급사에 보낸다(우리가 보내지 않음). 내려받을 때마다 건수·내용 지문을 기록.
* **송장.** 공급사가 '송장' 칸을 채워 돌려준 파일을 올리면 주문 번호로 송장을 넣는다(폐쇄몰 ``read_tracking`` 재사용 —
  숫자로 바뀐 송장은 고치지 않고 문제로 돌려줌). 자기 주문만.
* **알림(화면).** 승인 상품의 품절, 2영업일 넘게 출고 안 된 주문. 알림톡은 사업자등록·채널 개설 뒤.
* 노출 없음(결정 2) — 재고·품절도 고객 화면·추천과 연결하지 않는다.
"""

from __future__ import annotations

import csv
import hashlib
import io
import re
import secrets
from datetime import date, datetime, timedelta

from openpyxl import Workbook
from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    UniqueConstraint,
    and_,
    select,
    update,
)

from app.services.corpmall import po as corp_po
from app.services.corpmall import store as corp
from app.services.seller import products, store

KEEP_AFTER_SHIP_DAYS = 30
KEEP_UNSHIPPED_DAYS = 90
DELAY_BIZ_DAYS = 2
MAX_ORDER_ROWS = 500
DIRECT = "직접 출고"
ORDER_STATUS = {"new": "발주 전", "po": "발주서 나감", "shipped": "송장 등록"}
ORDER_HEADERS = {
    "판매처 주문번호": "store_order_no",
    "상품 번호": "product_id",
    "수량": "qty",
    "받는 분": "name",
    "휴대폰": "phone",
    "우편번호": "zipcode",
    "주소": "address",
    "배송 메모": "memo",
    "주문일": "ordered_on",
}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

meta = MetaData()
t_stock = Table(
    "seller_stock",
    meta,
    Column("product_id", String(12), primary_key=True),
    Column("seller_id", String(12), index=True, nullable=False),
    Column("stock", Integer),  # None = 재고 관리 안 함
    Column("sold_out", Boolean, default=False),
    Column("restock_on", String(10)),
    Column("updated_at", DateTime(timezone=True)),
)
t_supplier = Table(
    "seller_supplier",
    meta,
    Column("supplier_id", String(12), primary_key=True),
    Column("seller_id", String(12), index=True, nullable=False),
    Column("name", String(40), nullable=False),
    Column("contact_enc", Text),  # 공급사 담당자 (암호화) — 셀러 계약 종료 뒤 셀러 연락처와 같이 지움
    Column("memo", String(200)),
    Column("created_at", DateTime(timezone=True)),
    UniqueConstraint("seller_id", "name", name="uq_seller_supplier_name"),
)
t_supply = Table(
    "seller_supply",
    meta,
    Column("product_id", String(12), primary_key=True),
    Column("seller_id", String(12), index=True, nullable=False),
    Column("supplier_id", String(12)),  # None = 직접 출고
    Column("sku", String(40)),
)
t_order = Table(
    "seller_order",
    meta,
    Column("order_id", String(12), primary_key=True),  # O + 16진 10자 (폐쇄몰 송장 읽기와 같은 모양)
    Column("seller_id", String(12), index=True, nullable=False),
    Column("product_id", String(12), nullable=False),
    Column("qty", Integer, nullable=False),
    Column("store_order_no", String(40), nullable=False),
    Column("ship_enc", Text),  # 받는 분 정보 (암호화) — 지우면 None
    Column("status", String(8), nullable=False, default="new"),
    Column("tracking", String(40)),
    Column("ordered_on", String(10)),
    Column("batch_id", String(12)),
    Column("created_at", DateTime(timezone=True)),
    Column("exported_at", DateTime(timezone=True)),
    Column("shipped_at", DateTime(timezone=True)),
    Column("purged_at", DateTime(timezone=True)),
    UniqueConstraint("seller_id", "store_order_no", "product_id", name="uq_seller_order_line"),
)
t_batch = Table(
    "seller_po_batch",
    meta,
    Column("batch_id", String(12), primary_key=True),
    Column("seller_id", String(12), index=True, nullable=False),
    Column("created_at", DateTime(timezone=True)),
    Column("n_orders", Integer),
    Column("n_suppliers", Integer),
    Column("downloads", JSON),  # [{at, sha16, n}] — 개인정보 없음
)


def engine(url: str | None = None):
    eng = products.engine(url)
    meta.create_all(eng)
    return eng


def _txt(v, n: int) -> str:
    return " ".join(str(v or "").split())[:n]


def _own_product(c, seller_id: str, product_id: str):
    r = (
        c.execute(
            select(products.t_product).where(
                and_(products.t_product.c.seller_id == seller_id, products.t_product.c.product_id == product_id)
            )
        )
        .mappings()
        .first()
    )
    if r is None:
        raise store.SellerError("없는 상품이에요")
    return r


# ── 재고·품절 ─────────────────────────────────────────────────────────────
def set_stock(eng, token: str, client: str, product_id: str, *, stock, sold_out: bool, restock_on: str | None) -> dict:
    s = store.resolve(eng, token, client)
    st = None
    if stock is not None and str(stock).strip() != "":
        try:
            st = int(str(stock).replace(",", "").strip())
        except ValueError as e:
            raise store.SellerError("재고는 숫자로 넣어 주세요") from e
        if not 0 <= st <= 1_000_000:
            raise store.SellerError("재고는 0~1,000,000 사이로 넣어 주세요")
    ro = (restock_on or "").strip() or None
    if ro and not DATE_RE.match(ro):
        raise store.SellerError("입고 예정일은 2026-12-01 모양으로 넣어 주세요")
    with eng.begin() as c:
        _own_product(c, s["seller_id"], product_id)
        vals = dict(seller_id=s["seller_id"], stock=st, sold_out=bool(sold_out), restock_on=ro, updated_at=store.now())
        if c.execute(update(t_stock).where(t_stock.c.product_id == product_id).values(**vals)).rowcount == 0:
            c.execute(t_stock.insert().values(product_id=product_id, **vals))
        store._event(
            c, s["seller_id"], "stock", "seller", {"product_id": product_id, "stock": st, "sold_out": bool(sold_out)}
        )
    return stock_of(eng, s["seller_id"])[product_id]


def stock_of(eng, seller_id: str) -> dict[str, dict]:
    with eng.connect() as c:
        rows = c.execute(select(t_stock).where(t_stock.c.seller_id == seller_id)).mappings().all()
    return {
        r["product_id"]: {
            "stock": r["stock"],
            "sold_out": bool(r["sold_out"]) or r["stock"] == 0,
            "restock_on": r["restock_on"],
            "updated_at": r["updated_at"].isoformat() if r["updated_at"] else None,
        }
        for r in rows
    }


# ── 셀러의 공급사 ─────────────────────────────────────────────────────────
def save_supplier(eng, token: str, client: str, *, name: str, contact: dict | None, memo: str = "",
                  supplier_id: str | None = None) -> dict:  # fmt: skip
    s = store.resolve(eng, token, client)
    name = _txt(name, 40)
    if not name or name == DIRECT:
        raise store.SellerError("공급사 이름을 넣어 주세요")
    ct = None
    if contact and any(str(v or "").strip() for v in contact.values()):
        ct = store._check_contact(contact)
    with eng.begin() as c:
        dup = c.execute(
            select(t_supplier.c.supplier_id).where(
                and_(t_supplier.c.seller_id == s["seller_id"], t_supplier.c.name == name)
            )
        ).scalar()
        if dup and dup != supplier_id:
            raise store.SellerError("같은 이름의 공급사가 이미 있어요")
        vals = dict(name=name, contact_enc=corp._enc(ct) if ct else None, memo=_txt(memo, 200))
        if supplier_id:
            n = c.execute(
                update(t_supplier)
                .where(and_(t_supplier.c.seller_id == s["seller_id"], t_supplier.c.supplier_id == supplier_id))
                .values(**vals)
            ).rowcount
            if n == 0:
                raise store.SellerError("없는 공급사예요")
            sid = supplier_id
        else:
            sid = "V" + secrets.token_hex(4).upper()
            c.execute(
                t_supplier.insert().values(supplier_id=sid, seller_id=s["seller_id"], created_at=store.now(), **vals)
            )
        store._event(c, s["seller_id"], "supplier_saved", "seller", {"supplier_id": sid})
    return next(x for x in list_suppliers(eng, token, client) if x["supplier_id"] == sid)


def list_suppliers(eng, token: str, client: str) -> list[dict]:
    s = store.resolve(eng, token, client)
    with eng.connect() as c:
        rows = (
            c.execute(select(t_supplier).where(t_supplier.c.seller_id == s["seller_id"]).order_by(t_supplier.c.name))
            .mappings()
            .all()
        )
    return [{"supplier_id": r["supplier_id"], "name": r["name"], "memo": r["memo"] or "",
             "contact": corp._dec(r["contact_enc"])} for r in rows]  # fmt: skip


def set_supply(eng, token: str, client: str, product_id: str, *, supplier_id: str | None, sku: str = "") -> dict:
    s = store.resolve(eng, token, client)
    with eng.begin() as c:
        _own_product(c, s["seller_id"], product_id)
        if supplier_id:
            ok = c.execute(
                select(t_supplier.c.supplier_id).where(
                    and_(t_supplier.c.seller_id == s["seller_id"], t_supplier.c.supplier_id == supplier_id)
                )
            ).scalar()
            if not ok:
                raise store.SellerError("없는 공급사예요")
        vals = dict(seller_id=s["seller_id"], supplier_id=supplier_id or None, sku=_txt(sku, 40) or None)
        if c.execute(update(t_supply).where(t_supply.c.product_id == product_id).values(**vals)).rowcount == 0:
            c.execute(t_supply.insert().values(product_id=product_id, **vals))
    return {"product_id": product_id, "supplier_id": supplier_id or None, "sku": vals["sku"]}


def supply_of(eng, seller_id: str) -> dict[str, dict]:
    with eng.connect() as c:
        rows = c.execute(select(t_supply).where(t_supply.c.seller_id == seller_id)).mappings().all()
    return {r["product_id"]: {"supplier_id": r["supplier_id"], "sku": r["sku"] or ""} for r in rows}


# ── 주문 ────────────────────────────────────────────────────────────────
def _check_ship(raw: dict) -> dict:
    name = _txt(raw.get("name"), 30)
    phone = re.sub(r"[^0-9-]", "", str(raw.get("phone") or ""))[:20]
    zipc = re.sub(r"\D", "", str(raw.get("zipcode") or ""))[:6]
    addr = _txt(raw.get("address"), 200)
    if not (name and phone and addr):
        raise store.SellerError("받는 분·휴대폰·주소를 넣어 주세요")
    if len(re.sub(r"\D", "", phone)) < 9:
        raise store.SellerError("휴대폰 번호를 확인해 주세요")
    return {"name": name, "phone": phone, "zipcode": zipc, "address": addr, "memo": _txt(raw.get("memo"), 100)}


def import_orders(eng, token: str, client: str, text: str, *, entrust_ok: bool) -> dict:
    """판매처 주문 CSV — 한 줄이라도 틀리면 저장 안 함. 이미 올린 주문(판매처 주문번호 + 상품)은 건너뜀."""
    s = store.resolve(eng, token, client)
    if not entrust_ok:
        raise store.SellerError("받는 분 정보를 발주서에 옮겨 적는 일을 맡긴다는 확인이 필요해요")
    rd = csv.DictReader(io.StringIO((text or "").lstrip("﻿")))
    heads = [h.strip() for h in (rd.fieldnames or [])]
    need = [h for h in ("판매처 주문번호", "상품 번호", "수량", "받는 분", "휴대폰", "주소") if h not in heads]
    if need:
        raise store.SellerError("빠진 칸이 있어요: " + ", ".join(need))
    unknown = [h for h in heads if h not in ORDER_HEADERS]
    if unknown:
        raise store.SellerError("모르는 칸 이름이 있어요: " + ", ".join(unknown))
    with eng.connect() as c:
        mine = {
            r[0]
            for r in c.execute(
                select(products.t_product.c.product_id).where(products.t_product.c.seller_id == s["seller_id"])
            )
        }
    rows, errors = [], []
    for i, row in enumerate(rd, start=2):
        if i - 1 > MAX_ORDER_ROWS:
            raise store.SellerError(f"한 번에 {MAX_ORDER_ROWS}줄까지 올릴 수 있어요")
        raw = {ORDER_HEADERS[k.strip()]: (v or "").strip() for k, v in row.items() if k and k.strip() in ORDER_HEADERS}
        if not any(raw.values()):
            continue
        try:
            no = _txt(raw.get("store_order_no"), 40)
            if not no:
                raise store.SellerError("판매처 주문번호를 넣어 주세요")
            pid = raw.get("product_id", "")
            if pid not in mine:
                raise store.SellerError(f"내 상품 번호가 아니에요: {pid}")
            try:
                qty = int(raw.get("qty") or "")
            except ValueError as e:
                raise store.SellerError("수량은 숫자로 넣어 주세요") from e
            if not 1 <= qty <= 999:
                raise store.SellerError("수량은 1~999")
            od = raw.get("ordered_on") or None
            if od and not DATE_RE.match(od):
                raise store.SellerError("주문일은 2026-11-25 모양으로")
            rows.append(
                {"store_order_no": no, "product_id": pid, "qty": qty, "ordered_on": od, "ship": _check_ship(raw)}
            )
        except store.SellerError as e:
            errors.append({"line": i, "error": str(e)})
    if errors:
        return {"ok": False, "added": 0, "skipped": 0, "errors": errors}
    added = skipped = 0
    with eng.begin() as c:
        for r in rows:
            dup = c.execute(
                select(t_order.c.order_id).where(
                    and_(
                        t_order.c.seller_id == s["seller_id"],
                        t_order.c.store_order_no == r["store_order_no"],
                        t_order.c.product_id == r["product_id"],
                    )  # fmt: skip
                )
            ).scalar()
            if dup:
                skipped += 1
                continue
            c.execute(
                t_order.insert().values(
                    order_id="O" + secrets.token_hex(5).upper(),
                    seller_id=s["seller_id"],
                    product_id=r["product_id"],
                    qty=r["qty"],
                    store_order_no=r["store_order_no"],
                    ship_enc=corp._enc(r["ship"]),
                    status="new",
                    ordered_on=r["ordered_on"] or store.now().date().isoformat(),
                    created_at=store.now(),
                )  # fmt: skip
            )
            added += 1
        store._event(
            c, s["seller_id"], "orders_csv", "seller", {"added": added, "skipped": skipped, "entrust_ok": True}
        )
    return {"ok": True, "added": added, "skipped": skipped, "errors": []}


def _mask_ship(sh: dict | None) -> str:
    if not sh:
        return "(지움)"
    p = re.sub(r"\D", "", sh.get("phone") or "")
    return f"{sh.get('name', '')[:1]}** · ***-{p[-4:]} · {(sh.get('address') or '')[:8]}…"


def list_orders(eng, token: str, client: str, *, at: datetime | None = None) -> list[dict]:
    s = store.resolve(eng, token, client)
    at = at or store.now()
    with eng.connect() as c:
        rows = (
            c.execute(
                select(t_order).where(t_order.c.seller_id == s["seller_id"]).order_by(t_order.c.created_at.desc())
            )
            .mappings()
            .all()
        )
        names = dict(c.execute(select(products.t_product.c.product_id, products.t_product.c.name)
                               .where(products.t_product.c.seller_id == s["seller_id"])).all())  # fmt: skip
    return [
        {
            "order_id": r["order_id"],
            "store_order_no": r["store_order_no"],
            "product": names.get(r["product_id"], ""),
            "qty": r["qty"],
            "status": r["status"],
            "status_label": ORDER_STATUS[r["status"]],
            "tracking": r["tracking"] or "",
            "ordered_on": r["ordered_on"],
            "recipient": _mask_ship(corp._dec(r["ship_enc"])),
            "delayed": _delayed(r, at),
        }  # fmt: skip
        for r in rows
    ]


def biz_days_between(d0: date, d1: date) -> int:
    n, d = 0, d0
    while d < d1:
        d += timedelta(days=1)
        if d.weekday() < 5:
            n += 1
    return n


def _delayed(r, at: datetime) -> bool:
    if r["status"] == "shipped" or not r["ordered_on"]:
        return False
    return biz_days_between(date.fromisoformat(r["ordered_on"]), at.date()) > DELAY_BIZ_DAYS


# ── 발주서 ──────────────────────────────────────────────────────────────
def create_batch(eng, token: str, client: str) -> dict:
    """'발주 전' 주문을 한 묶음으로 — 상태가 '발주서 나감'으로 바뀌어 다음 묶음에 다시 들어가지 않는다."""
    s = store.resolve(eng, token, client)
    sup = supply_of(eng, s["seller_id"])
    with eng.begin() as c:
        rows = c.execute(
            select(t_order.c.order_id, t_order.c.product_id).where(
                and_(t_order.c.seller_id == s["seller_id"], t_order.c.status == "new", t_order.c.ship_enc.is_not(None))
            )
        ).all()
        if not rows:
            raise store.SellerError("발주할 새 주문이 없어요")
        bid = "B" + secrets.token_hex(4).upper()
        n_sup = len({(sup.get(pid) or {}).get("supplier_id") for _, pid in rows})
        c.execute(t_batch.insert().values(batch_id=bid, seller_id=s["seller_id"], created_at=store.now(), n_orders=len(rows),
                                          n_suppliers=n_sup, downloads=[]))  # fmt: skip
        c.execute(
            update(t_order)
            .where(t_order.c.order_id.in_([o for o, _ in rows]))
            .values(status="po", batch_id=bid, exported_at=store.now())
        )
        store._event(c, s["seller_id"], "po_batch", "seller", {"batch_id": bid, "n": len(rows), "suppliers": n_sup})
    return {"batch_id": bid, "n_orders": len(rows), "n_suppliers": n_sup}


def list_batches(eng, token: str, client: str) -> list[dict]:
    s = store.resolve(eng, token, client)
    with eng.connect() as c:
        rows = (
            c.execute(
                select(t_batch).where(t_batch.c.seller_id == s["seller_id"]).order_by(t_batch.c.created_at.desc())
            )
            .mappings()
            .all()
        )
    return [{"batch_id": r["batch_id"], "created_at": r["created_at"].isoformat(), "n_orders": r["n_orders"],
             "n_suppliers": r["n_suppliers"], "downloads": len(r["downloads"] or [])} for r in rows]  # fmt: skip


COLS = [
    "주문 번호",
    "판매처 주문번호",
    "상품",
    "공급사 품번",
    "수량",
    "받는 분",
    "휴대폰",
    "우편번호",
    "주소",
    "배송 메모",
    "송장",
]
TEXT = {0, 1, 3, 6, 7, 10}


def render_batch(eng, token: str, client: str, batch_id: str) -> tuple[bytes, str]:
    """발주서 엑셀 — 공급사마다 시트, 송장 칸은 빈칸(텍스트 셀). 서버에 남기지 않고 내려받기만."""
    s = store.resolve(eng, token, client)
    with eng.connect() as c:
        b = (
            c.execute(
                select(t_batch).where(and_(t_batch.c.seller_id == s["seller_id"], t_batch.c.batch_id == batch_id))
            )
            .mappings()
            .first()
        )
        if b is None:
            raise store.SellerError("없는 발주 묶음이에요")
        orders = c.execute(select(t_order).where(and_(t_order.c.seller_id == s["seller_id"], t_order.c.batch_id == batch_id))
                           .order_by(t_order.c.created_at)).mappings().all()  # fmt: skip
        names = dict(c.execute(select(products.t_product.c.product_id, products.t_product.c.name)
                               .where(products.t_product.c.seller_id == s["seller_id"])).all())  # fmt: skip
        sups = dict(
            c.execute(
                select(t_supplier.c.supplier_id, t_supplier.c.name).where(t_supplier.c.seller_id == s["seller_id"])
            ).all()
        )
    supply = supply_of(eng, s["seller_id"])
    groups: dict[str, list] = {}
    for o in orders:
        sp = supply.get(o["product_id"]) or {}
        groups.setdefault(sups.get(sp.get("supplier_id")) or DIRECT, []).append((o, sp.get("sku", "")))
    wb = Workbook()
    ws = wb.active
    ws.title = "요약"
    corp_po._head(ws, ["공급사", "주문 수", "수량 합"])
    for g, items in sorted(groups.items()):
        corp_po._row(ws, [g, len(items), sum(o["qty"] for o, _ in items)], {0})
    ws.append([])
    ws.append(
        [f"발주 묶음 {batch_id} · {s['name']} · 받는 분 정보가 들어 있어요 — 공급사에 보낸 뒤 파일을 지워 주세요"]
    )
    used: set = set()
    gone = 0
    for g, items in sorted(groups.items()):
        sh = wb.create_sheet(corp_po._sheet_name(g, used))
        corp_po._head(sh, COLS)
        for o, sku in items:
            ship = corp._dec(o["ship_enc"])
            if ship is None:
                gone += 1
                ship = {"name": "(보존 기간이 지나 지움)"}
            corp_po._row(sh, [o["order_id"], o["store_order_no"], names.get(o["product_id"], ""), sku, o["qty"],
                              ship.get("name", ""), ship.get("phone", ""), ship.get("zipcode", ""), ship.get("address", ""),
                              ship.get("memo", ""), o["tracking"] or ""], TEXT)  # fmt: skip
    buf = io.BytesIO()
    wb.save(buf)
    data = buf.getvalue()
    sha = hashlib.sha256(data).hexdigest()[:16]
    with eng.begin() as c:
        c.execute(update(t_batch).where(t_batch.c.batch_id == batch_id)
                  .values(downloads=list(b["downloads"] or []) + [{"at": store.now().isoformat(), "sha16": sha, "n": len(orders)}]))  # fmt: skip
        store._event(
            c,
            s["seller_id"],
            "po_download",
            "seller",
            {"batch_id": batch_id, "n": len(orders), "sha16": sha, "purged": gone},
        )
    return data, f"발주서_{batch_id}.xlsx"


# ── 송장 ────────────────────────────────────────────────────────────────
def upload_tracking(eng, token: str, client: str, filename: str, data: bytes) -> dict:
    s = store.resolve(eng, token, client)
    rows, problems = corp_po.read_tracking(filename, data)
    done = 0
    with eng.begin() as c:
        for r in rows:
            o = (
                c.execute(
                    select(t_order).where(
                        and_(t_order.c.seller_id == s["seller_id"], t_order.c.order_id == r["order_id"])
                    )
                )
                .mappings()
                .first()
            )
            if o is None:
                problems.append({"order_id": r["order_id"], "why": "내 주문이 아니에요"})
                continue
            if o["status"] == "new":
                problems.append({"order_id": r["order_id"], "why": "아직 발주서에 들어가지 않은 주문이에요"})
                continue
            if o["tracking"] and o["tracking"] != r["tracking"]:
                problems.append({"order_id": r["order_id"], "why": "이미 다른 송장이 있어요 — 운영팀에 문의해 주세요"})
                continue
            if o["tracking"] == r["tracking"]:
                continue
            c.execute(update(t_order).where(t_order.c.order_id == o["order_id"])
                      .values(tracking=_txt(r["tracking"], 40), status="shipped", shipped_at=store.now()))  # fmt: skip
            done += 1
        store._event(c, s["seller_id"], "tracking_upload", "seller", {"set": done, "problems": len(problems)})
    return {"set": done, "problems": problems}


# ── 알림 ────────────────────────────────────────────────────────────────
def _alerts_for(eng, seller_id: str, at: datetime) -> dict:
    stocks = stock_of(eng, seller_id)
    with eng.connect() as c:
        prods = c.execute(select(products.t_product.c.product_id, products.t_product.c.name, products.t_product.c.status)
                          .where(products.t_product.c.seller_id == seller_id)).mappings().all()  # fmt: skip
        orders = (
            c.execute(select(t_order).where(and_(t_order.c.seller_id == seller_id, t_order.c.status != "shipped")))
            .mappings()
            .all()
        )
    sold = [{"product_id": p["product_id"], "name": p["name"], "restock_on": stocks[p["product_id"]]["restock_on"]}
            for p in prods if p["status"] == "approved" and stocks.get(p["product_id"], {}).get("sold_out")]  # fmt: skip
    late = [o for o in orders if _delayed(o, at)]
    return {
        "sold_out": sold,
        "delayed_orders": len(late),
        "no_tracking": sum(1 for o in orders if o["status"] == "po"),
        "new_orders": sum(1 for o in orders if o["status"] == "new"),
    }


def my_alerts(eng, token: str, client: str, *, at: datetime | None = None) -> dict:
    s = store.resolve(eng, token, client)
    return _alerts_for(eng, s["seller_id"], at or store.now())


def all_alerts(eng, *, at: datetime | None = None) -> list[dict]:
    """운영자 화면 — 셀러별 숫자와 품절 상품 이름만(받는 분 정보 없음)."""
    at = at or store.now()
    out = []
    for s in store.list_sellers(eng):
        a = _alerts_for(eng, s["seller_id"], at)
        if a["sold_out"] or a["delayed_orders"] or a["no_tracking"] or a["new_orders"]:
            out.append({"seller_id": s["seller_id"], "name": s["name"], "status_label": s["status_label"], **a})
    return out


# ── 보존 ────────────────────────────────────────────────────────────────
def purge(eng, at: datetime | None = None) -> int:
    """송장 등록 뒤 30일, 출고 안 된 주문은 올린 뒤 90일 — 받는 분 정보 삭제. 셀러 종료 뒤 1년이면 공급사 연락처도."""
    at = at or store.now()
    n = 0
    with eng.begin() as c:
        for r in c.execute(select(t_order.c.order_id, t_order.c.seller_id, t_order.c.shipped_at, t_order.c.created_at)
                           .where(t_order.c.ship_enc.is_not(None))).mappings().all():  # fmt: skip
            base, keep = (
                (r["shipped_at"], KEEP_AFTER_SHIP_DAYS) if r["shipped_at"] else (r["created_at"], KEEP_UNSHIPPED_DAYS)
            )
            base = base if base.tzinfo else base.replace(tzinfo=store.KST)
            if base + timedelta(days=keep) <= at:
                c.execute(
                    update(t_order).where(t_order.c.order_id == r["order_id"]).values(ship_enc=None, purged_at=at)
                )
                n += 1
        cut = at - timedelta(days=store.CONTACT_KEEP_DAYS)
        ended = [x[0] for x in c.execute(select(store.t_seller.c.seller_id)
                                          .where(and_(store.t_seller.c.status == "ended", store.t_seller.c.ended_at <= cut))).all()]  # fmt: skip
        if ended:
            n += c.execute(update(t_supplier).where(and_(t_supplier.c.seller_id.in_(ended), t_supplier.c.contact_enc.is_not(None)))
                           .values(contact_enc=None)).rowcount  # fmt: skip
    return n


def order_csv_template() -> str:
    return ",".join(ORDER_HEADERS) + "\n"
