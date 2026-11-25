"""셀러 상품 등록·검수 ② (창 5, 2026-11-25) — 설계 claude/stage5_seller_design_2026-11-25.md.

* **신고값과 확인값을 나눈다.** 셀러가 적은 원산지·인증 표기·당도는 ``declared``('판매자 표기')에만 들어간다.
  운영자가 서류·사진 등 근거를 보고 확인한 값만 ``verified``('확인됨')에 들어간다(근거 메모 필수).
  셀러가 신고값을 바꾸면 그 칸의 확인값은 지운다 — 옛 확인이 새 값을 보증하지 않게.
* **검수 대기 → 승인만.** 새로 등록하거나 고치면 '검수 대기'. 승인·반려·확인은 운영자만(``store._operator``).
  승인한 상품을 셀러가 고치면 다시 '검수 대기'로 돌아간다.
* **노출 없음(결정 2).** 승인돼도 고객 화면·추천 후보·업체 제공 상품 칸과 연결하지 않는다. 관리자 화면에만.
* **격리.** 셀러 쪽 함수는 코드 → 셀러 번호를 풀고 그 셀러의 상품만 읽고 쓴다. 남의 상품 번호는 '없는 상품'.
* 가격·배송비는 셀러의 판매 조건이라 확인값 대상이 아니다. 판매처 주소는 https 만.
"""

from __future__ import annotations

import csv
import io
import re
import secrets

from sqlalchemy import JSON, Column, DateTime, Integer, MetaData, String, Table, and_, func, select, update

from app.services.seller import store

DECLARED = {"origin": "원산지", "cert": "인증 표기", "brix": "당도(브릭스)"}
STATUSES = {"pending": "검수 대기", "approved": "승인", "rejected": "반려", "withdrawn": "판매 중지(셀러)"}
MAX_PER_SELLER = 2000
MAX_CSV_ROWS = 300
CSV_HEADERS = {
    "상품명": "name",
    "용량": "volume",
    "가격": "price",
    "배송비": "ship_fee",
    "원산지": "origin",
    "인증 표기": "cert",
    "당도": "brix",
    "판매처 주소": "sale_url",
}
URL_RE = re.compile(r"^https://[^\s<>\"']{4,290}$")

meta = MetaData()
t_product = Table(
    "seller_product",
    meta,
    Column("product_id", String(12), primary_key=True),
    Column("seller_id", String(12), index=True, nullable=False),
    Column("name", String(80), nullable=False),
    Column("volume", String(40)),
    Column("price", Integer),  # 원 — 셀러 판매가
    Column("ship_fee", Integer),  # 원 — None 이면 '판매처 확인'
    Column("sale_url", String(300)),
    Column("declared", JSON, nullable=False),  # 판매자 표기 {origin, cert, brix}
    Column("verified", JSON, nullable=False),  # 확인됨 {key: {value, by, at, note}}
    Column("status", String(10), nullable=False, default="pending"),
    Column("review_note", String(200)),  # 반려 이유·승인 메모 (셀러에게 보임)
    Column("created_at", DateTime(timezone=True)),
    Column("updated_at", DateTime(timezone=True)),
    Column("reviewed_at", DateTime(timezone=True)),
)


def engine(url: str | None = None):
    eng = store.engine(url)
    meta.create_all(eng)
    return eng


def _int(v, label: str, lo: int, hi: int, *, allow_none: bool = False) -> int | None:
    if v is None or (isinstance(v, str) and not v.strip()):
        if allow_none:
            return None
        raise store.SellerError(f"{label}을(를) 넣어 주세요")
    try:
        n = int(str(v).replace(",", "").replace("원", "").strip())
    except ValueError as e:
        raise store.SellerError(f"{label}은(는) 숫자로 넣어 주세요") from e
    if not lo <= n <= hi:
        raise store.SellerError(f"{label}은(는) {lo:,}~{hi:,} 사이로 넣어 주세요")
    return n


