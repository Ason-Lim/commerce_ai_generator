"""2026-11-27 대화 검색 결과 아래 해외 직구 칸 — 품목표 매칭·통화 환산·차단 품목·홈 칸 제거."""

from __future__ import annotations

import pytest

from app.services.chat.service import direct_buy_block
from app.services.direct_buy import items, service
from tests.services.direct_buy.test_direct_buy_2026_11_26 import FakeHttp, product

FX = {"rate": 1333.88, "source": "관세청 과세환율(수입)", "date": "2026-11-22", "kind": "customs", "stale": False,
      "table": {"USD": 1333.88, "GBP": 1756.5, "AUD": 896.87, "JPY": 8.3599, "KRW": 1.0}}


@pytest.fixture(autouse=True)
def env(monkeypatch):
    for k in ("DIRECT_IN_CHAT", "SHOPIFY_CATALOG", "DIRECT_SHOW_QUARANTINE"):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setattr(service, "_fx", lambda: dict(FX))


@pytest.mark.parametrize("label,text,key", [
    ("올리브유", "올리브유 추천해줘", "olive_oil"),
    ("엑스트라버진 올리브유", "엑스트라버진 올리브유", "olive_oil"),
    ("올리브", "올리브 추천", "olives"),
    ("발사믹", "발사믹 식초 추천", "balsamic"),
    ("꿀", "꿀 추천해줘", "honey"),
    ("원두", "원두 추천", "coffee"),
])
def test_match_known_items(label, text, key):
    assert items.match(label, text).key == key


@pytest.mark.parametrize("label,text", [("사과", "사과 추천"), ("꿀고구마", "꿀고구마 추천"), ("치즈", "치즈 추천해줘"),
                                         ("햄", "햄 추천"), ("귤", "귤 10kg")])
def test_no_direct_block_for_ordinary_searches(label, text):
    assert items.match(label, text) is None and direct_buy_block(label, text) is None


def test_blocked_item_only_when_customer_says_direct_buy():
    it = items.match("치즈", "해외 직구 치즈 추천")
    assert it.key == "dairy" and it.status == "blocked"
    blk = direct_buy_block("치즈", "해외 직구 치즈 추천")
    assert blk["type"] == "direct_buy" and blk["data"]["status"] == "blocked" and "유제품" in blk["data"]["note"]
    assert items.match("생올리브", "생올리브 직구").key == "fresh"            # '올리브' 보다 긴 '생올리브'가 이김


def test_block_carries_no_shopify_data_and_switch(monkeypatch):
    blk = direct_buy_block("올리브유", "올리브유 추천해줘")
    assert blk == {"type": "direct_buy", "data": {"key": "olive_oil", "label": "올리브유", "status": "ok"}}
    monkeypatch.setenv("DIRECT_IN_CHAT", "0")
    assert direct_buy_block("올리브유", "올리브유 추천해줘") is None


def test_search_item_converts_any_currency_with_customs_table():
    gbp = product("Ultra High Phenolic Extra Virgin Olive Oil", cents=3446)
    gbp["variants"][0]["price"]["currency"] = "GBP"
    krw = product("Italian Extra Virgin Olive Oil", cents=36000, url="https://k.example/p")
    krw["variants"][0]["price"]["currency"] = "KRW"
    data = service.search_item("olive_oil", http=FakeHttp([product("Arbequina Extra Virgin Olive Oil", cents=2499), gbp, krw]))
    p = {x["title"]: x for x in data["products"]}
    assert p["Arbequina Extra Virgin Olive Oil"]["krw_estimate"] == round(24.99 * 1333.88, -2)
    assert p["Ultra High Phenolic Extra Virgin Olive Oil"]["krw_estimate"] == round(34.46 * 1756.5, -2)
    assert p["Ultra High Phenolic Extra Virgin Olive Oil"]["duty"]["kind"] == "in"           # 약 45달러
    assert "과세환율로 바꾼" in p["Ultra High Phenolic Extra Virgin Olive Oil"]["duty"]["text"]
    assert p["Italian Extra Virgin Olive Oil"]["krw_estimate"] is None                         # 원화는 그대로
    assert p["Italian Extra Virgin Olive Oil"]["duty"]["kind"] == "in"                         # 36,000원 ≈ 27달러
    assert data["fx"]["source"].startswith("관세청") and "table" not in data["fx"]


def test_search_item_blocked_does_not_call_shopify():
    http = FakeHttp([product("Aged Cheese")])
    data = service.search_item("dairy", http=http)
    assert data["products"] == [] and not http.calls and data["status"] == "blocked"


def test_caution_item_note_in_checklist():
    data = service.search_item("coffee", http=FakeHttp([product("Roasted Coffee Beans 1kg")]))
    assert data["status"] == "caution" and "생두" in data["note"]
    assert any(s["key"] == "quarantine" and "생두" in s["text"] for s in data["checklist"])


def test_route_item(monkeypatch):
    from fastapi.testclient import TestClient

    from app.main import app

    monkeypatch.setattr(service.catalog, "requests", FakeHttp([product("Extra Virgin Olive Oil")]))
    r = TestClient(app).get("/api/direct/item/olive_oil")
    assert r.status_code == 200 and r.headers["cache-control"] == "no-store" and r.json()["products"]

