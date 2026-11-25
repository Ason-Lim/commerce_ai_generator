"""셀러 월 이용료 ④ (창 5, 2026-11-25) — 표시·기록만. 금액은 시험용 가짜 값."""

from __future__ import annotations

import os
from datetime import date

import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient

os.environ.setdefault("CORPMALL_KEY", Fernet.generate_key().decode())

from app.services.corpmall import store as corp  # noqa: E402
from app.services.seller import billing as bill  # noqa: E402
from app.services.seller import store as sel  # noqa: E402

H = {"X-Access-Token": "test-token"}
IP = "1.1.1.1"
FEE = 1000  # 가짜 금액


@pytest.fixture
def eng():
    corp.reset_limits()
    e = bill.engine()
    with e.begin() as c:
        for t in (bill.t_invoice, bill.t_plan, sel.t_event, sel.t_key, sel.t_seller):
            c.execute(t.delete())
    return e


def _seller(eng, name="가농장"):
    s = sel.create_seller(eng, name=name, kind="direct", contact={"name": "김", "email": "k@a.kr"}, by="operator")
    sel.set_status(eng, s["seller_id"], "active", by="operator", reason="ok")
    return s, sel.issue_key(eng, s["seller_id"], by="operator")["code"]


def test_money_rules():
    assert bill.money(1000, "excluded") == (1000, 100, 1100)
    assert bill.money(1100, "included") == (1000, 100, 1100)


def test_invoices_from_start_month_idempotent(eng):
    s, _ = _seller(eng)
    bill.set_plan(
        eng, s["seller_id"], plan_name="기본", monthly_fee=FEE, vat_mode="excluded", starts_on="2026-10", by="operator"
    )
    assert bill.ensure_invoices(eng, today=date(2026, 12, 15)) == 3
    assert bill.ensure_invoices(eng, today=date(2026, 12, 20)) == 0
    inv = bill.invoices(eng, s["seller_id"])
    assert [i["month"] for i in inv] == ["2026-12", "2026-11", "2026-10"]
    assert all(i["total"] == 1100 and i["status"] == "draft" for i in inv)


def test_no_invoice_after_contract_end_or_for_invited(eng):
    s, _ = _seller(eng)
    inv_only = sel.create_seller(
        eng, name="나수산", kind="direct", contact={"name": "이", "email": "l@b.kr"}, by="operator"
    )
    for sid in (s["seller_id"], inv_only["seller_id"]):
        bill.set_plan(
            eng, sid, plan_name="기본", monthly_fee=FEE, vat_mode="excluded", starts_on="2026-01", by="operator"
        )
    sel.set_status(eng, s["seller_id"], "ended", by="operator", reason="종료")
    end_month = sel.now().strftime("%Y-%m")
    bill.ensure_invoices(eng, today=date(2027, 6, 1))
    assert max(i["month"] for i in bill.invoices(eng, s["seller_id"])) == end_month
    assert bill.invoices(eng, inv_only["seller_id"]) == []


@pytest.mark.parametrize("who", ["ai", "ai:seller_cs", "system:billing", "seller", None])
def test_only_operator_changes_money(eng, who):
    s, _ = _seller(eng)
    with pytest.raises(sel.SellerError, match="운영자만"):
        bill.set_plan(
            eng, s["seller_id"], plan_name="기본", monthly_fee=FEE, vat_mode="excluded", starts_on="2026-10", by=who
        )
    bill.set_plan(
        eng, s["seller_id"], plan_name="기본", monthly_fee=FEE, vat_mode="excluded", starts_on="2026-10", by="operator"
    )
    bill.ensure_invoices(eng, today=date(2026, 10, 2))
    iid = bill.invoices(eng, s["seller_id"])[0]["invoice_id"]
    with pytest.raises(sel.SellerError, match="운영자만"):
        bill.adjust(eng, iid, 0, by=who, reason="감면")
    for to in ("issued", "waived"):
        with pytest.raises(sel.SellerError, match="운영자만"):
            bill.mark(eng, iid, to, by=who, note="x", tax_invoice_no="1")
    assert bill.invoices(eng, s["seller_id"])[0]["total"] == 1100


