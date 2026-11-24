"""2단계 (2026-11-24) — 수주 문의 → 폐쇄몰 초안 · 행사별 매출·매입 정산."""

from __future__ import annotations

import os
from datetime import datetime

import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient

os.environ.setdefault("CORPMALL_KEY", Fernet.generate_key().decode())

from app.admin.b2b.models import Candidate  # noqa: E402
from app.services.b2b_inquiry import store as inq  # noqa: E402
from app.services.corpmall import draft, po, settle, suppliers  # noqa: E402
from app.services.corpmall import store as corp  # noqa: E402

KST = corp.KST
IN = datetime(2026, 12, 3, 10, 0, tzinfo=KST)
SHIP = {"name": "홍길동", "phone": "010-1234-5678", "zipcode": "04524", "address": "서울 중구 세종대로 110", "memo": ""}
H = {"X-Access-Token": "test-token"}
FORM = {
    "company": "샘플공사",
    "kind": "company",
    "occasion": "설",
    "due_date": "2027-01-20",
    "headcount": "3",
    "budget_per_person": "55,000",
    "delivery": "undecided",
    "message": "특산물",
    "contact_name": "김담당",
    "email": "buyer@example.org",
    "consent": True,
}
CANDS = [
    Candidate(
        candidate_id="cand-hangwa-01",
        supplier="가나식품",
        name="전통 한과 세트",
        option="18입",
        unit_price_quote=32000,
        price_kind="supplier_quote",
    ),
    Candidate(
        candidate_id="cand-gyul-02",
        supplier="제주농원",
        name="제주 감귤 5kg",
        observed_price=29000,
        price_kind="public_retail",
    ),
]


PROFILE = {"company_name": "커머스에이아이", "business_no": "000-00-00000", "address": "서울"}


@pytest.fixture(autouse=True)
def _profile(monkeypatch):
    """발주사 정보가 있어야 정식 발주(없으면 미확정) — 검토 반영 2026-11-24."""
    from app.admin.b2b import proposal

    monkeypatch.setattr(proposal, "load_profile", lambda path=None: dict(PROFILE))


@pytest.fixture
def eng(tmp_path, monkeypatch):
    monkeypatch.setenv("CS_DIR", str(tmp_path / "cs"))
    monkeypatch.setenv("OPERATOR_NOTIFY", "off")
    from app.admin.b2b import evidence

    monkeypatch.setattr(evidence, "all_candidates", lambda: list(CANDS))
    corp.reset_limits()
    inq.reset_limits()
    return corp.engine()


def _won_inquiry():
    ieng = inq.engine()
    iid = inq.submit(ieng, FORM, f"ip-{os.urandom(3).hex()}")["inquiry_id"]
    return ieng, iid


def test_candidates_search_and_price_kinds(eng):
    got = draft.candidates("한과")
    assert [c["candidate_id"] for c in got] == ["cand-hangwa-01"] and got[0]["quote"] == 32000
    allc = draft.candidates("")
    assert allc[0]["quote"] == 32000 and allc[1]["quote"] is None and "소매" in allc[1]["price_label"]


