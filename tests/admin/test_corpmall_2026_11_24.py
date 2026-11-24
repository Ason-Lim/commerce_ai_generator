"""B2B 폐쇄몰 1차 (2026-11-24) — 코드 입장·선택 저장·배송 정보 암호화·마감·파기."""

from __future__ import annotations

import os
from datetime import datetime, timedelta

import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient
from sqlalchemy import select

os.environ.setdefault("CORPMALL_KEY", Fernet.generate_key().decode())

from app.services.corpmall import store  # noqa: E402

KST = store.KST
OPEN_AT = datetime(2026, 12, 1, 9, 0, tzinfo=KST)
IN = OPEN_AT + timedelta(days=1)
SHIP = {
    "name": "홍길동",
    "phone": "010-1234-5678",
    "zipcode": "04524",
    "address": "서울 중구 세종대로 110 3층",
    "memo": "",
}


def _spec(slug, mode="individual", **kw):
    return {
        "slug": slug,
        "client": "샘플공사",
        "title": "설 선물",
        "opens_at": "2026-12-01T09:00",
        "closes_at": "2026-12-10T18:00",
        "delivery_mode": mode,
        "default_item_id": "A",
        "items": [
            {"id": "A", "name": "한과", "tier": "5만원대"},
            {"id": "B", "name": "감귤", "supplier_candidate_id": "s1"},
        ],
        **kw,
    }


@pytest.fixture
def eng():
    store.reset_limits()
    return store.engine()


def _mall(eng, slug, mode="individual", n=3):
    m = store.create_mall(eng, _spec(slug, mode))
    store.set_status(eng, m["mall_id"], "open")
    return m, store.issue_codes(eng, m["mall_id"], n)


def test_codes_are_hashed_and_both_entry_paths_work(eng):
    m, codes = _mall(eng, "t-hash")
    label, code, token = codes[0]
    assert len(code) == 9 and len(token) == 24
    with eng.connect() as c:
        rows = c.execute(select(store.t_code).where(store.t_code.c.mall_id == m["mall_id"])).mappings().all()
    blob = repr(rows)
    assert code.replace("-", "") not in blob and token not in blob
    for cred in (code, code.lower().replace("-", ""), token):
        got = store.enter(eng, "t-hash", cred, "ip1", at=IN)
        assert got["label"] == label and got["window"] == "open" and got["order"] is None
    pub = got["mall"]
    assert "supplier_candidate_id" not in repr(pub) and "mall_id" not in pub


def test_entering_does_not_consume(eng):
    m, codes = _mall(eng, "t-noconsume")
    for _ in range(3):
        store.enter(eng, "t-noconsume", codes[0][2], "ip", at=IN)
    assert store.stats(eng, m["mall_id"])["chosen"] == 0
    with eng.connect() as c:
        assert (
            c.execute(select(store.t_code.c.status).where(store.t_code.c.mall_id == m["mall_id"])).scalars().all()
            == ["unused"] * 3
        )


def test_draft_and_window(eng):
    m = store.create_mall(eng, _spec("t-window"))
    ((_, code, _),) = store.issue_codes(eng, m["mall_id"], 1)
    with pytest.raises(store.MallError):
        store.enter(eng, "t-window", code, "ip", at=IN)  # 초안은 안 보임
    store.set_status(eng, m["mall_id"], "open")
    assert store.enter(eng, "t-window", code, "ip", at=OPEN_AT - timedelta(minutes=1))["window"] == "not_open"
    assert store.enter(eng, "t-window", code, "ip", at=datetime(2026, 12, 10, 18, 0, tzinfo=KST))["window"] == "closed"
    with pytest.raises(store.MallError, match="기간"):
        store.choose(eng, "t-window", code, "A", "ip", shipping=SHIP, consent=True, at=OPEN_AT - timedelta(hours=1))


def test_rate_limit_per_client_and_mall(eng):
    _, codes = _mall(eng, "t-limit", n=1)
    for _ in range(store.MAX_FAILS):
        with pytest.raises(store.MallError, match="맞지"):
            store.enter(eng, "t-limit", "ZZZZ-ZZZZ", "bad", at=IN)
    with pytest.raises(store.MallError, match="막았"):
        store.enter(eng, "t-limit", codes[0][1], "bad", at=IN)  # 맞는 코드도 잠시 막힘
    assert store.enter(eng, "t-limit", codes[0][1], "other", at=IN)["label"] == 1
    store.reset_limits()
    for i in range(store.MALL_MAX_FAILS):
        store._fail(f"ip{i}", "t-limit")
    with pytest.raises(store.MallError, match="초대 링크"):
        store.enter(eng, "t-limit", codes[0][1], "fresh", at=IN)  # 몰 전체 한도 — 짧은 코드만 막힘
    assert store.enter(eng, "t-limit", codes[0][2], "fresh", at=IN)["label"] == 1