def _brix(v) -> float | None:
    if v is None or (isinstance(v, str) and not v.strip()):
        return None
    try:
        b = round(float(str(v).replace("brix", "").replace("Brix", "").replace("°", "").strip()), 1)
    except ValueError as e:
        raise store.SellerError("당도는 숫자로 넣어 주세요 (예: 12.5)") from e
    if not 0 <= b <= 40:
        raise store.SellerError("당도는 0~40 사이로 넣어 주세요")
    return b


def _txt(v, n: int) -> str:
    return " ".join(str(v or "").split())[:n]


def check_fields(raw: dict) -> dict:
    """셀러가 넣는 칸 검사 — 모르는 칸은 거부."""
    extra = set(raw) - {"name", "volume", "price", "ship_fee", "sale_url", *DECLARED}
    if extra:
        raise store.SellerError("받지 않는 칸이 있어요: " + ", ".join(sorted(extra)))
    name = _txt(raw.get("name"), 80)
    if not name:
        raise store.SellerError("상품명을 넣어 주세요")
    url = str(raw.get("sale_url") or "").strip()
    if url and not URL_RE.match(url):
        raise store.SellerError("판매처 주소는 https:// 로 시작하는 주소만 넣어 주세요")
    return {
        "name": name,
        "volume": _txt(raw.get("volume"), 40),
        "price": _int(raw.get("price"), "가격", 100, 10_000_000),
        "ship_fee": _int(raw.get("ship_fee"), "배송비", 0, 100_000, allow_none=True),
        "sale_url": url,
        "declared": {
            "origin": _txt(raw.get("origin"), 40),
            "cert": _txt(raw.get("cert"), 60),
            "brix": _brix(raw.get("brix")),
        },
    }


def facts(declared: dict, verified: dict) -> list[dict]:
    """칸마다 보여 줄 값과 출처 — 확인값이 있으면 '확인됨', 없으면 '판매자 표기'."""
    out = []
    for k, label in DECLARED.items():
        d = (declared or {}).get(k)
        v = (verified or {}).get(k)
        if d in (None, "") and not v:
            continue
        if v:
            out.append({"key": k, "label": label, "value": v["value"], "source": "verified", "source_label": "확인됨",
                        "declared": d, "differs": str(v["value"]) != str(d if d is not None else "")})  # fmt: skip
        else:
            out.append({"key": k, "label": label, "value": d, "source": "seller", "source_label": "판매자 표기",
                        "declared": d, "differs": False})  # fmt: skip
    return out


def _view(r, *, operator: bool = False) -> dict:
    d = {
        "product_id": r["product_id"],
        "name": r["name"],
        "volume": r["volume"] or "",
        "price": r["price"],
        "ship_fee": r["ship_fee"],
        "sale_url": r["sale_url"] or "",
        "declared": r["declared"] or {},
        "facts": facts(r["declared"], r["verified"]),
        "status": r["status"],
        "status_label": STATUSES.get(r["status"], r["status"]),
        "review_note": r["review_note"] or "",
        "updated_at": r["updated_at"].isoformat() if r["updated_at"] else None,
    }
    if operator:
        d["seller_id"] = r["seller_id"]
        d["verified"] = r["verified"] or {}
    return d


# ── 셀러 쪽 (코드로만) ──────────────────────────────────────────────────
def _mine(c, seller_id: str, product_id: str):
    r = (
        c.execute(
            select(t_product).where(and_(t_product.c.seller_id == seller_id, t_product.c.product_id == product_id))
        )
        .mappings()
        .first()
    )
    if r is None:
        raise store.SellerError("없는 상품이에요")
    return r


def list_mine(eng, token: str, client: str) -> list[dict]:
    s = store.resolve(eng, token, client)
    with eng.connect() as c:
        rows = (
            c.execute(select(t_product).where(t_product.c.seller_id == s["seller_id"]).order_by(t_product.c.created_at))
            .mappings()
            .all()
        )
    return [_view(r) for r in rows]


def _insert(c, seller_id: str, f: dict) -> str:
    pid = "P" + secrets.token_hex(4).upper()
    t = store.now()
    c.execute(t_product.insert().values(product_id=pid, seller_id=seller_id, declared=f.pop("declared"), verified={},
                                        status="pending", created_at=t, updated_at=t, **f))  # fmt: skip
    return pid


