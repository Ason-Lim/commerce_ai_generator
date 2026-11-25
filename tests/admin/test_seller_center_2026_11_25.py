"""셀러 센터 ① (창 5, 2026-11-25) — 초대 코드 입장 · 셀러 간 격리 · 운영자만 상태 변경 · 연락처 암호화·1년 파기."""

from __future__ import annotations

import os
from datetime import timedelta

import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient

os.environ.setdefault("CORPMALL_KEY", Fernet.generate_key().decode())

from app.services.corpmall import store as corp  # noqa: E402
from app.services.seller import store as sel  # noqa: E402

H = {"X-Access-Token": "test-token"}
CT_A = {"name": "김담당", "email": "kim@farm-a.kr", "phone": "010-1111-2222"}
CT_B = {"name": "이담당", "email": "lee@farm-b.kr", "phone": ""}


@pytest.fixture
def eng():
    corp.reset_limits()
    e = sel.engine()
    with e.begin() as c:  # 시험마다 셀러 표 비우기 (같은 임시 DB 를 나눠 씀)
        for t in (sel.t_event, sel.t_key, sel.t_seller):
            c.execute(t.delete())
    return e


@pytest.fixture
def client():
    from app.main import app

    return TestClient(app)


def _two(eng):
    a = sel.create_seller(eng, name="가농장", kind="direct", contact=CT_A, by="operator")
    b = sel.create_seller(eng, name="나수산", kind="consign", contact=CT_B, by="operator")
    ka = sel.issue_key(eng, a["seller_id"], by="operator")["code"]
    kb = sel.issue_key(eng, b["seller_id"], by="operator")["code"]
    return a, b, ka, kb


# ── 입장 ──
def test_code_enters_own_seller_and_contact_is_masked(eng):
    a, _, ka, _ = _two(eng)
    me = sel.me(eng, ka, "1.1.1.1")
    assert me["name"] == "가농장" and me["status"] == "invited"
    assert "seller_id" not in me
    assert me["contact"]["email"].startswith("ki***@") and me["contact"]["phone"] == "***-2222"
    assert "010-1111" not in str(me)


def test_contact_is_encrypted_at_rest(eng):
    a, *_ = _two(eng)
    with eng.connect() as c:
        raw = c.execute(sel.t_seller.select().where(sel.t_seller.c.seller_id == a["seller_id"])).mappings().first()
    assert "kim@farm-a.kr" not in (raw["contact_enc"] or "") and "010-1111" not in (raw["contact_enc"] or "")
    with eng.connect() as c:
        keys = c.execute(sel.t_key.select()).mappings().all()
    assert all(len(k["token_hash"]) == 64 for k in keys)  # 원문 없음


def test_reissue_blocks_old_code(eng):
    a, _, ka, _ = _two(eng)
    new = sel.issue_key(eng, a["seller_id"], by="operator")
    assert new["revoked_old"] == 1 and new["link"] == f"/seller#k={new['code']}"
    with pytest.raises(sel.SellerError):
        sel.me(eng, ka, "1.1.1.1")
    assert sel.me(eng, new["code"], "1.1.1.1")["name"] == "가농장"


def test_wrong_codes_are_rate_limited(eng):
    _, _, ka, _ = _two(eng)
    for _ in range(corp.MAX_FAILS):
        with pytest.raises(sel.SellerError):
            sel.me(eng, "x" * 24, "9.9.9.9")
    with pytest.raises(sel.SellerError, match="잠시 막았어요"):
        sel.me(eng, ka, "9.9.9.9")  # 맞는 코드도 그 주소에선 잠시 막힘
    assert sel.me(eng, ka, "8.8.8.8")["name"] == "가농장"  # 다른 주소는 그대로


# ── 셀러 간 격리 ──
def test_isolation_each_code_sees_and_changes_only_its_seller(eng):
    a, b, ka, kb = _two(eng)
    assert sel.me(eng, kb, "1.1.1.1")["name"] == "나수산"
    sel.update_contact(eng, ka, "1.1.1.1", {"name": "박새담당", "email": "park@farm-a.kr"})
    da, db = sel.detail(eng, a["seller_id"]), sel.detail(eng, b["seller_id"])
    assert da["contact"]["email"] == "park@farm-a.kr"
    assert db["contact"] == CT_B  # B 는 그대로


def test_seller_api_takes_no_seller_id(client, eng):
    a, b, ka, _ = _two(eng)
    r = client.post("/seller/api/me", json={"key": ka, "seller_id": b["seller_id"]})
    assert r.status_code == 422  # 모르는 칸 거부 — 셀러 번호를 넣어 볼 수 없음
    r = client.post("/seller/api/contact", json={"key": ka, "seller_id": b["seller_id"], "contact": CT_A})
    assert r.status_code == 422
    r = client.post("/seller/api/me", json={"key": ka})
    assert r.json()["seller"]["name"] == "가농장"


