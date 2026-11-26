"""2026-11-26 해외 직구 — Shopify Global Catalog 검색·홈 칸·직구 도우미 (가짜 응답, 바깥 호출 없음)."""

from __future__ import annotations

import json

import pytest

from app.services.direct_buy import catalog, rules, service


def product(title, cents=1899, avail=True, seller="Olive House", url="https://olive.example/products/a?utm=x"):
    return {"id": "gid://shopify/p/1", "title": title, "description": {"plain": "d"},
            "price_range": {"min": {"amount": cents, "currency": "USD"}, "max": {"amount": cents, "currency": "USD"}},
            "media": [{"type": "image", "url": "https://cdn.example/a.jpg", "alt_text": ""}],
            "variants": [{"id": "v1", "title": "500ml", "price": {"amount": cents, "currency": "USD"}, "url": url,
                          "checkout_url": "https://olive.example/cart/v1:1", "availability": {"available": avail}}],
            "seller": {"name": seller, "domain": "olive.example", "links": {"refund_policy": "https://olive.example/refund"}}}


class Resp:
    def __init__(self, data, status=200):
        self.status_code, self._d = status, data
        self.content = json.dumps(data).encode()

    def json(self):
        return self._d


class FakeHttp:
    def __init__(self, products=None, status=200, raw=None):
        self.calls, self.products, self.status, self.raw = [], products or [], status, raw

    def post(self, url, json=None, headers=None, timeout=None, allow_redirects=None):
        self.calls.append({"url": url, "json": json, "headers": headers})
        if url == catalog.TOKEN_URL:
            return Resp({"access_token": "tok", "token_type": "Bearer"})
        if self.raw is not None:
            return Resp(self.raw, self.status)
        return Resp({"jsonrpc": "2.0", "id": json["id"], "result": {"structuredContent": {
            "ucp": {"version": "2026-08-25", "status": "success"}, "products": self.products, "messages": [],
            "pagination": {"has_next_page": False}}}}, self.status)


@pytest.fixture(autouse=True)
def env(monkeypatch):
    for k in ("SHOPIFY_CATALOG", "SHOPIFY_CATALOG_CLIENT_ID", "SHOPIFY_CATALOG_CLIENT_SECRET", "DIRECT_SHOW_QUARANTINE",
              "DIRECT_USD_KRW", "UCP_PLATFORM_PROFILE_URL"):
        monkeypatch.delenv(k, raising=False)
    catalog._token.clear()


def test_request_asks_korea_shipping_and_sends_no_personal_data():
    http = FakeHttp([product("Extra Virgin Olive Oil 500ml")])
    res = catalog.search("extra virgin olive oil", http=http)
    assert res.ok and len(res.offers) == 1
    body = http.calls[0]["json"]
    args = body["params"]["arguments"]
    assert body["method"] == "tools/call" and body["params"]["name"] == "search_catalog"
    assert args["meta"]["ucp-agent"]["profile"] == "https://trendguide.kr/.well-known/ucp"
    assert args["catalog"]["filters"]["ships_to"] == {"country": "KR"}
    assert set(args["catalog"]["context"]) == {"address_country", "currency", "language"}   # 주소·IP 없음
    assert "Authorization" not in http.calls[0]["headers"]                                    # 키 없으면 키 없이


def test_urls_kept_exactly_and_sold_out_dropped():
    http = FakeHttp([product("Olive Oil A"), product("Olive Oil B", avail=False)])
    offers = catalog.search("olive oil", http=http).offers
    assert [o.title for o in offers] == ["Olive Oil A"]
    assert offers[0].url == "https://olive.example/products/a?utm=x"              # 귀속 파라미터 그대로
    assert offers[0].refund_policy == "https://olive.example/refund" and offers[0].seller == "Olive House"