def test_draft_from_won_inquiry_only_quote_becomes_cost(eng):
    ieng, iid = _won_inquiry()
    kw = {
        "slug": f"st2-{os.urandom(2).hex()}",
        "opens_at": "2027-01-05T09:00",
        "closes_at": "2027-01-12T18:00",
        "candidate_ids": ["cand-hangwa-01", "cand-gyul-02"],
    }
    with pytest.raises(corp.MallError, match="수주"):
        draft.from_inquiry(eng, iid, **kw)
    inq.set_status(ieng, iid, "won", by="op")
    with pytest.raises(corp.MallError, match="하나 이상"):
        draft.from_inquiry(eng, iid, **{**kw, "candidate_ids": []})
    with pytest.raises(corp.MallError, match="없는 후보"):
        draft.from_inquiry(eng, iid, **{**kw, "candidate_ids": ["nope"]})
    m = draft.from_inquiry(eng, iid, **kw, default_item="cand-gyul-02")
    assert m["status"] == "draft" and m["client"] == "샘플공사" and m["title"] == "설 임직원 선물"
    assert m["delivery_mode"] == "individual" and m["inquiry_id"] == iid
    items = {i["supplier_candidate_id"]: i for i in m["items"]}
    assert (
        items["cand-hangwa-01"]["unit_cost"] == 32000 and items["cand-gyul-02"]["unit_cost"] is None
    )  # 관측가는 매입 단가 아님
    assert all("image" not in i or not i["image"] for i in m["items"])
    assert m["default_item_id"] == items["cand-gyul-02"]["id"]
    assert (
        m["contract"]["headcount"] == 3
        and m["contract"]["unit_price"] == 55000
        and "확정 전" in m["contract"]["source"]
    )
    assert any(e["kind"] == "mall_draft" and e["mall_id"] == m["mall_id"] for e in inq.get(ieng, iid)["events"])
    pub = corp.public_mall(m)
    assert "32000" not in repr(pub) and "가나식품" not in repr(pub)


def _settle_mall(eng, slug):
    s = suppliers.save(
        eng, {"name": f"정산식품-{slug}", "contact": {"email": "po@example.com"}, "vat_mode": "excluded"}
    )
    m = corp.create_mall(
        eng,
        {
            "slug": slug,
            "client": "샘플공사",
            "opens_at": "2026-12-01T09:00",
            "closes_at": "2026-12-10T18:00",
            "delivery_mode": "individual",
            "items": [{"id": "A", "name": "한과"}, {"id": "B", "name": "감귤"}],
        },
    )
    corp.set_status(eng, m["mall_id"], "open")
    codes = corp.issue_codes(eng, m["mall_id"], 4)
    po.set_suppliers(
        eng, m["mall_id"], {"A": {"supplier_id": s["supplier_id"], "unit_cost": 30000}, "B": {"supplier": "이름만농원"}}
    )
    return m, codes


def test_settlement_revenue_cost_margin(eng):
    m, codes = _settle_mall(eng, f"st2s-{os.urandom(2).hex()}")
    mid = m["mall_id"]
    for (_, code, _), item in zip(codes, "AAAB", strict=True):
        corp.choose(eng, m["slug"], code, item, "ip", shipping=SHIP, consent=True, at=IN)
    s0 = settle.summary(eng, mid)
    assert s0["revenue"] is None and s0["margin"] is None and s0["orders"] == 4
    settle.set_contract(eng, mid, {"unit_price": 55000, "headcount": 4, "vat_mode": "included", "basis": "headcount"})
    s1 = settle.summary(eng, mid)
    assert s1["revenue"] == {"count": 4, "supply": 200000, "vat": 20000, "total": 220000}
    # 아직 발주서 없음: A 3개 추정(30000×3=90000, 부가세 별도라 공급가액 그대로), B 1개 단가 없음
    assert (
        s1["cost"]["estimate_supply"] == 90000
        and s1["cost"]["estimate_unknown_qty"] == 1
        and not s1["cost"]["complete"]
    )
    assert s1["margin"]["amount"] == 110000 and not s1["margin"]["final"]
    po.create_batch(eng, mid, by="t")  # A 는 발주서(정식 거래처), B 는 이름만 — 둘 다 묶임
    s2 = settle.summary(eng, mid)
    assert s2["cost"]["po_supply"] == 90000 and s2["cost"]["po_unknown"] == 1 and s2["cost"]["estimate"] == []
    assert not s2["margin"]["final"]  # B 발주서 단가 확인 필요
    assert s2["cost"]["po_open"] == 1  # B 는 이름만 → 미확정 발주서
    pos = {p["status"]: p["po_no"] for p in s2["cost"]["po"]}
    with pytest.raises(corp.MallError, match="미확정"):  # 미확정 발주서엔 매입 세금계산서 표시 안 됨
        settle.set_po_invoice(eng, mid, pos["draft"], received_on="2026-12-20")
    settle.set_po_invoice(eng, mid, pos["issued"], received_on="2026-12-20")
    s3 = settle.summary(eng, mid)
    assert s3["invoices"]["purchase_received"] == 1 and s3["invoices"]["purchase_total"] == 2
    settle.set_contract(eng, mid, {"basis": "orders", "invoice_issued_on": "2026-12-21"})
    s4 = settle.summary(eng, mid)
    assert s4["revenue"]["count"] == 4 and s4["invoices"]["sales_issued_on"] == "2026-12-21"
    assert s4["contract"]["unit_price"] == 55000  # 안 보낸 값은 그대로
    with pytest.raises(corp.MallError, match="날짜"):
        settle.set_contract(eng, mid, {"invoice_issued_on": "어제"})
    row = next(r for r in settle.overview(eng) if r["mall_id"] == mid)
    assert row["revenue"]["supply"] == 200000 and row["cost_supply"] == 90000 and not row["cost_complete"]


