"""셀러 월 이용료·정산 화면 ④ (창 5, 2026-11-25) — **표시·기록만, 실제 청구·결제 없음**.

* 요금은 저장소에 쓰지 않는다(공개 저장소 — 로드맵 고정 원칙). 운영자가 관리자 화면에서 셀러마다
  요금제 이름·월 금액·부가세 기준(별도/포함)·청구 시작 달을 넣고, DB 에만 남는다.
* 청구 내역은 달마다 한 줄(셀러·달 유일). 시작 달부터 이번 달까지 계약 종료 전 달만 만든다(정지 중인 달도 만들고
  면제 여부는 운영자가 정함). 시작 달을 운영자가 고르므로 일할 계산은 하지 않는다.
* 상태: 예정 → 세금계산서 발행 기록(번호) → 입금 확인 / 면제. **금액 조정·면제·발행·입금 표시는 운영자만**(이유·근거 필수)
  — AI·자동 작업·셀러는 못 한다(로드맵: 이용료 환불·감면·예외는 사람이 맡는 일). 발행한 뒤에는 금액을 바꾸지 않는다.
* 정기결제·세금계산서 실제 발행(홈택스·PG)은 사업자등록 뒤.
"""

from __future__ import annotations

import secrets
from datetime import date

from sqlalchemy import JSON, Column, DateTime, Integer, MetaData, String, Table, UniqueConstraint, select, update

from app.services.seller import store

VAT_MODES = {"excluded": "부가세 별도", "included": "부가세 포함"}
INV_STATUS = {"draft": "청구 예정", "issued": "세금계산서 발행 기록", "paid": "입금 확인", "waived": "면제"}
MONTH = "%Y-%m"

meta = MetaData()
t_plan = Table(
    "seller_plan",
    meta,
    Column("seller_id", String(12), primary_key=True),
    Column("plan_name", String(40), nullable=False),
    Column("monthly_fee", Integer, nullable=False),  # 원 — 단가 기준(vat_mode)대로
    Column("vat_mode", String(8), nullable=False),
    Column("starts_on", String(7), nullable=False),  # YYYY-MM
    Column("memo", String(200)),
    Column("updated_at", DateTime(timezone=True)),
)
t_invoice = Table(
    "seller_invoice",
    meta,
    Column("invoice_id", String(12), primary_key=True),
    Column("seller_id", String(12), index=True, nullable=False),
    Column("month", String(7), nullable=False),
    Column("supply", Integer, nullable=False),  # 공급가액
    Column("vat", Integer, nullable=False),
    Column("total", Integer, nullable=False),
    Column("status", String(8), nullable=False, default="draft"),
    Column("tax_invoice_no", String(40)),
    Column("history", JSON),  # [{at, by, what, before, after, reason}]
    Column("created_at", DateTime(timezone=True)),
    UniqueConstraint("seller_id", "month", name="uq_seller_invoice_month"),
)


def engine(url: str | None = None):
    eng = store.engine(url)
    meta.create_all(eng)
    return eng


def money(fee: int, vat_mode: str) -> tuple[int, int, int]:
    """(공급가액, 부가세, 합계) — 폐쇄몰 발주서와 같은 규칙(별도: 10% 반올림 / 포함: 합 ÷ 1.1 반올림). 세무 검토 전."""
    if vat_mode == "included":
        supply = round(fee / 1.1)
        return supply, fee - supply, fee
    vat = round(fee * 0.1)
    return fee, vat, fee + vat


def _month(s: str) -> str:
    try:
        return date.fromisoformat(s.strip() + "-01").strftime(MONTH)
    except ValueError as e:
        raise store.SellerError("달은 2026-12 모양으로 넣어 주세요") from e


def _months(a: str, b: str) -> list[str]:
    y, m = map(int, a.split("-"))
    out = []
    while f"{y:04d}-{m:02d}" <= b:
        out.append(f"{y:04d}-{m:02d}")
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


def _hist(old, by: str, what: str, reason: str = "", before=None, after=None) -> list:
    return list(old or []) + [{"at": store.now().isoformat(timespec="seconds"), "by": by, "what": what,
                               "reason": reason, "before": before, "after": after}]  # fmt: skip