def test_bearer_token_when_key_configured(monkeypatch):
    monkeypatch.setenv("SHOPIFY_CATALOG_CLIENT_ID", "id")
    monkeypatch.setenv("SHOPIFY_CATALOG_CLIENT_SECRET", "sec")
    http = FakeHttp([product("Olive Oil")])
    catalog.search("olive oil", http=http)
    catalog.search("olive oil 2", http=http)
    assert [c["url"] for c in http.calls].count(catalog.TOKEN_URL) == 1             # 토큰만 메모리에
    assert http.calls[-1]["headers"]["Authorization"] == "Bearer tok"


def test_errors_become_results_not_exceptions():
    assert catalog.search("x", http=FakeHttp(status=429, raw={})).code == "rate_limited"
    assert catalog.search("x", http=FakeHttp(status=401, raw={})).code == "auth"
    err = catalog.search("x", http=FakeHttp(raw={"jsonrpc": "2.0", "error": {"code": -32000, "message": "bad"}}))
    assert not err.ok and err.error == "bad"


def test_no_cache_every_search_calls_shopify():
    http = FakeHttp([product("Olive Oil")])
    catalog.search("olive oil", http=http)
    catalog.search("olive oil", http=http)
    assert len(http.calls) == 2


def test_disabled_switch(monkeypatch):
    monkeypatch.setenv("SHOPIFY_CATALOG", "0")
    http = FakeHttp([product("Olive Oil")])
    assert catalog.search("olive oil", http=http).code == "disabled" and not http.calls


def test_food_filter_and_quarantine_rules():
    assert rules.keep("Extra Virgin Olive Oil 1L")
    assert not rules.keep("Olive Oil Soap Bar")
    assert not rules.keep("Olive Oil & Aged Cheese Gift Box")          # 올리브유 칸에 치즈 묶음은 빼기
    assert rules.keep("Aged Cheese", item_status="quarantine")


def test_duty_free_guide_by_price():
    assert rules.duty(14999, "USD")["kind"] == "in"
    assert rules.duty(18000, "USD")["kind"] == "us_only"
    assert rules.duty(25000, "USD")["kind"] == "over"
    assert rules.duty(20000, "KRW")["kind"] == "unknown"


def test_home_sections_blocked_and_quarantine_show_notes_only():
    http = FakeHttp([product("Extra Virgin Olive Oil"), product("Olive Oil Soap")])
    data = service.home(http=http)
    sec = {s["key"]: s for s in data["sections"]}
    assert [p["title"] for p in sec["olive_oil"]["products"]] == ["Extra Virgin Olive Oil"]
    assert sec["cheese"]["products"] == [] and "검역" in sec["cheese"]["note"]
    assert sec["fresh_olive"]["products"] == [] and "수입이 금지" in sec["fresh_olive"]["note"]
    queries = [c["json"]["params"]["arguments"]["catalog"]["query"] for c in http.calls]
    assert "aged cheese" not in queries                                  # 검역 품목은 기본적으로 부르지도 않음
    assert "판매 당사자가 아니며" in data["notice"]
    assert data["sections"][0]["products"][0]["duty"]["kind"] == "in"


def test_search_quarantine_query_shows_guidance(monkeypatch):
    data = service.search("cheese", http=FakeHttp([product("Aged Cheese")]))
    assert data["products"] == [] and data["quarantine_note"]
    assert any(s["key"] == "quarantine" for s in data["checklist"])


def test_krw_estimate_only_with_configured_rate(monkeypatch):
    http = FakeHttp([product("Extra Virgin Olive Oil", cents=2000)])
    assert service.search("olive oil", http=http)["products"][0]["krw_estimate"] is None
    monkeypatch.setenv("DIRECT_USD_KRW", "1400")
    assert service.search("olive oil", http=http)["products"][0]["krw_estimate"] == 28000


def test_routes_no_store(monkeypatch):
    from fastapi.testclient import TestClient

    from app.main import app

    monkeypatch.setattr(service.catalog, "requests", FakeHttp([product("Extra Virgin Olive Oil")]))
    c = TestClient(app)
    r = c.get("/api/direct/home")
    assert r.status_code == 200 and r.headers["cache-control"] == "no-store"
    assert c.get("/api/direct/search", params={"q": "olive oil"}).json()["products"][0]["title"] == "Extra Virgin Olive Oil"