def test_settlement_complete_margin_is_final(eng):
    m, codes = _settle_mall(eng, f"st2f-{os.urandom(2).hex()}")
    corp.choose(eng, m["slug"], codes[0][1], "A", "ip", shipping=SHIP, consent=True, at=IN)
    settle.set_contract(eng, m["mall_id"], {"unit_price": 44000, "headcount": 1, "vat_mode": "excluded"})
    po.create_batch(eng, m["mall_id"], by="t")
    s = settle.summary(eng, m["mall_id"])
    assert (
        s["revenue"]["supply"] == 44000
        and s["cost"]["complete"]
        and s["margin"] == {"amount": 14000, "rate": 0.3182, "final": True}
    )


def test_routes(eng):
    from app.main import app

    cl = TestClient(app)
    ieng, iid = _won_inquiry()
    inq.set_status(ieng, iid, "won", by="op")
    assert cl.get(f"/admin/api/b2b-inquiry/{iid}/candidates").status_code == 401
    assert len(cl.get(f"/admin/api/b2b-inquiry/{iid}/candidates", headers=H).json()["candidates"]) == 2
    slug = f"st2r-{os.urandom(2).hex()}"
    r = cl.post(
        f"/admin/api/b2b-inquiry/{iid}/mall-draft",
        headers=H,
        json={
            "slug": slug,
            "opens_at": "2027-01-05T09:00",
            "closes_at": "2027-01-12T18:00",
            "candidate_ids": ["cand-hangwa-01"],
        },
    )
    mid = r.json()["mall"]["mall_id"]
    assert cl.get(f"/admin/api/corpmall/{mid}/settle", headers=H).json()["revenue"]["total"] == 165000
    assert cl.post(f"/admin/api/corpmall/{mid}/contract", headers=H, json={"unit_price": 50000, "headcount": 3}).json()[
        "ok"
    ]
    assert cl.get("/admin/api/b2b-settle", headers=H).status_code == 200
    assert (
        cl.post(
            f"/admin/api/corpmall/{mid}/pos/NOPE/invoice", headers=H, json={"received_on": "2026-12-01"}
        ).status_code
        == 400
    )
    assert cl.get("/admin/b2b/settle", headers=H).status_code in (200, 302, 303, 307)


def test_settlement_tax_exempt_revenue(eng):
    """매출 과세·면세 구분 (검토 반영 — 세무 검토 뒤 확정)."""
    m, codes = _settle_mall(eng, f"st2x-{os.urandom(2).hex()}")
    corp.choose(eng, m["slug"], codes[0][1], "A", "ip", shipping=SHIP, consent=True, at=IN)
    settle.set_contract(
        eng, m["mall_id"], {"unit_price": 33000, "headcount": 2, "vat_mode": "included", "tax_type": "exempt"}
    )
    assert settle.summary(eng, m["mall_id"])["revenue"] == {"count": 2, "supply": 66000, "vat": 0, "total": 66000}
    with pytest.raises(corp.MallError, match="과세 구분"):
        settle.set_contract(eng, m["mall_id"], {"tax_type": "zero"})