def test_adjust_issue_pay_flow_and_locks(eng):
    s, _ = _seller(eng)
    bill.set_plan(
        eng, s["seller_id"], plan_name="기본", monthly_fee=FEE, vat_mode="excluded", starts_on="2026-10", by="operator"
    )
    bill.ensure_invoices(eng, today=date(2026, 10, 2))
    iid = bill.invoices(eng, s["seller_id"])[0]["invoice_id"]
    with pytest.raises(sel.SellerError, match="이유"):
        bill.adjust(eng, iid, 500, by="operator", reason="")
    got = bill.adjust(eng, iid, 500, by="operator", reason="첫 달 감면")
    assert got["total"] == 550 and got["history"][-1]["before"] == 1100
    with pytest.raises(sel.SellerError, match="승인번호"):
        bill.mark(eng, iid, "issued", by="operator")
    with pytest.raises(sel.SellerError, match="바꿀 수 없어요"):
        bill.mark(eng, iid, "paid", by="operator", note="입금")  # 발행 전 입금 표시 안 됨
    bill.mark(eng, iid, "issued", by="operator", tax_invoice_no="20261102-0000")
    with pytest.raises(sel.SellerError, match="금액을 바꿀 수 없어요"):
        bill.adjust(eng, iid, 0, by="operator", reason="x")
    with pytest.raises(sel.SellerError, match="근거"):
        bill.mark(eng, iid, "paid", by="operator", note="")
    assert bill.mark(eng, iid, "paid", by="operator", note="11-30 입금")["status"] == "paid"


def test_plan_change_does_not_touch_issued_months(eng):
    s, _ = _seller(eng)
    bill.set_plan(
        eng, s["seller_id"], plan_name="기본", monthly_fee=FEE, vat_mode="excluded", starts_on="2026-10", by="operator"
    )
    bill.ensure_invoices(eng, today=date(2026, 10, 2))
    bill.set_plan(
        eng,
        s["seller_id"],
        plan_name="확장",
        monthly_fee=FEE * 2,
        vat_mode="excluded",
        starts_on="2026-10",
        by="operator",
    )
    bill.ensure_invoices(eng, today=date(2026, 11, 2))
    inv = {i["month"]: i["total"] for i in bill.invoices(eng, s["seller_id"])}
    assert inv == {"2026-10": 1100, "2026-11": 2200}


def test_seller_sees_only_own_billing_and_no_history(eng):
    a, ka = _seller(eng, "가농장")
    b, kb = _seller(eng, "나수산")
    bill.set_plan(
        eng, a["seller_id"], plan_name="기본", monthly_fee=FEE, vat_mode="excluded", starts_on="2026-10", by="operator"
    )
    mine = bill.my_billing(eng, kb, IP)
    assert mine["plan"] is None and mine["invoices"] == [] and "실제 청구" in mine["notice"]
    got = bill.my_billing(eng, ka, IP)
    assert got["plan"]["plan_name"] == "기본" and all("history" not in i for i in got["invoices"])


def test_events_have_no_amounts(eng):
    s, _ = _seller(eng)
    bill.set_plan(
        eng,
        s["seller_id"],
        plan_name="기본",
        monthly_fee=12345,
        vat_mode="excluded",
        starts_on="2026-10",
        by="operator",
    )
    assert "12345" not in str(sel.events(eng, s["seller_id"]))


def test_api(eng):
    from app.main import app

    cl = TestClient(app)
    s, k = _seller(eng)
    r = cl.post(f"/admin/api/seller-billing/{s['seller_id']}/plan", headers=H,
                json={"plan_name": "기본", "monthly_fee": FEE, "vat_mode": "included", "starts_on": "2026-11"})  # fmt: skip
    assert r.json()["plan"]["total"] == FEE
    summ = cl.get("/admin/api/seller-billing", headers=H).json()["sellers"]
    assert summ[0]["plan"]["plan_name"] == "기본"
    assert cl.post("/seller/api/billing", json={"key": k}).json()["billing"]["plan"]["total"] == FEE
    assert cl.get("/admin/api/seller-billing").status_code in (401, 403)
    assert not any("billing" in p and ("plan" in p or "invoice" in p) for p in
                   {r.path for r in app.routes if getattr(r, "path", "").startswith("/seller")})  # fmt: skip