# ── 운영자 ──────────────────────────────────────────────────────────────
def set_plan(
    eng, seller_id: str, *, plan_name: str, monthly_fee, vat_mode: str, starts_on: str, by: str, memo: str = ""
) -> dict:
    by = store._operator(by)
    if store.detail(eng, seller_id) is None:
        raise store.SellerError("없는 셀러예요")
    name = " ".join((plan_name or "").split())[:40]
    if not name:
        raise store.SellerError("요금제 이름을 넣어 주세요")
    try:
        fee = int(str(monthly_fee).replace(",", "").strip())
    except ValueError as e:
        raise store.SellerError("월 이용료는 숫자로 넣어 주세요") from e
    if not 0 <= fee <= 10_000_000:
        raise store.SellerError("월 이용료는 0~10,000,000 사이로 넣어 주세요")
    if vat_mode not in VAT_MODES:
        raise store.SellerError("부가세 기준을 골라 주세요")
    vals = dict(plan_name=name, monthly_fee=fee, vat_mode=vat_mode, starts_on=_month(starts_on),
                memo=" ".join((memo or "").split())[:200], updated_at=store.now())  # fmt: skip
    with eng.begin() as c:
        old = c.execute(select(t_plan).where(t_plan.c.seller_id == seller_id)).mappings().first()
        if old:
            c.execute(update(t_plan).where(t_plan.c.seller_id == seller_id).values(**vals))
        else:
            c.execute(t_plan.insert().values(seller_id=seller_id, **vals))
        store._event(
            c, seller_id, "plan_set", by, {"plan": name, "changed": bool(old)}
        )  # 금액은 기록 detail 에 넣지 않음
    return plan_of(eng, seller_id)


def plan_of(eng, seller_id: str) -> dict | None:
    with eng.connect() as c:
        r = c.execute(select(t_plan).where(t_plan.c.seller_id == seller_id)).mappings().first()
    if r is None:
        return None
    supply, vat, total = money(r["monthly_fee"], r["vat_mode"])
    return {"plan_name": r["plan_name"], "monthly_fee": r["monthly_fee"], "vat_mode": r["vat_mode"],
            "vat_label": VAT_MODES[r["vat_mode"]], "starts_on": r["starts_on"], "memo": r["memo"] or "",
            "supply": supply, "vat": vat, "total": total}  # fmt: skip


def ensure_invoices(eng, *, today: date | None = None) -> int:
    """시작 달부터 이번 달까지 빠진 청구 줄을 만든다(계약 종료 달 뒤로는 안 만듦). 이미 있는 줄은 그대로."""
    today = today or store.now().date()
    upto = today.strftime(MONTH)
    n = 0
    with eng.begin() as c:
        plans = c.execute(select(t_plan)).mappings().all()
        for p in plans:
            s = c.execute(select(store.t_seller).where(store.t_seller.c.seller_id == p["seller_id"])).mappings().first()
            if s is None or s["status"] == "invited":
                continue
            last = upto
            if s["status"] == "ended" and s["ended_at"]:
                last = min(upto, s["ended_at"].strftime(MONTH))
            have = {
                r[0] for r in c.execute(select(t_invoice.c.month).where(t_invoice.c.seller_id == p["seller_id"])).all()
            }
            supply, vat, total = money(p["monthly_fee"], p["vat_mode"])
            for m in _months(p["starts_on"], last):
                if m in have:
                    continue
                c.execute(t_invoice.insert().values(invoice_id="I" + secrets.token_hex(4).upper(), seller_id=p["seller_id"],
                                                    month=m, supply=supply, vat=vat, total=total, status="draft",
                                                    history=_hist([], "system:billing", "created"), created_at=store.now()))  # fmt: skip
                n += 1
    return n


def _inv(c, invoice_id: str):
    r = c.execute(select(t_invoice).where(t_invoice.c.invoice_id == invoice_id)).mappings().first()
    if r is None:
        raise store.SellerError("없는 청구 내역이에요")
    return r


def _view(r, *, operator: bool = False) -> dict:
    d = {"invoice_id": r["invoice_id"], "month": r["month"], "supply": r["supply"], "vat": r["vat"], "total": r["total"],
         "status": r["status"], "status_label": INV_STATUS[r["status"]], "tax_invoice_no": r["tax_invoice_no"] or ""}  # fmt: skip
    if operator:
        d["seller_id"] = r["seller_id"]
        d["history"] = r["history"] or []
    return d


