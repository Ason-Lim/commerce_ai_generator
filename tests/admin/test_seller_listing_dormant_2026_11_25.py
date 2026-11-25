"""판매 켜기·끄기(셀러가 정함) · 죽은 셀러몰 찾기 (2026-11-25 사용자 요청)."""

from __future__ import annotations

import os
from datetime import timedelta

import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient

os.environ.setdefault("CORPMALL_KEY", Fernet.generate_key().decode())

from app.services.corpmall import store as corp  # noqa: E402
from app.services.seller import health  # noqa: E402
from app.services.seller import products as prod  # noqa: E402
from app.services.seller import scm  # noqa: E402
from app.services.seller import store as sel  # noqa: E402

H = {"X-Access-Token": "test-token"}
IP = "1.1.1.1"
P = {"name": "제주 감귤 5kg", "volume": "5kg", "price": "23900", "origin": "제주"}


@pytest.fixture
def eng(monkeypatch):
    monkeypatch.setenv("OPERATOR_NOTIFY", "queue")
    corp.reset_limits()
    e = scm.engine()
    with e.begin() as c:
        for t in (scm.t_order, scm.t_batch, scm.t_supply, scm.t_supplier, scm.t_stock, prod.t_listing, prod.t_product,
                  sel.t_event, sel.t_key, sel.t_seller):  # fmt: skip
            c.execute(t.delete())
    return e


def _seller(eng, name="가농장", approve=True):
    s = sel.create_seller(eng, name=name, kind="direct", contact={"name": "김", "email": "k@a.kr"}, by="operator")
    sel.set_status(eng, s["seller_id"], "active", by="operator", reason="ok")
    k = sel.issue_key(eng, s["seller_id"], by="operator")["code"]
    p = prod.save(eng, k, IP, P)
    if approve:
        prod.review(eng, p["product_id"], "approved", by="operator")
    return s, k, p["product_id"]


def _age(eng, seller_id, days):
    """그 셀러의 모든 기록을 days 일 전으로 (시간 흐름 흉내)."""
    from sqlalchemy import update

    with eng.begin() as c:
        rows = c.execute(sel.t_event.select().where(sel.t_event.c.seller_id == seller_id)).mappings().all()
        for r in rows:
            c.execute(update(sel.t_event).where(sel.t_event.c.id == r["id"]).values(at=r["at"] - timedelta(days=days)))
        c.execute(update(sel.t_seller).where(sel.t_seller.c.seller_id == seller_id)
                  .values(created_at=sel.now() - timedelta(days=days)))  # fmt: skip


# ── 판매 켜기·끄기 ──
def test_seller_turns_sale_off_and_on_without_review(eng):
    _, k, pid = _seller(eng)
    p = prod.list_mine(eng, k, IP)[0]
    assert p["sale_state"] == "on_sale" and p["on"] is True
    assert prod.set_listing(eng, k, IP, pid, False) == 1
    p = prod.list_mine(eng, k, IP)[0]
    assert p["sale_state"] == "off" and p["status"] == "approved"  # 검수 결과 그대로
    prod.set_listing(eng, k, IP, pid, True)
    assert prod.list_mine(eng, k, IP)[0]["sale_state"] == "on_sale"  # 다시 켜도 검수 없음
    assert prod.queue(eng, "pending") == []


def test_editing_content_still_needs_review_and_sold_out_shows(eng):
    _, k, pid = _seller(eng)
    scm.set_stock(eng, k, IP, pid, stock=0, sold_out=True, restock_on=None)
    assert prod.list_mine(eng, k, IP)[0]["sale_state"] == "sold_out"
    prod.save(eng, k, IP, {**P, "price": "21900"}, pid)
    assert prod.list_mine(eng, k, IP)[0]["sale_state"] == "pending"


