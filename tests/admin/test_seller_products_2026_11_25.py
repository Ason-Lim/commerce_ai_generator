"""셀러 상품 등록·검수 ② (창 5, 2026-11-25) — 판매자 표기/확인됨 분리 · 검수 · 격리 · 운영자만 · 노출 없음."""

from __future__ import annotations

import os
import re
from pathlib import Path

import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient

os.environ.setdefault("CORPMALL_KEY", Fernet.generate_key().decode())

from app.services.corpmall import store as corp  # noqa: E402
from app.services.seller import products as prod  # noqa: E402
from app.services.seller import store as sel  # noqa: E402

H = {"X-Access-Token": "test-token"}
CT = {"name": "김담당", "email": "kim@farm.kr"}
IP = "1.1.1.1"
TANGERINE = {"name": "제주 감귤 5kg", "volume": "5kg", "price": "23,900", "ship_fee": "0",
             "origin": "제주", "cert": "GAP", "brix": "12", "sale_url": "https://smartstore.naver.com/x/products/1"}  # fmt: skip


@pytest.fixture
def eng():
    corp.reset_limits()
    e = prod.engine()
    with e.begin() as c:
        for t in (prod.t_product, sel.t_event, sel.t_key, sel.t_seller):
            c.execute(t.delete())
    return e


@pytest.fixture
def client():
    from app.main import app

    return TestClient(app)


def _seller(eng, name="가농장", active=True):
    s = sel.create_seller(eng, name=name, kind="direct", contact=CT, by="operator")
    if active:
        sel.set_status(eng, s["seller_id"], "active", by="operator", reason="서류 확인")
    return s, sel.issue_key(eng, s["seller_id"], by="operator")["code"]


# ── 등록 · 신고값/확인값 ──
def test_new_product_is_pending_with_seller_declared_facts(eng):
    _, k = _seller(eng)
    p = prod.save(eng, k, IP, TANGERINE)
    assert p["status"] == "pending" and p["price"] == 23900 and p["ship_fee"] == 0
    assert {f["key"]: f["source"] for f in p["facts"]} == {"origin": "seller", "cert": "seller", "brix": "seller"}
    assert all(f["source_label"] == "판매자 표기" for f in p["facts"])


def test_verify_needs_note_and_marks_only_that_field(eng):
    _, k = _seller(eng)
    p = prod.save(eng, k, IP, TANGERINE)
    with pytest.raises(sel.SellerError, match="근거"):
        prod.verify(eng, p["product_id"], "origin", "제주", by="operator", note="")
    prod.verify(eng, p["product_id"], "origin", "제주", by="operator", note="원산지 증명서 사본")
    mine = prod.list_mine(eng, k, IP)[0]
    src = {f["key"]: f["source_label"] for f in mine["facts"]}
    assert src == {"origin": "확인됨", "cert": "판매자 표기", "brix": "판매자 표기"}
    assert "verified" not in mine  # 셀러에게는 확인자·근거 원문 안 보냄


def test_verified_value_differing_from_declared_is_flagged(eng):
    _, k = _seller(eng)
    p = prod.save(eng, k, IP, TANGERINE)
    got = prod.verify(eng, p["product_id"], "brix", "10.5", by="operator", note="당도 측정 사진")
    f = next(x for x in got["facts"] if x["key"] == "brix")
    assert f["value"] == 10.5 and f["source"] == "verified" and f["differs"] is True


def test_editing_declared_value_drops_its_verification_and_returns_to_pending(eng):
    s, k = _seller(eng)
    p = prod.save(eng, k, IP, TANGERINE)
    pid = p["product_id"]
    prod.verify(eng, pid, "origin", "제주", by="operator", note="증명서")
    prod.verify(eng, pid, "cert", "GAP", by="operator", note="인증서")
    prod.review(eng, pid, "approved", by="operator")
    got = prod.save(eng, k, IP, {**TANGERINE, "origin": "전남 고흥"}, pid)
    assert got["status"] == "pending"
    src = {f["key"]: f["source"] for f in got["facts"]}
    assert src["origin"] == "seller" and src["cert"] == "verified"  # 바뀐 칸만 확인 지움


def test_unknown_fields_and_bad_values_rejected(eng):
    _, k = _seller(eng)
    with pytest.raises(sel.SellerError, match="받지 않는 칸"):
        prod.save(eng, k, IP, {**TANGERINE, "score": 99})
    with pytest.raises(sel.SellerError, match="https"):
        prod.save(eng, k, IP, {**TANGERINE, "sale_url": "javascript:alert(1)"})
    with pytest.raises(sel.SellerError, match="당도"):
        prod.save(eng, k, IP, {**TANGERINE, "brix": "99"})
    with pytest.raises(sel.SellerError, match="가격"):
        prod.save(eng, k, IP, {**TANGERINE, "price": ""})


# ── CSV ──
def test_csv_all_or_nothing_with_line_errors(eng):
    _, k = _seller(eng)
    bad = prod.csv_template() + "사과 3kg,3kg,abc,,경북,,,\n"
    got = prod.import_csv(eng, k, IP, bad)
    assert got["ok"] is False and got["errors"][0]["line"] == 3 and prod.list_mine(eng, k, IP) == []
    good = prod.csv_template() + "사과 3kg,3kg,19900,,경북,,,\n"
    got = prod.import_csv(eng, k, IP, "﻿" + good)
    assert got == {"ok": True, "added": 2, "errors": []}
    assert all(p["status"] == "pending" for p in prod.list_mine(eng, k, IP))


