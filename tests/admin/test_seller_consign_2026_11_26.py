"""정식 위탁판매 셀러 (2026-11-26) — 입점 심사표(운영자만)·상품 공급사 규칙·소매몰 공급사 금지·운영 지표·배송 예외 문의."""

from __future__ import annotations

import os
from datetime import datetime, timezone

import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient

os.environ.setdefault("CORPMALL_KEY", Fernet.generate_key().decode())

from app.services.corpmall import store as corp  # noqa: E402
from app.services.seller import chat as SC  # noqa: E402
from app.services.seller import consign as CG  # noqa: E402
from app.services.seller import products as prod  # noqa: E402
from app.services.seller import scm  # noqa: E402
from app.services.seller import store as sel  # noqa: E402

IP = "1.1.1.1"
H = {"X-Access-Token": "test-token"}
CSV = "판매처 주문번호,상품 번호,수량,받는 분,휴대폰,우편번호,주소,배송 메모,주문일\n"


@pytest.fixture
def eng():
    corp.reset_limits()
    e = CG.engine()
    with e.begin() as c:
        for t in (CG.t_check, scm.t_order, scm.t_batch, scm.t_supply, scm.t_supplier, scm.t_stock, prod.t_listing,
                  prod.t_product, sel.t_event, sel.t_key, sel.t_seller):  # fmt: skip
            c.execute(t.delete())
    return e


def _consign(eng, name="나수산"):
    s = sel.create_seller(eng, name=name, kind="consign", contact={"name": "김", "email": "k@a.kr"}, by="operator")
    return s["seller_id"], sel.issue_key(eng, s["seller_id"], by="operator")["code"]


def test_checklist_gates_activation_operator_only(eng):
    sid, k = _consign(eng)
    with pytest.raises(sel.SellerError, match="심사표"):
        sel.set_status(eng, sid, "active", by="operator", reason="서류 확인")
    cl = CG.checklist(eng, sid)
    assert not cl["ready"] and len(cl["items"]) == 6 and "공급사 등록" in cl["missing"]
    for who in ("ai", "seller", "ai:cs_domain"):
        with pytest.raises(sel.SellerError, match="운영자만"):
            CG.set_check(eng, sid, "supplier_contract", True, by=who, note="봤음")
    with pytest.raises(sel.SellerError, match="메모"):
        CG.set_check(eng, sid, "supplier_contract", True, by="operator")
    with pytest.raises(sel.SellerError, match="운영자가 확인하는"):
        CG.set_check(eng, sid, "supplier_registered", True, by="operator", note="x")  # 자동 항목
    for item in CG.ITEMS:
        if item not in CG.AUTO:
            CG.set_check(eng, sid, item, True, by="operator", note="계약서 2026-11-26 확인")
    assert CG.checklist(eng, sid)["missing"] == ["공급사 등록"]
    with pytest.raises(sel.SellerError, match="소매몰"):
        scm.save_supplier(eng, k, IP, name="쿠팡 로켓배송", contact=None)  # 차익거래 금지
    with pytest.raises(sel.SellerError, match="소매몰"):
        scm.save_supplier(eng, k, IP, name="네이버 스마트스토어 OO", contact=None)
    scm.save_supplier(eng, k, IP, name="완도수협 공판장", contact=None)
    assert CG.checklist(eng, sid)["ready"]
    sel.set_status(eng, sid, "active", by="operator", reason="심사표 확인")
    # 직접 재고 셀러는 심사표 없이
    d = sel.create_seller(eng, name="가농장", kind="direct", contact={"name": "이", "email": "l@a.kr"}, by="operator")
    sel.set_status(eng, d["seller_id"], "active", by="operator", reason="ok")
    with pytest.raises(sel.SellerError, match="위탁판매 셀러만"):
        CG.set_check(eng, d["seller_id"], "supplier_contract", True, by="operator", note="x")


