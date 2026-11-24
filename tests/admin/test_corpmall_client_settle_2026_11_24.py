"""발주처 정산 화면 (2026-11-24) — 담당자 화면의 청구 인원·금액·세금계산서·확인. 매입·마진은 보이지 않는다."""

from __future__ import annotations

import os
from datetime import datetime

import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient

os.environ.setdefault("CORPMALL_KEY", Fernet.generate_key().decode())

from app.services.corpmall import manager, po, settle, suppliers  # noqa: E402
from app.services.corpmall import store as corp  # noqa: E402

KST = corp.KST
IN = datetime(2026, 12, 3, 10, 0, tzinfo=KST)
SHIP = {"name": "홍길동", "phone": "010-1234-5678", "zipcode": "04524", "address": "서울 중구 세종대로 110", "memo": ""}
H = {"X-Access-Token": "test-token"}


@pytest.fixture
def eng(tmp_path, monkeypatch):
    monkeypatch.setenv("CS_DIR", str(tmp_path / "cs"))
    monkeypatch.setenv("OPERATOR_NOTIFY", "off")
    corp.reset_limits()
    return corp.engine()


def _setup(eng, slug, n=4, chosen=3):
    m = corp.create_mall(
        eng,
        {
            "slug": slug,
            "client": "샘플공사",
            "title": "설 선물",
            "opens_at": "2026-12-01T09:00",
            "closes_at": "2026-12-10T18:00",
            "delivery_mode": "bulk",
            "default_item_id": "A",
            "items": [{"id": "A", "name": "한과"}, {"id": "B", "name": "감귤"}],
        },
    )
    corp.set_status(eng, m["mall_id"], "open")
    codes = corp.issue_codes(eng, m["mall_id"], n)
    for _, code, _ in codes[:chosen]:
        corp.choose(eng, slug, code, "B", "ip", at=IN)
    s = suppliers.save(eng, {"name": f"비밀공급-{slug}", "contact": {"email": "s@x.example"}})
    po.set_suppliers(eng, m["mall_id"], {"B": {"supplier_id": s["supplier_id"], "unit_cost": 12345}})
    key = manager.issue(eng, m["mall_id"], "총무팀")["link"].split("#k=")[1]
    return m, key


def test_statement_hides_cost_and_is_estimate_before_close(eng):
    slug = f"cs-a-{os.urandom(2).hex()}"
    m, key = _setup(eng, slug)
    v = manager.view(eng, slug, key, "ip")
    assert v["settle"]["ready"] is False and v["settle"]["can_confirm"] is False
    settle.set_contract(
        eng, m["mall_id"], {"unit_price": 55000, "headcount": 4, "vat_mode": "included", "basis": "headcount"}
    )
    st = manager.view(eng, slug, key, "ip")["settle"]
    assert st["stage"] == "estimate" and not st["can_confirm"]
    assert st["bill"] == {
        "basis": "headcount", "unit_price": 55000, "vat_mode": "included", "tax_type": "taxable",
        "count": 4, "supply": 200000, "vat": 20000, "total": 220000,
    }  # fmt: skip
    assert st["actual"] == {"issued": 4, "void": 0, "chosen": 3, "defaulted": 0, "orders": 3}
    text = repr(v) + repr(st)
    for secret in ("12345", "비밀공급", "margin", "cost", "unit_cost", "supplier"):
        assert secret not in text  # 매입·마진·공급사는 발주처에게 안 보임
    with pytest.raises(corp.MallError, match="마감된 뒤"):
        manager.confirm_settle(eng, slug, key, "ip", name="김총무", agree=True, sig=st["sig"])


