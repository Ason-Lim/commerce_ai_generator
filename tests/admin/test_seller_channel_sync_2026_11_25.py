"""②-b 판매처 호환 — 그룹 + 판매 단위 · 카테고리 규칙 · 기준 판매처 따라가기 (2026-11-25 사용자 결정 13:37·13:47)."""

from __future__ import annotations

import os
from datetime import timedelta

import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient

os.environ.setdefault("CORPMALL_KEY", Fernet.generate_key().decode())

from app.services.corpmall import store as corp  # noqa: E402
from app.services.seller import catalog, health, scm  # noqa: E402
from app.services.seller import products as prod  # noqa: E402
from app.services.seller import store as sel  # noqa: E402

IP = "1.1.1.1"
HEAD = "그룹번호,그룹명,상품번호,카테고리,상품명,판매옵션,용량,판매가,할인가,배송비 유형,배송비,원산지,인증,재고,전시상태,판매처 주소\n"


def _row(
    ext,
    opt="중량=3kg",
    vol="3kg",
    price="19900",
    origin="제주",
    cert="",
    stock="10",
    display="전시중",
    cat="식품>과일>감귤",
):
    return (
        f"G100,제주 감귤,{ext},{cat},제주 감귤 {vol},{opt},{vol},{int(price) + 2000},{price},무료,0,{origin},{cert},{stock},{display},"
        f"https://smartstore.naver.com/x/products/{ext}\n"
    )


@pytest.fixture
def eng():
    corp.reset_limits()
    e = catalog.engine()
    with e.begin() as c:
        for t in (catalog.t_unit, catalog.t_group, catalog.t_base, scm.t_order, scm.t_stock, prod.t_listing, prod.t_product,
                  sel.t_event, sel.t_key, sel.t_seller):  # fmt: skip
            c.execute(t.delete())
    return e


def _seller(eng, name="가농장", channel="naver"):
    s = sel.create_seller(eng, name=name, kind="direct", contact={"name": "김", "email": "k@a.kr"}, by="operator")
    sel.set_status(eng, s["seller_id"], "active", by="operator", reason="ok")
    k = sel.issue_key(eng, s["seller_id"], by="operator")["code"]
    if channel != "manual":
        catalog.set_base_channel(eng, k, IP, channel)
    return s, k


# ── 카테고리 · 규칙 ──
def test_category_path_keeps_slash_names():
    assert catalog.category_path("식품>냉동/간편조리식품>누룽지") == ["식품", "냉동/간편조리식품", "누룽지"]
    assert catalog.our_top(["식품", "과일"]) == "food" and catalog.our_top(["생활/건강"]) == "non_food"


def test_rules_origin_required_and_eco_cert_needs_org_no():
    e, _ = catalog.check(["식품", "과일", "감귤"], [], [])
    assert e and "원산지" in e[0]
    e, _ = catalog.check(["식품", "과일", "감귤"], ["상세페이지 참조"], [])
    assert e
    e, _ = catalog.check(["식품", "과일"], ["제주"], [{"kind": "무농약", "org": "", "no": ""}])
    assert e and "인증기관" in e[0]
    e, w = catalog.check(
        ["식품", "과일"], ["제주"], [{"kind": "무농약", "org": "국립농산물품질관리원", "no": "12-34-567"}]
    )
    assert e == [] and w == []
    e, w = catalog.check(["생활/건강", "주방용품"], [], [])
    assert e == [] and any("식품 외" in x for x in w) and any("KC" in x for x in w)


def test_manual_entry_uses_group_unit_and_rules(eng):
    _, k = _seller(eng, channel="manual")
    with pytest.raises(sel.SellerError, match="원산지가 필수"):
        prod.save(eng, k, IP, {"name": "감귤 3kg", "price": "19900", "category": "식품>과일>감귤"})
    p3 = prod.save(eng, k, IP, {"name": "감귤 3kg", "price": "19900", "category": "식품>과일>감귤", "origin": "제주",
                                "group": "제주 감귤", "option": "중량=3kg", "cert": "무농약/국립농산물품질관리원/12-34-567"})  # fmt: skip
    p5 = prod.save(eng, k, IP, {"name": "감귤 5kg", "price": "29900", "category": "식품>과일>감귤", "origin": "제주",
                                "group": "제주 감귤", "option": "중량=5kg"})  # fmt: skip
    mine = {p["product_id"]: p for p in prod.list_mine(eng, k, IP)}
    assert mine[p3["product_id"]]["unit"]["group_id"] == mine[p5["product_id"]]["unit"]["group_id"]
    assert mine[p3["product_id"]]["unit"]["info"]["option"] == {"중량": "3kg"}
    assert mine[p3["product_id"]]["declared"]["certs"][0]["no"] == "12-34-567"
    assert mine[p3["product_id"]]["locked"] is False