def test_contact_rejects_unknown_fields(eng):
    _, _, ka, _ = _two(eng)
    with pytest.raises(sel.SellerError, match="받지 않는 칸"):
        sel.update_contact(eng, ka, "1.1.1.1", {"name": "김", "email": "a@b.kr", "account": "123-45"})
    with pytest.raises(sel.SellerError, match="하나는"):
        sel.update_contact(eng, ka, "1.1.1.1", {"name": "김"})


# ── 사람이 정하는 것 ──
@pytest.mark.parametrize("who", ["ai", "ai:cs_domain", "system:retention", "seller", "", None, "operatorx"])
def test_only_operator_changes_status_or_issues_codes(eng, who):
    a, *_ = _two(eng)
    with pytest.raises(sel.SellerError, match="운영자만"):
        sel.set_status(eng, a["seller_id"], "active", by=who, reason="심사 통과")
    with pytest.raises(sel.SellerError, match="운영자만"):
        sel.issue_key(eng, a["seller_id"], by=who)
    with pytest.raises(sel.SellerError, match="운영자만"):
        sel.create_seller(eng, name="다", kind="direct", contact=CT_A, by=who)
    assert sel.detail(eng, a["seller_id"])["status"] == "invited"


def test_status_flow_needs_reason_and_blocks_entry(eng):
    a, _, ka, _ = _two(eng)
    with pytest.raises(sel.SellerError, match="이유"):
        sel.set_status(eng, a["seller_id"], "active", by="operator", reason=" ")
    sel.set_status(eng, a["seller_id"], "active", by="operator", reason="서류 확인")
    assert sel.me(eng, ka, "1.1.1.1")["status"] == "active"
    sel.set_status(eng, a["seller_id"], "suspended", by="operator", reason="배송 지연")
    with pytest.raises(sel.SellerError):
        sel.me(eng, ka, "1.1.1.1")  # 정지하면 코드도 막힘
    with pytest.raises(sel.SellerError):
        sel.issue_key(eng, a["seller_id"], by="operator")
    sel.set_status(eng, a["seller_id"], "ended", by="operator", reason="계약 종료")
    with pytest.raises(sel.SellerError, match="바꿀 수 없어요"):
        sel.set_status(eng, a["seller_id"], "active", by="operator", reason="다시")
    kinds = [e["kind"] for e in sel.events(eng, a["seller_id"])]
    assert kinds.count("status") == 3


def test_seller_side_has_no_status_route(client):
    from app.main import app

    seller_paths = {r.path for r in app.routes if getattr(r, "path", "").startswith("/seller")}
    assert seller_paths == {"/seller", "/seller/api/me", "/seller/api/contact"}


# ── 보존 ──
def test_contact_purged_one_year_after_contract_end(eng):
    a, b, *_ = _two(eng)
    sel.set_status(eng, a["seller_id"], "ended", by="operator", reason="계약 종료")
    end = sel.detail(eng, a["seller_id"])["ended_at"]
    from datetime import datetime

    t0 = datetime.fromisoformat(end)
    assert sel.purge(eng, t0 + timedelta(days=364)) == 0
    assert sel.purge(eng, t0 + timedelta(days=366)) == 1
    assert sel.detail(eng, a["seller_id"])["contact"] is None
    assert sel.detail(eng, b["seller_id"])["contact"] == CT_B  # 계약 중인 셀러는 그대로


# ── 관리자 API · 화면 ──
def test_admin_api_flow_and_list_has_no_contact(client, eng):
    r = client.post("/admin/api/seller", headers=H,
                    json={"name": "다과원", "kind": "direct", "contact": CT_A})  # fmt: skip
    sid = r.json()["seller"]["seller_id"]
    lst = client.get("/admin/api/seller", headers=H).json()["sellers"]
    assert lst[0]["contact"] is None and lst[0]["has_contact"] is True
    code = client.post(f"/admin/api/seller/{sid}/key", headers=H).json()["code"]
    assert client.post("/seller/api/me", json={"key": code}).json()["seller"]["name"] == "다과원"
    r = client.post(f"/admin/api/seller/{sid}/status", headers=H, json={"status": "active", "reason": "심사 통과"})
    assert r.json()["seller"]["status"] == "active"
    assert client.post("/admin/api/seller", json={"name": "x", "kind": "direct", "contact": CT_A}).status_code in (
        401,
        403,
    )


def test_page_is_noindex_and_robots_blocks_seller(client):
    r = client.get("/seller")
    assert r.status_code == 200 and "noindex" in r.headers.get("x-robots-tag", "")
    assert 'name="robots" content="noindex' in r.text
    assert "Disallow: /seller" in client.get("/robots.txt").text