def test_confirm_after_close_and_reconfirm_when_changed(eng):
    slug = f"cs-b-{os.urandom(2).hex()}"
    m, key = _setup(eng, slug)
    settle.set_contract(
        eng, m["mall_id"], {"unit_price": 50000, "headcount": 4, "vat_mode": "excluded", "basis": "orders"}
    )
    corp.close_mall(eng, m["mall_id"])  # 안 고른 1명은 기본 선물 → 주문 4
    st = manager.view(eng, slug, key, "ip")["settle"]
    assert st["stage"] == "closed" and st["can_confirm"] and st["bill"]["count"] == 4 and st["bill"]["total"] == 220000
    assert st["actual"]["defaulted"] == 1
    with pytest.raises(corp.MallError, match="이름"):
        manager.confirm_settle(eng, slug, key, "ip", name=" ", agree=True, sig=st["sig"])
    with pytest.raises(corp.MallError, match="확인했다는 표시"):
        manager.confirm_settle(eng, slug, key, "ip", name="김총무", agree=False, sig=st["sig"])
    with pytest.raises(corp.MallError, match="바뀌었어요"):  # 화면에서 본 금액과 다르면 거부
        manager.confirm_settle(eng, slug, key, "ip", name="김총무", agree=True, sig="0" * 16)
    got = manager.confirm_settle(eng, slug, key, "ip", name="김총무", agree=True, sig=st["sig"])
    assert got["confirm"]["valid"] and got["confirm"]["by"] == "총무팀 · 김총무" and not got["can_confirm"]
    with pytest.raises(corp.MallError, match="이미 확인"):
        manager.confirm_settle(eng, slug, key, "ip", name="김총무", agree=True, sig=st["sig"])
    adm = settle.summary(eng, m["mall_id"])["client_confirm"]
    assert adm["valid"] and adm["total"] == 220000
    # 운영자가 계약값을 바꾸면 다시 확인 필요
    settle.set_contract(eng, m["mall_id"], {"unit_price": 52000})
    st2 = manager.view(eng, slug, key, "ip")["settle"]
    assert st2["confirm"]["valid"] is False and st2["can_confirm"] and st2["bill"]["total"] == 228800
    assert settle.summary(eng, m["mall_id"])["client_confirm"]["valid"] is False
    again = manager.confirm_settle(eng, slug, key, "ip", name="김총무", agree=True, sig=st2["sig"])
    assert again["confirm"]["valid"] and again["confirm"]["total"] == 228800
    mm = corp.get_mall(eng, mall_id=m["mall_id"])
    assert len(mm["client_confirm_history"]) == 2 and mm["contract"]["unit_price"] == 52000  # 계약값 보존
    assert any(e["kind"] == "client_settle_confirm" for e in corp.events(eng, m["mall_id"]))


def test_settle_request_needs_memo(eng):
    slug = f"cs-c-{os.urandom(2).hex()}"
    m, key = _setup(eng, slug)
    with pytest.raises(corp.MallError, match="정산에서"):
        manager.request(eng, slug, key, "ip", "settle", text="")
    got = manager.request(eng, slug, key, "ip", "settle", text="인원 3명 빠짐 확인 부탁 010-1111-2222")
    summ = got["requests"][-1]["summary"]
    assert "정산 문의" in summ and "2222" not in summ


def test_routes(eng):
    from app.main import app

    cl = TestClient(app)
    slug = f"cs-r-{os.urandom(2).hex()}"
    m, key = _setup(eng, slug)
    assert cl.post(
        f"/admin/api/corpmall/{m['mall_id']}/contract",
        headers=H,
        json={"unit_price": 30000, "headcount": 4, "vat_mode": "included", "basis": "headcount", "tax_type": "exempt"},
    ).json()["ok"]
    corp.close_mall(eng, m["mall_id"])
    v = cl.post(f"/corp/api/{slug}/manager/view", json={"key": key}).json()
    st = v["settle"]
    assert st["bill"]["vat"] == 0 and st["contract"]["tax_label"] == "면세" and "_sig" not in st
    bad = cl.post(
        f"/corp/api/{slug}/manager/settle-confirm", json={"key": "nope", "name": "a", "agree": True, "sig": st["sig"]}
    )
    assert bad.status_code == 400
    ok = cl.post(
        f"/corp/api/{slug}/manager/settle-confirm", json={"key": key, "name": "김총무", "agree": True, "sig": st["sig"]}
    )
    assert ok.json()["ok"] and ok.json()["settle"]["confirm"]["valid"]
    adm = cl.get(f"/admin/api/corpmall/{m['mall_id']}/settle", headers=H).json()
    assert adm["client_confirm"]["valid"]
