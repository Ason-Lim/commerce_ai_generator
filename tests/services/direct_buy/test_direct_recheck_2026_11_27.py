"""2026-11-27 판매처 이동 전 재확인 — lookup_catalog 로 지금 가격·재고를 다시 묻는다(저장 없음)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.services.direct_buy import catalog, service
from tests.services.direct_buy.test_direct_buy_2026_11_26 import FakeHttp, product

VID = "gid://shopify/ProductVariant/12345"


@pytest.fixture(autouse=True)
def env(monkeypatch):
    for k in ("SHOPIFY_CATALOG", "SHOPIFY_CATALOG_CLIENT_ID", "SHOPIFY_CATALOG_CLIENT_SECRET"):
        monkeypatch.delenv(k, raising=False)
    catalog._token.clear()


def item(cents=2499, avail=True, vid=VID):
    p = product("Olive Oil 500ml", cents=cents, avail=avail)
    p["variants"][0]["id"] = vid
    return p


def test_offer_keeps_variant_gid_only():
    assert catalog.to_offers({"products": [item()]})[0].variant_id == VID
    assert catalog.to_offers({"products": [item(vid="v1")]})[0].variant_id is None


def test_lookup_body_uses_lookup_catalog_with_korea_context():
    http = FakeHttp([item()])
    catalog.lookup(VID, http=http)
    body = http.calls[-1]["json"]
    assert body["params"]["name"] == "lookup_catalog"
    cat = body["params"]["arguments"]["catalog"]
    assert cat["ids"] == [VID] and cat["context"]["address_country"] == "KR"


@pytest.mark.parametrize("cents,avail,state", [(2499, True, "same"), (2999, True, "changed"), (2499, False, "sold_out")])
def test_recheck_states(cents, avail, state):
    products = [item(cents, avail)] if avail else [item(cents, False)]
    out = service.recheck(VID, 2499, "USD", http=FakeHttp(products))
    assert out["state"] == state
    if state == "changed":
        assert out["price"] == 2999


def test_recheck_bad_id_makes_no_call():
    http = FakeHttp([item()])
    out = service.recheck("https://evil.example", 1, "USD", http=http)
    assert out["ok"] is False and out["state"] == "unknown" and http.calls == []


def test_recheck_failure_tells_to_check_at_seller():
    out = service.recheck(VID, 2499, "USD", http=FakeHttp(status=500, raw={"error": {"message": "x"}}))
    assert out["ok"] is False and "판매처 화면" in out["text"]


def test_route_no_store(monkeypatch):
    from app.main import app
    monkeypatch.setattr(service, "recheck", lambda i, p, c: {"ok": True, "state": "same", "id": i, "p": p, "c": c})
    r = TestClient(app).get("/api/direct/recheck", params={"id": VID, "price": 2499, "cur": "USD"})
    assert r.status_code == 200 and r.json()["p"] == 2499 and "no-store" in r.headers["cache-control"]



# ── 2026-11-27 GPT 검토(높음): 같은 옵션이 없으면 다른 옵션으로 대신하지 않음 ──
def test_recheck_other_option_only_is_unknown():
    out = service.recheck(VID, 2499, "USD", http=FakeHttp([item(vid="gid://shopify/ProductVariant/999")]))
    assert out["state"] == "unknown" and "같은 옵션" in out["text"]


def test_recheck_picks_requested_option_among_many():
    p = item(2499)
    other = dict(p["variants"][0], id="gid://shopify/ProductVariant/1")
    mine = dict(p["variants"][0], id=VID, price={"amount": 3999, "currency": "USD"})
    p["variants"] = [other, mine]
    out = service.recheck(VID, 2499, "USD", http=FakeHttp([p]))
    assert out["state"] == "changed" and out["price"] == 3999
