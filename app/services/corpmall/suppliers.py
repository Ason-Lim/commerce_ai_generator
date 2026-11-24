"""공급 거래처 (2026-11-24) — 설계 claude/b2b_supplier_po_2026-11-24.md.

commerce_ai 가 공급사에 직접 발주하는 '발주사'가 될 때 필요한 거래처 기본 정보.
(app/admin/b2b/suppliers.py 는 근거 저장소에서 '공급사 후보'를 모으는 것 — 계약 전. 이 파일은 거래하기로 한 곳.)

* 거래처: 이름(고유) · 사업자등록번호 · 발주 받는 담당자(이름·메일·전화 — **암호화**) · 발주 방식(메일·엑셀·API) ·
  결제 조건 · 기본 납기(영업일) · 단가 기준(부가세 별도/포함) · 메모 · 사용 여부.
* 목록에는 담당자 연락처를 넣지 않는다(있는지만). 상세에서만 복호화.
* 개인 사업자의 사업자등록번호는 개인정보일 수 있어 목록에서는 가운데를 가린다.
"""

from __future__ import annotations

import re
import secrets

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Table, Text, and_, select, update

from app.services.corpmall import store

ORDER_METHODS = {"email": "메일", "excel": "엑셀 전달", "api": "API"}
VAT_MODES = {"excluded": "부가세 별도", "included": "부가세 포함"}
EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]{1,64}@[A-Za-z0-9.-]{1,120}\.[A-Za-z]{2,}$")

t_supplier = Table(
    "corpmall_supplier",
    store.meta,
    Column("supplier_id", String(12), primary_key=True),
    Column("name", String(40), unique=True, nullable=False),
    Column("biz_no", String(12)),
    Column("contact_enc", Text),
    Column("order_method", String(8), nullable=False, default="email"),
    Column("payment_terms", String(120)),
    Column("lead_days", Integer),
    Column("vat_mode", String(10), nullable=False, default="excluded"),
    Column("memo", String(300)),
    Column("active", Boolean, nullable=False, default=True),
    Column("created_at", DateTime(timezone=True)),
    Column("updated_at", DateTime(timezone=True)),
)


def _clean(v, n: int) -> str:
    return " ".join(str(v or "").split())[:n]


def _check(d: dict) -> tuple[dict, dict | None]:
    name = _clean(d.get("name"), 40)
    if not name:
        raise store.MallError("거래처 이름을 넣어 주세요")
    biz = re.sub(r"\D", "", str(d.get("biz_no") or ""))
    if biz and len(biz) != 10:
        raise store.MallError("사업자등록번호는 숫자 10자리예요")
    method = d.get("order_method") or "email"
    vat = d.get("vat_mode") or "excluded"
    if method not in ORDER_METHODS or vat not in VAT_MODES:
        raise store.MallError("발주 방식·단가 기준을 다시 골라 주세요")
    lead = d.get("lead_days")
    if lead not in (None, ""):
        try:
            lead = int(lead)
        except (TypeError, ValueError) as e:
            raise store.MallError("기본 납기는 영업일 수(숫자)로 적어 주세요") from e
        if not 0 <= lead <= 60:
            raise store.MallError("기본 납기는 0~60 영업일이에요")
    else:
        lead = None
    c = d.get("contact") or {}
    contact = {
        "name": _clean(c.get("name"), 30),
        "email": _clean(c.get("email"), 120),
        "phone": re.sub(r"[^\d-]", "", str(c.get("phone") or ""))[:20],
    }
    if contact["email"] and not EMAIL_RE.fullmatch(contact["email"]):
        raise store.MallError("담당자 메일 주소를 확인해 주세요")
    if method == "email" and not contact["email"]:
        raise store.MallError("메일로 발주하는 거래처는 발주 받을 메일 주소가 있어야 해요")
    vals = {
        "name": name,
        "biz_no": biz or None,
        "order_method": method,
        "payment_terms": _clean(d.get("payment_terms"), 120) or None,
        "lead_days": lead,
        "vat_mode": vat,
        "memo": _clean(d.get("memo"), 300) or None,
        "active": bool(d.get("active", True)),
    }
    return vals, (contact if any(contact.values()) else None)


def _mask_biz(b: str | None) -> str | None:
    return f"{b[:3]}-**-***{b[-2:]}" if b and len(b) == 10 else None


def _row(r, *, full: bool) -> dict:
    d = {
        "supplier_id": r["supplier_id"],
        "name": r["name"],
        "order_method": r["order_method"],
        "order_method_label": ORDER_METHODS.get(r["order_method"], r["order_method"]),
        "payment_terms": r["payment_terms"],
        "lead_days": r["lead_days"],
        "vat_mode": r["vat_mode"],
        "vat_label": VAT_MODES.get(r["vat_mode"], r["vat_mode"]),
        "memo": r["memo"],
        "active": r["active"],
        "has_contact": r["contact_enc"] is not None,
    }
    if full:
        d["biz_no"] = r["biz_no"]
        d["contact"] = store._dec(r["contact_enc"]) if r["contact_enc"] else None
    else:
        d["biz_no_masked"] = _mask_biz(r["biz_no"])
    return d


def save(eng, data: dict, supplier_id: str | None = None, *, by: str = "operator") -> dict:
    """만들기(supplier_id 없음) 또는 고치기. 연락처를 비워 보내면 기존 연락처를 지운다."""
    vals, contact = _check(data)
    t = store.now()
    vals.update(contact_enc=store._enc(contact) if contact else None, updated_at=t)
    with eng.begin() as c:
        dup = c.execute(select(t_supplier.c.supplier_id).where(t_supplier.c.name == vals["name"])).scalar()
        if dup and dup != supplier_id:
            raise store.MallError("같은 이름의 거래처가 이미 있어요")
        if supplier_id:
            n = c.execute(update(t_supplier).where(t_supplier.c.supplier_id == supplier_id).values(**vals)).rowcount
            if not n:
                raise store.MallError("없는 거래처예요")
        else:
            supplier_id = "S" + secrets.token_hex(4).upper()
            c.execute(t_supplier.insert().values(supplier_id=supplier_id, created_at=t, **vals))
    return get(eng, supplier_id, full=True)


def get(eng, supplier_id: str, *, full: bool = False) -> dict | None:
    with eng.connect() as c:
        r = c.execute(select(t_supplier).where(t_supplier.c.supplier_id == supplier_id)).mappings().first()
    return _row(r, full=full) if r else None


def list_all(eng, *, active_only: bool = False) -> list[dict]:
    q = select(t_supplier).order_by(t_supplier.c.name)
    if active_only:
        q = q.where(t_supplier.c.active.is_(True))
    with eng.connect() as c:
        return [_row(r, full=False) for r in c.execute(q).mappings()]


def by_ids(eng, ids: list[str]) -> dict[str, dict]:
    if not ids:
        return {}
    with eng.connect() as c:
        rows = c.execute(select(t_supplier).where(and_(t_supplier.c.supplier_id.in_(ids)))).mappings().all()
    return {r["supplier_id"]: _row(r, full=True) for r in rows}


__all__ = ["ORDER_METHODS", "VAT_MODES", "t_supplier", "save", "get", "list_all", "by_ids"]