# ── 판매처 따라가기 ──
def test_sync_adds_units_in_one_group(eng):
    _, k = _seller(eng)
    rep = catalog.import_std_csv(eng, k, IP, "naver", HEAD + _row("N1-1") + _row("N1-2", "중량=5kg", "5kg", "29900"))
    assert rep["added"] == 2 and rep["ok"]
    mine = prod.list_mine(eng, k, IP)
    assert len({p["unit"]["group_id"] for p in mine}) == 1 and all(
        p["locked"] and p["status"] == "pending" for p in mine
    )
    assert all(f["source"] == "seller" for p in mine for f in p["facts"])  # 판매처 값도 '판매자 표기'
    stock = scm.stock_of(eng, sel.list_sellers(eng)[0]["seller_id"])
    assert {v["stock"] for v in stock.values()} == {10}  # 재고도 판매처 값


def test_fast_fields_update_without_review(eng):
    _, k = _seller(eng)
    catalog.import_std_csv(eng, k, IP, "naver", HEAD + _row("N1-1"))
    pid = prod.list_mine(eng, k, IP)[0]["product_id"]
    prod.verify(eng, pid, "origin", "제주", by="operator", note="증명서")
    prod.review(eng, pid, "approved", by="operator")
    rep = catalog.import_std_csv(eng, k, IP, "naver", HEAD + _row("N1-1", price="17900", stock="0"))
    assert rep["fast"] == 1 and rep["review"] == 0
    p = prod.list_mine(eng, k, IP)[0]
    assert p["status"] == "approved" and p["price"] == 17900 and p["sale_state"] == "sold_out"
    assert any(f["key"] == "origin" and f["source"] == "verified" for f in p["facts"])  # 확인값 그대로


def test_origin_change_drops_only_that_verification_and_needs_review(eng):
    _, k = _seller(eng)
    catalog.import_std_csv(eng, k, IP, "naver", HEAD + _row("N1-1", cert="GAP/농관원/1234"))
    pid = prod.list_mine(eng, k, IP)[0]["product_id"]
    prod.verify(eng, pid, "origin", "제주", by="operator", note="증명서")
    prod.verify(eng, pid, "cert", "GAP(1234)", by="operator", note="인증서")
    prod.review(eng, pid, "approved", by="operator")
    rep = catalog.import_std_csv(eng, k, IP, "naver", HEAD + _row("N1-1", origin="전남", cert="GAP/농관원/1234"))
    assert rep["review"] == 1
    p = prod.list_mine(eng, k, IP)[0]
    src = {f["key"]: f["source"] for f in p["facts"]}
    assert p["status"] == "pending" and src["origin"] == "seller" and src["cert"] == "verified"


def test_unchanged_sync_is_not_activity_but_changed_is(eng):
    s, k = _seller(eng)
    catalog.import_std_csv(eng, k, IP, "naver", HEAD + _row("N1-1"))
    from sqlalchemy import update

    with eng.begin() as c:  # 70일 전으로
        for r in c.execute(sel.t_event.select()).mappings().all():
            c.execute(update(sel.t_event).where(sel.t_event.c.id == r["id"]).values(at=r["at"] - timedelta(days=70)))
    rep = catalog.import_std_csv(eng, k, IP, "naver", HEAD + _row("N1-1"))
    assert rep["unchanged"] == 1
    assert health.signals(eng, sel.detail(eng, s["seller_id"]), sel.now())["change_days"] >= 69
    catalog.import_std_csv(eng, k, IP, "naver", HEAD + _row("N1-1", price="18900"))
    assert health.signals(eng, sel.detail(eng, s["seller_id"]), sel.now())["change_days"] == 0