def test_all_off_and_isolation(eng):
    _, ka, pa = _seller(eng, "가농장")
    _, kb, pb = _seller(eng, "나수산")
    prod.save(eng, ka, IP, {**P, "name": "유자청"})
    assert prod.set_listing(eng, ka, IP, None, False) == 2
    assert all(not p["on"] for p in prod.list_mine(eng, ka, IP))
    assert prod.list_mine(eng, kb, IP)[0]["on"] is True  # 남의 상품은 그대로
    with pytest.raises(sel.SellerError, match="없는 상품"):
        prod.set_listing(eng, kb, IP, pa, False)


# ── 죽은 셀러몰 ──
def test_new_seller_is_not_flagged(eng):
    _seller(eng)
    assert health.report(eng)["sellers"] == []


def test_dead_store_needs_no_change_60_and_no_sales_clicks_unmeasured(eng):
    s, k, pid = _seller(eng)
    _age(eng, s["seller_id"], 61)
    rep = health.report(eng)
    row = rep["sellers"][0]
    assert row["level"] == "dead" and row["clicks_30"] is None
    assert any("측정 전" in r for r in row["reasons"]) and row["orders_30"] == 0


def test_watch_between_30_and_60_days(eng):
    s, k, pid = _seller(eng)
    _age(eng, s["seller_id"], 40)
    assert health.report(eng)["sellers"][0]["level"] == "watch"
    assert health.my_health(eng, k, IP)["ask_confirm"] is True


def test_confirm_unchanged_or_sales_keep_store_alive(eng):
    s, k, pid = _seller(eng)
    _age(eng, s["seller_id"], 61)
    health.confirm_unchanged(eng, k, IP)  # 상품은 그대로 — '그대로예요' 한 번
    assert health.report(eng)["sellers"] == []
    assert health.my_health(eng, k, IP)["ask_confirm"] is False
    s2, k2, p2 = _seller(eng, "나수산")
    scm.import_orders(eng, k2, IP, "판매처 주문번호,상품 번호,수량,받는 분,휴대폰,주소\n"
                      f"N1,{p2},1,홍길동,010-1234-5678,서울\n", entrust_ok=True)  # fmt: skip
    _age(eng, s2["seller_id"], 61)
    assert all(
        r["name"] != "나수산" for r in health.report(eng)["sellers"]
    )  # 팔리고 있으면 61일 변화 없어도 목록에 없음
    assert health.signals(eng, sel.detail(eng, s2["seller_id"]), sel.now())["orders_30"] == 1


def test_daily_check_notifies_once_until_change(eng):
    s, k, pid = _seller(eng)
    _age(eng, s["seller_id"], 61)
    first = health.daily_check(eng)
    assert first["flagged"] == ["가농장"] and first["notified"] == "queue"
    assert health.daily_check(eng)["flagged"] == []  # 같은 셀러를 매일 다시 알리지 않음
    sel_status = sel.detail(eng, s["seller_id"])["status"]
    assert sel_status == "active"  # 자동 정지 없음 — 사람이 정함


def test_invited_but_never_entered(eng):
    s = sel.create_seller(eng, name="다과원", kind="direct", contact={"name": "이", "email": "l@b.kr"}, by="operator")
    sel.issue_key(eng, s["seller_id"], by="operator")
    _age(eng, s["seller_id"], 20)
    assert [x["name"] for x in health.report(eng)["no_entry"]] == ["다과원"]


def test_api(eng):
    from app.main import app

    cl = TestClient(app)
    s, k, pid = _seller(eng)
    r = cl.post("/seller/api/products/listing", json={"key": k, "product_id": pid, "on": False})
    assert r.json()["changed"] == 1
    assert cl.post("/seller/api/products", json={"key": k}).json()["products"][0]["sale_state"] == "off"
    assert cl.post("/seller/api/confirm", json={"key": k}).json()["health"]["ask_confirm"] is False
    rep = cl.get("/admin/api/seller-health", headers=H).json()
    assert rep["rules"]["dead_days"] == 60 and "홍길동" not in str(rep)
    assert cl.get("/admin/api/seller-health").status_code in (401, 403)
