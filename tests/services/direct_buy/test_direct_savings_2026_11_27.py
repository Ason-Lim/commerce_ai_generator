"""2026-11-27 직구 '약 n% 저렴' 추정 — 같은 단위·15% 이상일 때만, 국내 기준은 대화 후보 중간값(저장 안 함)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.services.chat.service import direct_buy_block
from app.services.direct_buy import items, savings, service
from tests.services.direct_buy.test_direct_buy_2026_11_26 import FakeHttp, product

FX = {"rate": 1333.88, "source": "관세청 과세환율(수입)", "date": "2026-11-22", "kind": "customs", "stale": False,
      "table": {"USD": 1333.88, "GBP": 1756.5, "KRW": 1.0}}


@pytest.fixture(autouse=True)
def env(monkeypatch):
    for k in ("DIRECT_IN_CHAT", "SHOPIFY_CATALOG"):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setattr(service, "_fx", lambda: dict(FX))


@pytest.mark.parametrize("title,want", [
    ("Extra Virgin Olive Oil 500ml", (500.0, "ml")), ("Olive Oil 16.9 fl oz", (499.7, "ml")), ("Maple Syrup 1L", (1000.0, "ml")),
    ("Dark Chocolate 100g x 3", (300.0, "g")), ("Sea Salt 8.5 oz", (241.0, "g")), ("Olive Oil (Pack of 2) 750ml", (1500.0, "ml")),
    ("Olive Oil Gift Set", None),
])
def test_amount(title, want):
    assert savings.amount(title) == want


def test_domestic_ref_median_and_unit():
    picks = [{"per100ml": 1980}, {"per100ml": 3000}, {"per100ml": 2500}, {"per100g": 999}]
    assert savings.domestic_ref(picks) == {"per100": 2500, "unit": "ml", "n": 3}
    assert savings.domestic_ref([{"price": 1}]) is None


def test_estimate_only_when_cheaper_by_15pct_same_unit():
    ref = {"per100": 5000, "unit": "ml", "n": 3}
    # 500ml 15달러 → 20,008원 + 배송 14달러(18,674원) → 약 7,740원/100ml → 국내보다 비쌈
    assert savings.estimate("Olive Oil 500ml", 20008, ref, 1333.88) is None
    # 1L 20달러 → 26,678원 + 배송 18달러(24,010원) = 50,688 → 5,069원/100ml → 국내 5,000 보다 비쌈
    assert savings.estimate("Olive Oil 1L", 26678, ref, 1333.88) is None
    cheap = savings.estimate("Olive Oil 3L", 40000, ref, 1333.88)       # 40,000 + 34달러(45,352) = 85,352 → 2,845원/100ml
    assert cheap["pct"] == 40 and cheap["unit"] == "ml" and cheap["taxed"] is False
    assert savings.estimate("Olive Oil 3kg", 40000, ref, 1333.88) is None      # g 와 ml 는 견주지 않음
    assert savings.estimate("Olive Oil", 40000, ref, 1333.88) is None


def test_estimate_adds_duty_and_vat_over_de_minimis():
    land = savings.landed(300_000, 1000, 1333.88, label="올리브유")
    assert land["over"] and land["tax"] > 0 and land["total"] > 300_000 + land["ship"]


@pytest.mark.parametrize("args,ok", [(("2500", "ml", "3"), True), (("x", "ml", "3"), False), (("2500", "kg", "3"), False),
                                     (("0", "g", "1"), False), ((None, None, None), False)])
def test_parse_ref(args, ok):
    assert (savings.parse_ref(*args) is not None) is ok


def test_search_item_marks_saving_and_summary():
    big = product("Spanish Extra Virgin Olive Oil 3L", cents=2999)          # 29.99달러 → 약 40,000원
    big["variants"][0]["title"] = "Default Title"
    small = product("Arbequina Extra Virgin Olive Oil 500ml", cents=2499, url="https://s.example/p")
    data = service.search_item("olive_oil", http=FakeHttp([big, small]), ref={"per100": 5000, "unit": "ml", "n": 4})
    by = {p["title"]: p for p in data["products"]}
    assert by["Spanish Extra Virgin Olive Oil 3L"]["saving"]["pct"] >= 15
    assert by["Arbequina Extra Virgin Olive Oil 500ml"]["saving"] is None
    assert data["compare"]["best"]["pct"] == by["Spanish Extra Virgin Olive Oil 3L"]["saving"]["pct"]
    assert "쿠팡 추천 후보 4개" in data["compare"]["basis"] and "100ml" in data["compare"]["basis"]


def test_option_size_wins_over_title():
    p = product("Olive Oil Tin", cents=2999)
    p["variants"][0]["title"] = "3L"
    data = service.search_item("olive_oil", http=FakeHttp([p]), ref={"per100": 5000, "unit": "ml", "n": 2})
    assert data["products"][0]["option"] == "3L" and data["products"][0]["saving"]["pct"] >= 15


def test_search_item_without_ref_has_no_compare():
    data = service.search_item("olive_oil", http=FakeHttp([product("Olive Oil 3L", cents=2999)]))
    assert data["compare"] is None and data["products"][0]["saving"] is None


def test_chat_block_carries_domestic_ref_only():
    picks = [{"per100ml": 1980, "title": "x", "price": 19800}, {"per100ml": 2400, "title": "y", "price": 12000}]
    blk = direct_buy_block("올리브유", "올리브유 추천해줘", picks)
    assert blk["data"]["domestic"] == {"per100": 2190, "unit": "ml", "n": 2}
    assert set(blk["data"]) == {"key", "label", "status", "domestic", "compare"}
    assert [r["per100"] for r in blk["data"]["compare"]] == [1980, 2400] and blk["data"]["compare"][0]["unit"] == "ml"


def test_compare_rows_carry_go_link_with_session():
    picks = [{"key": "k1", "rank": 1, "title": "올리브유 1L", "price": 19800, "per100ml": 1980}]
    blk = direct_buy_block("올리브유", "올리브유 추천해줘", picks, "sid123")
    assert blk["data"]["compare"][0]["go"] == "/go/sid123/k/k1"


def test_quote_for_every_readable_product():
    q = savings.quote("ATLAS Olive Oil 16,9 OZ (500 ML)", 28000, 1333.88)
    assert q["unit"] == "ml" and q["qty"] == 500 and q["landed_krw"] == 46700 and q["per100"] == 9330 and not q["taxed"]
    assert savings.quote("Olive Oil", 28000, 1333.88) is None


def test_search_item_adds_landed_for_compare_table():
    data = service.search_item("olive_oil", http=FakeHttp([product("Olive Oil 1L", cents=2000)]))
    assert data["products"][0]["landed"]["unit"] == "ml"


def test_route_passes_ref(monkeypatch):
    from app.main import app
    seen = {}
    monkeypatch.setattr(service, "search_item", lambda key, ref=None, **k: seen.update(key=key, ref=ref) or {"ok": True})
    r = TestClient(app).get("/api/direct/item/olive_oil?ref=2500&unit=ml&n=3")
    assert r.status_code == 200 and seen == {"key": "olive_oil", "ref": {"per100": 2500, "unit": "ml", "n": 3}}


@pytest.mark.parametrize("text,key", [("사과식초 추천", "vinegar"), ("소금 추천", "salt"), ("땅콩버터 추천", "nut_butter"),
                                      ("아보카도오일", "avocado_oil"), ("프로틴바 추천", "bar"), ("스테비아", "sweetener"),
                                      ("프로틴 파우더 추천", "protein")])
def test_new_items(text, key):
    assert items.match(text.split()[0], text).key == key


@pytest.mark.parametrize("text", ["소금빵 추천", "버터 추천", "아보카도 추천", "고구마 추천"])
def test_new_items_do_not_catch_ordinary(text):
    assert items.match(text.split()[0], text) is None