def _count(c, seller_id: str) -> int:
    return c.execute(select(func.count()).select_from(t_product).where(t_product.c.seller_id == seller_id)).scalar_one()


def save(eng, token: str, client: str, raw: dict, product_id: str | None = None) -> dict:
    """새 상품(product_id 없음) 또는 내 상품 고치기 — 어느 쪽이든 '검수 대기'로."""
    s = store.resolve(eng, token, client)
    f = check_fields(raw)
    with eng.begin() as c:
        if product_id is None:
            if _count(c, s["seller_id"]) >= MAX_PER_SELLER:
                raise store.SellerError(f"상품은 {MAX_PER_SELLER:,}개까지 등록할 수 있어요")
            pid = _insert(c, s["seller_id"], dict(f))
            store._event(c, s["seller_id"], "product_added", "seller", {"product_id": pid})
        else:
            r = _mine(c, s["seller_id"], product_id)
            pid = product_id
            verified = dict(r["verified"] or {})
            dropped = [k for k in DECLARED if k in verified and (r["declared"] or {}).get(k) != f["declared"].get(k)]
            for k in dropped:
                verified.pop(k)
            c.execute(
                update(t_product)
                .where(t_product.c.product_id == pid)
                .values(
                    **{k: v for k, v in f.items() if k != "declared"},
                    declared=f["declared"],
                    verified=verified,
                    status="pending",
                    review_note=None,
                    updated_at=store.now(),
                )  # fmt: skip
            )
            store._event(c, s["seller_id"], "product_edited", "seller",
                         {"product_id": pid, "from": r["status"], "verified_dropped": dropped})  # fmt: skip
        r = _mine(c, s["seller_id"], pid)
    return _view(r)


def withdraw(eng, token: str, client: str, product_id: str) -> dict:
    """셀러가 자기 상품 판매를 멈춤 — 다시 고치면 검수 대기로."""
    s = store.resolve(eng, token, client)
    with eng.begin() as c:
        _mine(c, s["seller_id"], product_id)
        c.execute(update(t_product).where(t_product.c.product_id == product_id)
                  .values(status="withdrawn", updated_at=store.now()))  # fmt: skip
        store._event(c, s["seller_id"], "product_withdrawn", "seller", {"product_id": product_id})
        r = _mine(c, s["seller_id"], product_id)
    return _view(r)


def import_csv(eng, token: str, client: str, text: str) -> dict:
    """CSV 한꺼번에 등록 — 한 줄이라도 틀리면 아무것도 저장하지 않고 줄마다 이유를 돌려준다."""
    s = store.resolve(eng, token, client)
    text = (text or "").lstrip("﻿")
    rd = csv.DictReader(io.StringIO(text))
    heads = [h.strip() for h in (rd.fieldnames or [])]
    unknown = [h for h in heads if h not in CSV_HEADERS]
    if "상품명" not in heads or "가격" not in heads:
        raise store.SellerError("첫 줄에 칸 이름이 있어야 해요 (적어도 상품명·가격): " + ", ".join(CSV_HEADERS))
    if unknown:
        raise store.SellerError("모르는 칸 이름이 있어요: " + ", ".join(unknown))
    rows, errors = [], []
    for i, row in enumerate(rd, start=2):
        if i - 1 > MAX_CSV_ROWS:
            raise store.SellerError(f"한 번에 {MAX_CSV_ROWS}줄까지 올릴 수 있어요")
        raw = {CSV_HEADERS[k.strip()]: v for k, v in row.items() if k and k.strip() in CSV_HEADERS}
        if not any(str(v or "").strip() for v in raw.values()):
            continue
        try:
            rows.append(check_fields(raw))
        except store.SellerError as e:
            errors.append({"line": i, "error": str(e)})
    if errors:
        return {"ok": False, "added": 0, "errors": errors}
    if not rows:
        raise store.SellerError("올릴 상품이 없어요")
    with eng.begin() as c:
        if _count(c, s["seller_id"]) + len(rows) > MAX_PER_SELLER:
            raise store.SellerError(f"상품은 {MAX_PER_SELLER:,}개까지 등록할 수 있어요")
        ids = [_insert(c, s["seller_id"], dict(f)) for f in rows]
        store._event(c, s["seller_id"], "product_csv", "seller", {"n": len(ids)})
    return {"ok": True, "added": len(ids), "errors": []}