def test_locked_units_cannot_be_edited_here_but_can_be_turned_off(eng):
    _, k = _seller(eng)
    catalog.import_std_csv(eng, k, IP, "naver", HEAD + _row("N1-1"))
    pid = prod.list_mine(eng, k, IP)[0]["product_id"]
    with pytest.raises(sel.SellerError, match="네이버 스마트스토어에서 바꿔"):
        prod.save(eng, k, IP, {"name": "x", "price": "100", "origin": "제주"}, pid)
    with pytest.raises(sel.SellerError, match="네이버 스마트스토어에서 바꿔"):
        scm.set_stock(eng, k, IP, pid, stock=3, sold_out=False, restock_on=None)
    assert prod.set_listing(eng, k, IP, pid, False) == 1  # 우리 몰에서만 끄기는 됨


def test_display_suspended_and_missing_from_full_list(eng):
    _, k = _seller(eng)
    catalog.import_std_csv(
        eng, k, IP, "naver", HEAD + _row("N1-1") + _row("N1-2", "중량=5kg", "5kg", "29900", display="전시중지")
    )
    st = {p["unit"]["ext_no"]: p["sale_state"] for p in prod.list_mine(eng, k, IP)}
    assert st["N1-2"] in ("off", "pending")
    assert next(p for p in prod.list_mine(eng, k, IP) if p["unit"]["ext_no"] == "N1-2")["on"] is False
    rep = catalog.import_std_csv(eng, k, IP, "naver", HEAD + _row("N1-1"), full=True)
    assert rep["missing"] == 1
    gone = next(p for p in prod.list_mine(eng, k, IP) if p["unit"]["ext_no"] == "N1-2")
    assert gone["unit"]["source_missing"] is True and gone["on"] is False
    q = prod.queue(eng, "all")
    assert any("판매처에서 사라짐" in x["warnings"] for x in q)


def test_only_base_channel_and_isolation(eng):
    _, ka = _seller(eng, "가농장", "naver")
    _, kb = _seller(eng, "나수산", "coupang")
    with pytest.raises(sel.SellerError, match="기준 판매처"):
        catalog.import_std_csv(eng, ka, IP, "coupang", HEAD + _row("C1"))
    catalog.import_std_csv(eng, ka, IP, "naver", HEAD + _row("SAME-1"))
    catalog.import_std_csv(eng, kb, IP, "coupang", HEAD + _row("SAME-1"))  # 같은 번호여도 셀러·판매처마다 따로
    assert len(prod.list_mine(eng, ka, IP)) == 1 and len(prod.list_mine(eng, kb, IP)) == 1


def test_bad_rows_all_or_nothing(eng):
    _, k = _seller(eng)
    bad = HEAD + _row("N1-1") + "G1,감귤,,식품>과일,감귤,,3kg,1000,1000,무료,0,제주,,1,전시중,\n"
    got = catalog.import_std_csv(eng, k, IP, "naver", bad)
    assert got["ok"] is False and got["errors"][0]["line"] == 3 and prod.list_mine(eng, k, IP) == []
    with pytest.raises(sel.SellerError, match="모르는 칸"):
        catalog.import_std_csv(eng, k, IP, "naver", "상품번호,상품명,순위가점\n1,a,3\n")


def test_api(eng):
    from app.main import app

    cl = TestClient(app)
    _, k = _seller(eng, channel="manual")
    r = cl.post("/seller/api/channel", json={"key": k, "channel": "coupang"})
    assert r.json()["channel"] == "coupang" and "상품번호" in r.json()["std_template"]
    r = cl.post("/seller/api/sync", json={"key": k, "channel": "coupang", "csv": HEAD + _row("C9")})
    assert r.json()["added"] == 1
    p = cl.post("/seller/api/products", json={"key": k}).json()["products"][0]
    assert p["locked"] is True and p["unit"]["channel_label"] == "쿠팡"
    r = cl.post(
        "/seller/api/products/save",
        json={
            "key": k,
            "fields": {"name": "누룽지", "price": 5000, "category": "식품>냉동/간편조리식품>누룽지", "origin": "국산"},
        },
    )
    assert r.json()["ok"] is True