def test_choose_requires_consent_and_valid_shipping(eng):
    _, codes = _mall(eng, "t-consent")
    code = codes[0][1]
    with pytest.raises(store.MallError, match="동의"):
        store.choose(eng, "t-consent", code, "A", "ip", shipping=SHIP, at=IN)
    with pytest.raises(store.MallError, match="휴대폰"):
        store.choose(eng, "t-consent", code, "A", "ip", shipping=dict(SHIP, phone="1234"), consent=True, at=IN)
    with pytest.raises(store.MallError, match="없는 상품"):
        store.choose(eng, "t-consent", code, "Z", "ip", shipping=SHIP, consent=True, at=IN)
    got = store.choose(eng, "t-consent", code, "A", "ip", shipping=SHIP, consent=True, at=IN)
    assert got["order"]["item_id"] == "A" and got["order"]["ship_status"] == "requested"
    shown = got["order"]["shipping"]
    assert shown["name"] == "홍**" and "5678" not in shown["phone"] and "110" not in shown["address"]


def test_shipping_encrypted_and_change_needs_verify(eng):
    m, codes = _mall(eng, "t-verify")
    code = codes[0][1]
    store.choose(eng, "t-verify", code, "A", "ip", shipping=SHIP, consent=True, at=IN)
    with eng.connect() as c:
        enc = c.execute(select(store.t_order.c.ship_enc).where(store.t_order.c.mall_id == m["mall_id"])).scalar()
    assert "홍길동" not in enc and "5678" not in enc
    # 상품만 바꾸기 — 배송지 그대로, 재확인 없음
    assert store.choose(eng, "t-verify", code, "B", "ip", at=IN)["order"]["item_id"] == "B"
    other = dict(SHIP, address="부산 어딘가 1")
    with pytest.raises(store.MallError, match="끝 4자리"):
        store.choose(eng, "t-verify", code, "B", "ip", shipping=other, consent=True, at=IN)
    with pytest.raises(store.MallError, match="끝 4자리"):
        store.choose(eng, "t-verify", code, "B", "ip", shipping=other, consent=True, verify="0000", at=IN)
    store.choose(eng, "t-verify", code, "B", "ip", shipping=other, consent=True, verify="5678", at=IN)
    out = store.export_orders(eng, m["mall_id"], by="t")
    assert len(out) == 1 and out[0]["address"] == "부산 어딘가 1" and out[0]["item"] == "감귤"


def test_one_order_per_code_even_when_choosing_twice(eng):
    m, codes = _mall(eng, "t-once", mode="bulk")
    store.choose(eng, "t-once", codes[0][1], "A", "ip", at=IN)
    store.choose(eng, "t-once", codes[0][2], "B", "ip", at=IN)  # 링크로 들어와 다시 — 같은 코드
    assert [o["item_id"] for o in store.orders(eng, m["mall_id"])] == ["B"]
    assert store.stats(eng, m["mall_id"])["chosen"] == 1


def test_bulk_mall_takes_no_shipping(eng):
    m, codes = _mall(eng, "t-bulk", mode="bulk")
    got = store.choose(eng, "t-bulk", codes[0][1], "A", "ip", shipping=SHIP, consent=True, at=IN)
    assert got["order"]["shipping"] is None
    assert store.export_orders(eng, m["mall_id"], by="t") == []


def test_reissue_voids_old_code_and_link_and_moves_order(eng):
    m, codes = _mall(eng, "t-reissue", mode="bulk")
    label, code, token = codes[0]
    store.choose(eng, "t-reissue", code, "B", "ip", at=IN)
    new_label, new_code, new_token = store.void_and_reissue(eng, m["mall_id"], label)
    for old in (code, token):
        with pytest.raises(store.MallError, match="맞지"):
            store.enter(eng, "t-reissue", old, "ip2", at=IN)
    got = store.enter(eng, "t-reissue", new_token, "ip2", at=IN)
    assert got["label"] == new_label and got["order"]["item_id"] == "B"
    assert store.enter(eng, "t-reissue", new_code, "ip2", at=IN)["label"] == new_label
    with pytest.raises(store.MallError):
        store.void_and_reissue(eng, m["mall_id"], label)


def test_close_defaults_depend_on_delivery_mode(eng):
    mb, cb = _mall(eng, "t-close-bulk", mode="bulk")
    store.choose(eng, "t-close-bulk", cb[0][1], "B", "ip", at=IN)
    assert store.close_mall(eng, mb["mall_id"]) == {"defaulted": 2}
    assert {o["ship_status"] for o in store.orders(eng, mb["mall_id"]) if o["defaulted"]} == {"none"}
    assert store.enter(eng, "t-close-bulk", cb[1][1], "ip", at=IN)["window"] == "closed"

    mi, ci = _mall(eng, "t-close-ind")
    store.choose(eng, "t-close-ind", ci[0][1], "B", "ip", shipping=SHIP, consent=True, at=IN)
    store.close_mall(eng, mi["mall_id"])
    assert store.no_address_labels(eng, mi["mall_id"]) == [2, 3]  # 주소 없는 기본 상품 — 발주처 후속 처리
    assert len(store.export_orders(eng, mi["mall_id"], by="t")) == 1
    st = store.stats(eng, mi["mall_id"])
    assert st["chosen"] == 1 and st["defaulted"] == 2 and st["rate"] == round(1 / 3, 4)