# ── 운영자 ──────────────────────────────────────────────────────────────
def _row(c, product_id: str):
    r = c.execute(select(t_product).where(t_product.c.product_id == product_id)).mappings().first()
    if r is None:
        raise store.SellerError("없는 상품이에요")
    return r


def queue(eng, status: str = "pending", seller_id: str | None = None) -> list[dict]:
    q = select(t_product)
    if status != "all":
        q = q.where(t_product.c.status == status)
    if seller_id:
        q = q.where(t_product.c.seller_id == seller_id)
    with eng.connect() as c:
        rows = c.execute(q.order_by(t_product.c.updated_at)).mappings().all()
        names = dict(c.execute(select(store.t_seller.c.seller_id, store.t_seller.c.name)).all())
    return [dict(_view(r, operator=True), seller_name=names.get(r["seller_id"], "")) for r in rows]


def verify(eng, product_id: str, key: str, value, *, by: str, note: str) -> dict:
    """운영자가 근거를 보고 한 칸을 '확인됨'으로 — 근거 메모 필수. value 가 비면 그 칸 확인을 지운다."""
    by = store._operator(by)
    if key not in DECLARED:
        raise store.SellerError("확인할 수 있는 칸은 원산지·인증 표기·당도예요")
    note = _txt(note, 200)
    clear = value is None or (isinstance(value, str) and not value.strip())
    if not clear and not note:
        raise store.SellerError("무엇을 보고 확인했는지 근거를 적어 주세요 (예: 원산지 증명서 2026-11 사본)")
    val = None if clear else (_brix(value) if key == "brix" else _txt(value, 60))
    with eng.begin() as c:
        r = _row(c, product_id)
        v = dict(r["verified"] or {})
        if clear:
            v.pop(key, None)
        else:
            v[key] = {"value": val, "by": by, "at": store.now().isoformat(), "note": note}
        c.execute(update(t_product).where(t_product.c.product_id == product_id).values(verified=v))
        store._event(c, r["seller_id"], "product_verify", by, {"product_id": product_id, "key": key, "clear": clear})
        r = _row(c, product_id)
    return _view(r, operator=True)


def review(eng, product_id: str, decision: str, *, by: str, note: str = "") -> dict:
    """승인·반려 — 운영자만. 반려는 이유 필수(셀러에게 보임). 셀러가 '판매 중지'한 상품은 승인하지 않음."""
    by = store._operator(by)
    if decision not in ("approved", "rejected"):
        raise store.SellerError("승인 또는 반려만 할 수 있어요")
    note = _txt(note, 200)
    if decision == "rejected" and not note:
        raise store.SellerError("반려 이유를 적어 주세요 (셀러에게 보여요)")
    with eng.begin() as c:
        r = _row(c, product_id)
        if r["status"] == "withdrawn":
            raise store.SellerError("셀러가 판매를 멈춘 상품이에요")
        s = c.execute(select(store.t_seller.c.status).where(store.t_seller.c.seller_id == r["seller_id"])).scalar_one()
        if decision == "approved" and s != "active":
            raise store.SellerError("입점 승인 전(또는 정지·종료) 셀러의 상품은 승인할 수 없어요")
        c.execute(update(t_product).where(t_product.c.product_id == product_id)
                  .values(status=decision, review_note=note or None, reviewed_at=store.now()))  # fmt: skip
        store._event(c, r["seller_id"], "product_review", by, {"product_id": product_id, "to": decision})
        r = _row(c, product_id)
    return _view(r, operator=True)


def csv_template() -> str:
    return (
        ",".join(CSV_HEADERS)
        + "\n"
        + "제주 감귤 5kg,5kg,23900,0,제주,GAP,12,https://smartstore.naver.com/예시/products/1\n"
    )


__all__ = ["check_fields", "facts", "import_csv", "list_mine", "queue", "review", "save", "verify", "withdraw"]