def test_csv_unknown_header_rejected(eng):
    _, k = _seller(eng)
    with pytest.raises(sel.SellerError, match="모르는 칸"):
        prod.import_csv(eng, k, IP, "상품명,가격,순위가점\n감귤,1000,5\n")


# ── 격리 ──
def test_isolation_between_sellers(eng):
    _, ka = _seller(eng, "가농장")
    _, kb = _seller(eng, "나수산")
    pa = prod.save(eng, ka, IP, TANGERINE)
    assert prod.list_mine(eng, kb, IP) == []
    with pytest.raises(sel.SellerError, match="없는 상품"):
        prod.save(eng, kb, IP, {**TANGERINE, "price": 100}, pa["product_id"])
    with pytest.raises(sel.SellerError, match="없는 상품"):
        prod.withdraw(eng, kb, IP, pa["product_id"])
    assert prod.list_mine(eng, ka, IP)[0]["price"] == 23900


def test_seller_product_api_takes_no_seller_id(client, eng):
    s, k = _seller(eng)
    r = client.post("/seller/api/products", json={"key": k, "seller_id": s["seller_id"]})
    assert r.status_code == 422
    f = {k2: v for k2, v in TANGERINE.items()}
    r = client.post("/seller/api/products/save", json={"key": k, "fields": {**f, "status": "approved"}})
    assert r.status_code == 422  # 셀러가 상태를 넣을 수 없음
    r = client.post("/seller/api/products/save", json={"key": k, "fields": f})
    assert r.json()["product"]["status"] == "pending"


# ── 사람만 ──
@pytest.mark.parametrize("who", ["ai", "ai:seller_review", "system:auto", "seller", None])
def test_only_operator_reviews_and_verifies(eng, who):
    _, k = _seller(eng)
    p = prod.save(eng, k, IP, TANGERINE)
    with pytest.raises(sel.SellerError, match="운영자만"):
        prod.review(eng, p["product_id"], "approved", by=who)
    with pytest.raises(sel.SellerError, match="운영자만"):
        prod.verify(eng, p["product_id"], "origin", "제주", by=who, note="증명서")
    assert prod.list_mine(eng, k, IP)[0]["status"] == "pending"


def test_review_rules(eng):
    s, k = _seller(eng, active=False)
    p = prod.save(eng, k, IP, TANGERINE)
    with pytest.raises(sel.SellerError, match="입점 승인 전"):
        prod.review(eng, p["product_id"], "approved", by="operator")
    with pytest.raises(sel.SellerError, match="반려 이유"):
        prod.review(eng, p["product_id"], "rejected", by="operator")
    got = prod.review(eng, p["product_id"], "rejected", by="operator", note="원산지 서류가 필요해요")
    assert got["status"] == "rejected"
    assert prod.list_mine(eng, k, IP)[0]["review_note"] == "원산지 서류가 필요해요"
    off = prod.withdraw(eng, k, IP, p["product_id"])  # 판매 끄기(2026-11-25) — 검수 상태는 그대로
    assert off["status"] == "rejected" and off["on"] is False


def test_admin_api_queue_verify_review(client, eng):
    s, k = _seller(eng)
    p = prod.save(eng, k, IP, TANGERINE)
    q = client.get("/admin/api/seller-products", headers=H).json()["products"]
    assert [x["product_id"] for x in q] == [p["product_id"]] and q[0]["seller_name"] == "가농장"
    r = client.post(f"/admin/api/seller-products/{p['product_id']}/verify", headers=H,
                    json={"key": "origin", "value": "제주", "note": "증명서"})  # fmt: skip
    assert r.json()["product"]["verified"]["origin"]["value"] == "제주"
    r = client.post(f"/admin/api/seller-products/{p['product_id']}/review", headers=H, json={"decision": "approved"})
    assert r.json()["product"]["status"] == "approved"
    assert client.get("/admin/api/seller-products", headers=H).json()["products"] == []
    assert client.get("/admin/api/seller-products").status_code in (401, 403)
    assert client.get("/admin/seller", follow_redirects=False).status_code == 303


# ── 노출 없음 (결정 2) ──
ALLOWED_IMPORTERS = {"app/services/seller", "app/api/seller_routes.py", "app/admin/routes.py",
                     "app/services/privacy/retention.py"}  # fmt: skip


def test_seller_data_not_wired_into_customer_or_recommendation_paths():
    root = Path(__file__).resolve().parents[2]
    hits = []
    for f in (root / "app").rglob("*.py"):
        rel = f.relative_to(root).as_posix()
        if any(rel == a or rel.startswith(a + "/") for a in ALLOWED_IMPORTERS):
            continue
        if re.search(r"services\.seller\b|services import seller\b", f.read_text(encoding="utf-8")):
            hits.append(rel)
    assert hits == [], f"셀러 데이터를 쓰는 곳은 순위 변경 승인 절차 뒤에만: {hits}"


def test_admin_tabs_have_seller_link():
    root = Path(__file__).resolve().parents[2] / "app" / "admin"
    pages = [p for p in root.rglob("*.html") if 'aria-label="관리자 탭"' in p.read_text(encoding="utf-8")]
    assert pages and all('href="/admin/seller"' in p.read_text(encoding="utf-8") for p in pages)