def _active(eng):
    sid, k = _consign(eng)
    sup = scm.save_supplier(eng, k, IP, name="완도수협", contact=None)["supplier_id"]
    for item in CG.ITEMS:
        if item not in CG.AUTO:
            CG.set_check(eng, sid, item, True, by="operator", note="확인")
    sel.set_status(eng, sid, "active", by="operator", reason="ok")
    k = sel.issue_key(eng, sid, by="operator")["code"]
    return sid, k, sup


def test_consign_product_needs_supplier_to_be_approved(eng):
    sid, k, sup = _active(eng)
    pid = prod.save(eng, k, IP, {"name": "완도 전복 1kg", "volume": "1kg", "price": "39000"})["product_id"]
    with pytest.raises(sel.SellerError, match="공급사"):
        prod.review(eng, pid, "approved", by="operator")
    scm.set_supply(eng, k, IP, pid, supplier_id=sup, sku="AB-1")
    assert prod.review(eng, pid, "approved", by="operator")["status"] == "approved"


def test_metrics_watch_then_levels(eng):
    sid, k, sup = _active(eng)
    pid = prod.save(eng, k, IP, {"name": "완도 전복 1kg", "volume": "1kg", "price": "39000"})["product_id"]
    scm.set_supply(eng, k, IP, pid, supplier_id=sup)
    at = datetime(2026, 11, 26, 9, tzinfo=timezone.utc)
    lines = "".join(
        f"N{i},{pid},1,홍길동,010-1234-5678,04524,서울 중구 세종대로 110,,2026-11-{10 + i % 10:02d}\n"
        for i in range(32)
    )
    assert scm.import_orders(eng, k, IP, CSV + lines, entrust_ok=True)["ok"]
    m = CG.metrics(eng, sid, at=at)
    assert m["orders"] == 32 and m["shipped"] == 0 and m["late"] >= 20 and m["level"] == "bad"
    assert m["by_supplier"][0]["supplier"] == "완도수협" and m["by_supplier"][0]["late"] == m["late"]
    few = CG.metrics(eng, sid, at=at) | {}
    CG.MIN_ORDERS, old = 100, CG.MIN_ORDERS
    try:
        assert CG.metrics(eng, sid, at=at)["level"] == "watch"
    finally:
        CG.MIN_ORDERS = old
    assert few["waiting"] == 32
    assert "홍길동" not in str(CG.board(eng, at=at))  # 받는 분 정보 없음


def test_ship_issue_chat_topic():
    assert SC.classify("공급사가 오배송을 했어요 어떻게 하죠") == "ship_issue"
    assert SC.classify("택배 분실 신고") == "ship_issue"
    assert SC.classify("발주서 엑셀은 어디서 받나요") == "orders"
    assert SC.classify("이용료 환불 요청") == "fee"
    r = SC.respond("파손돼서 손님이 반품 원해요")
    assert r.topic == "ship_issue" and r.ticket_domain is None and r.offer_handoff and "공급사" in r.answer
    r2 = SC.respond("파손 건 손님이 보상 안 해주면 소비자원에 신고한대요")
    assert r2.ticket_domain == "seller_ship"
    from app.services.cs import tickets

    assert tickets.SPEC["seller_ship"]["human"] is True


def test_admin_routes(eng):
    from app.main import app

    sid, k = _consign(eng)
    c = TestClient(app)
    j = c.get("/admin/api/seller-consign", headers=H).json()
    row = next(x for x in j["sellers"] if x["seller_id"] == sid)
    assert row["ready"] is False and len(j["items"]) == 6
    r = c.post(
        f"/admin/api/seller-consign/{sid}/check",
        headers=H,
        json={"item": "return_policy", "ok": True, "note": "반품지 확인"},
    )
    assert r.json()["ok"] and any(i["item"] == "return_policy" and i["ok"] for i in r.json()["items"])
    assert c.post(f"/admin/api/seller-consign/{sid}/check", json={"item": "return_policy", "ok": True}).status_code in (
        401,
        403,
    )
    assert c.post("/seller/api/orders", json={"key": k}).json()["metrics"]["level"] == "watch"
    assert 'id="cg-h"' in c.get("/admin/seller", headers=H).text