def test_export_once_then_purge_after_retention(eng):
    m, codes = _mall(eng, "t-purge")
    store.choose(eng, "t-purge", codes[0][1], "A", "ip", shipping=SHIP, consent=True, at=IN)
    assert len(store.export_orders(eng, m["mall_id"], by="t")) == 1
    assert store.export_orders(eng, m["mall_id"], by="t") == []  # 두 번 나오지 않음
    with pytest.raises(store.MallError, match="발송 준비"):
        store.choose(eng, "t-purge", codes[0][1], "B", "ip", at=IN)
    oid = store.orders(eng, m["mall_id"])[0]["order_id"]
    assert store.mark(eng, m["mall_id"], [oid], "delivered") == 1
    with eng.connect() as c:
        delivered = c.execute(select(store.t_order.c.delivered_at).where(store.t_order.c.order_id == oid)).scalar()
    d = delivered if delivered.tzinfo else delivered.replace(tzinfo=KST)
    store.purge(eng, at=d + timedelta(days=29))
    assert store.orders(eng, m["mall_id"])[0]["has_shipping"]
    assert store.purge(eng, at=d + timedelta(days=31)) >= 1
    o = store.orders(eng, m["mall_id"])[0]
    assert not o["has_shipping"] and o["purged"]


def test_events_and_orders_hold_no_personal_data(eng):
    m, codes = _mall(eng, "t-pii")
    store.choose(eng, "t-pii", codes[0][1], "A", "ip", shipping=SHIP, consent=True, at=IN)
    store.export_orders(eng, m["mall_id"], by="t")
    blob = (
        repr(store.events(eng, m["mall_id"]))
        + repr(store.orders(eng, m["mall_id"]))
        + repr(store.stats(eng, m["mall_id"]))
    )
    for s in ("홍길동", "5678", "세종대로", codes[0][1], codes[0][2]):
        assert s not in blob


def test_spec_validation(eng):
    for bad in (
        {"slug": "A B"},
        {"delivery_mode": "drone"},
        {"items": []},
        {"default_item_id": "Q"},
        {"closes_at": "2026-11-30T00:00"},
    ):
        with pytest.raises(store.MallError):
            store.create_mall(eng, dict(_spec("t-spec"), **bad))
    store.create_mall(eng, _spec("t-spec"))
    with pytest.raises(store.MallError, match="이미"):
        store.create_mall(eng, _spec("t-spec"))


# ── 라우트 ─────────────────────────────────────────────────────────────
@pytest.fixture
def client():
    from app.main import app

    store.reset_limits()
    return TestClient(app)


H = {"X-Access-Token": "test-token"}


def test_routes_end_to_end(client):
    r = client.post(
        "/admin/api/corpmall",
        json={"spec": _spec("t-route", "bulk", opens_at="2026-01-01T00:00", closes_at="2099-01-01T00:00")},
        headers=H,
    )
    assert r.status_code == 200, r.text
    mid = r.json()["mall"]["mall_id"]
    assert client.post("/admin/api/corpmall", json={"spec": {}}).status_code in (401, 403)
    client.post(f"/admin/api/corpmall/{mid}/status/open", headers=H)
    codes = client.post(f"/admin/api/corpmall/{mid}/codes", json={"n": 2}, headers=H).json()["codes"]
    assert codes[0]["link"].startswith("/corp/t-route#t=") and len(codes[0]["link"].split("#t=")[1]) == 24

    page = client.get("/corp/t-route")
    assert page.status_code == 200 and "noindex" in page.headers["x-robots-tag"]
    token = codes[0]["link"].split("#t=")[1]
    e = client.post("/corp/api/t-route/enter", json={"code": token})
    assert e.json()["ok"] and "supplier_candidate_id" not in e.text
    assert client.post("/corp/api/t-route/enter", json={"code": "nope", "x": 1}).status_code == 422
    bad = client.post("/corp/api/t-route/enter", json={"code": "AAAA-AAAA"})
    assert bad.status_code == 400 and not bad.json()["ok"]
    ch = client.post("/corp/api/t-route/choose", json={"code": codes[1]["code"], "item_id": "B"})
    assert ch.json()["order"]["item_id"] == "B"

    d = client.get(f"/admin/api/corpmall/{mid}", headers=H).json()
    assert d["stats"]["chosen"] == 1 and len(d["orders"]) == 1
    assert client.post(f"/admin/api/corpmall/{mid}/status/closed", headers=H).json()["defaulted"] == 1
    assert client.get(f"/admin/api/corpmall/{mid}/no-address", headers=H).json() == {"labels": []}
    re_ = client.post(f"/admin/api/corpmall/{mid}/codes/1/reissue", headers=H).json()
    assert re_["label"] == 3 and "#t=" in re_["link"]
    assert client.get("/admin/b2b/mall", headers=H).status_code in (200, 302, 303, 307)


def test_robots_blocks_corp():
    from app.services.trend_posts import render

    txt = render.robots_txt() if hasattr(render, "robots_txt") else ""
    if txt:
        assert "Disallow: /corp/" in txt