def adjust(eng, invoice_id: str, amount, *, by: str, reason: str) -> dict:
    """금액 조정(감면 포함) — 운영자만, 이유 필수, 발행 전(예정)에만. amount 는 합계가 아니라 요금제 기준 금액."""
    by = store._operator(by)
    reason = " ".join((reason or "").split())[:200]
    if not reason:
        raise store.SellerError("조정 이유를 적어 주세요")
    try:
        fee = int(str(amount).replace(",", "").strip())
    except ValueError as e:
        raise store.SellerError("금액은 숫자로 넣어 주세요") from e
    if not 0 <= fee <= 10_000_000:
        raise store.SellerError("금액은 0~10,000,000 사이로")
    with eng.begin() as c:
        r = _inv(c, invoice_id)
        if r["status"] != "draft":
            raise store.SellerError("발행·입금·면제한 청구는 금액을 바꿀 수 없어요")
        vm = c.execute(select(t_plan.c.vat_mode).where(t_plan.c.seller_id == r["seller_id"])).scalar() or "excluded"
        supply, vat, total = money(fee, vm)
        c.execute(update(t_invoice).where(t_invoice.c.invoice_id == invoice_id).values(
            supply=supply, vat=vat, total=total,
            history=_hist(r["history"], by, "adjust", reason, before=r["total"], after=total)))  # fmt: skip
        store._event(c, r["seller_id"], "invoice_adjust", by, {"invoice_id": invoice_id, "month": r["month"]})
        r = _inv(c, invoice_id)
    return _view(r, operator=True)


def mark(eng, invoice_id: str, to: str, *, by: str, note: str = "", tax_invoice_no: str = "") -> dict:
    """발행 기록·입금 확인·면제 — 운영자만. 면제·입금은 근거 메모 필수, 발행은 세금계산서 번호 필수."""
    by = store._operator(by)
    note = " ".join((note or "").split())[:200]
    no = " ".join((tax_invoice_no or "").split())[:40]
    allowed = {"issued": {"draft"}, "paid": {"issued"}, "waived": {"draft"}}
    if to not in allowed:
        raise store.SellerError("발행 기록·입금 확인·면제만 할 수 있어요")
    if to == "issued" and not no:
        raise store.SellerError("세금계산서 승인번호를 넣어 주세요")
    if to in ("paid", "waived") and not note:
        raise store.SellerError("근거를 적어 주세요 (입금 확인: 입금일·통장 표시 / 면제: 이유)")
    with eng.begin() as c:
        r = _inv(c, invoice_id)
        if r["status"] not in allowed[to]:
            raise store.SellerError(f"'{INV_STATUS[r['status']]}' 상태에서는 '{INV_STATUS[to]}'(으)로 바꿀 수 없어요")
        c.execute(update(t_invoice).where(t_invoice.c.invoice_id == invoice_id).values(
            status=to, tax_invoice_no=no or r["tax_invoice_no"],
            history=_hist(r["history"], by, to, note, before=r["status"], after=to)))  # fmt: skip
        store._event(c, r["seller_id"], "invoice_" + to, by, {"invoice_id": invoice_id, "month": r["month"]})
        r = _inv(c, invoice_id)
    return _view(r, operator=True)


def invoices(eng, seller_id: str, *, operator: bool = True) -> list[dict]:
    with eng.connect() as c:
        rows = (
            c.execute(select(t_invoice).where(t_invoice.c.seller_id == seller_id).order_by(t_invoice.c.month.desc()))
            .mappings()
            .all()
        )
    return [_view(r, operator=operator) for r in rows]


def summary(eng, *, today: date | None = None) -> list[dict]:
    """운영자 — 셀러별 요금제·미수(예정+발행 합계)·이번 달 상태."""
    ensure_invoices(eng, today=today)
    month = (today or store.now().date()).strftime(MONTH)
    out = []
    for s in store.list_sellers(eng):
        p = plan_of(eng, s["seller_id"])
        inv = invoices(eng, s["seller_id"])
        this = next((i for i in inv if i["month"] == month), None)
        out.append({"seller_id": s["seller_id"], "name": s["name"], "status_label": s["status_label"], "plan": p,
                    "open_total": sum(i["total"] for i in inv if i["status"] in ("draft", "issued")),
                    "this_month": this["status_label"] if this else "—"})  # fmt: skip
    return out


# ── 셀러 쪽 (코드로만, 보기만) ──────────────────────────────────────────
def my_billing(eng, token: str, client: str) -> dict:
    s = store.resolve(eng, token, client)
    ensure_invoices(eng)
    return {"plan": plan_of(eng, s["seller_id"]), "invoices": invoices(eng, s["seller_id"], operator=False),
            "notice": "아직 실제 청구·결제는 하지 않아요. 사업자등록 뒤 세금계산서·정기결제를 시작하면 따로 알려 드려요."}  # fmt: skip
