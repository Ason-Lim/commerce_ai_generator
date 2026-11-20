"""가격 전망·매수 시점 API (2026-11-19 밤) — 합성 history.csv, 외부 호출 없음."""
from __future__ import annotations

import csv
import datetime as dt

import pytest

from app.services.trends.forecast import prices as pr

H = {"X-Access-Token": "test-token"}
AS_OF = dt.date(2026, 11, 19)


@pytest.fixture
def history(tmp_path, monkeypatch):
    p = tmp_path / "history.csv"
    with open(p, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["date", "cls", "country", "category", "item_code", "item_name", "kind_code", "kind_name", "rank_code", "rank", "unit", "price"])
        d = dt.date(2024, 1, 2)
        while d <= AS_OF:
            if d.weekday() < 5:
                price = 6000 if (d.month == 11 and d.day <= 10) else 3500
                w.writerow([d.isoformat(), "01", "1101", "200", "211", "배추", "06", "가을", "04", "상품", "1포기", price])
                w.writerow([d.isoformat(), "01", "1101", "500", "6701", "계란", "01", "XL30구(일반란)", "04", "상품", "30구", 7000])
            d += dt.timedelta(days=1)
    monkeypatch.setattr(pr, "HISTORY", p)
    monkeypatch.delenv("ADMIN_GUEST_TRENDS", raising=False)
    return p


def test_needs_admin(admin_client, history):
    assert admin_client.get("/admin/api/trends/forecast/prices").status_code == 401
    assert admin_client.get("/admin/api/trends/forecast/price?item=배추").status_code == 401


def test_prices_summary(admin_client, history):
    r = admin_client.get("/admin/api/trends/forecast/prices?as_of=2026-11-19", headers=H)
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["ok"] and d["history"]["backfilled"] and d["history"]["last"] == "2026-11-19"
    by = {i["item"]: i for i in d["items"]}
    assert by["배추"]["verdict"] in ("기다리기", "분할", "지금") and by["배추"]["position"]["price"] == 3500
    assert by["계란"]["verdict"] in ("지금", "분할")                 # 평평한 시세 → 전망 0%
    assert by["올리브유"]["verdict"] == "보류" and by["올리브유"]["kamis_item"] is None
    assert [i["verdict"] for i in d["items"]] == sorted((i["verdict"] for i in d["items"]),
                                                        key=lambda v: {"지금": 0, "기다리기": 1, "분할": 2, "보류": 3}[v])
    assert d["thresholds"]["min_years"] == 2


def test_price_detail_curve_and_unknown(admin_client, history):
    r = admin_client.get("/admin/api/trends/forecast/price?item=배추&as_of=2026-11-19", headers=H)
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["kamis"]["item"] == "배추" and d["position"]["date"] == "2026-11-19"
    assert d["curves"].get("event") == "김장 시즌" and "2025" in d["curves"]["years"]
    assert set(d["outlook"]) == {"7", "14", "28"} and d["outlook"]["28"]["n"] == 2
    assert d["domestic"] is None and d["overseas_quotes"] is None
    assert any(x["id"] == "kimjang" for x in d["drivers"])
    assert admin_client.get("/admin/api/trends/forecast/price?item=없는품목", headers=H).status_code == 404


def test_price_overseas_blocked_without_calls(admin_client, history, monkeypatch):
    r = admin_client.get("/admin/api/trends/forecast/price?item=계란&ucp=1", headers=H)
    assert r.status_code == 200
    assert "검역" in r.json()["overseas_quotes"]["blocked"]


def test_price_overseas_quote_with_fake_ucp(admin_client, history, monkeypatch):
    from app.admin import routes

    monkeypatch.setattr(routes, "_domestic_products", lambda kws, limit=8: [{"title": "국내 올리브유 500ml", "price": 20000, "weight_g": 500, "url": "https://x"}])
    monkeypatch.setattr(routes, "_ucp_foreign", lambda q, limit=8: {"variants": [{"title": "EVOO 1L", "currency": "USD", "price": 20.0,
                                                                                  "weight_g": 1000, "host": "shop.example.com", "url": "https://shop.example.com/evoo"}],
                                                                    "errors": []})
    r = admin_client.get("/admin/api/trends/forecast/price?item=올리브유&ucp=1&fx_usd=1400", headers=H)
    assert r.status_code == 200, r.text
    d = r.json()
    q = d["overseas_quotes"]["quotes"][0]
    assert q["ok"] and q["under_de_minimis"] and q["estimate"] and d["overseas_quotes"]["fx"]["USD"] == 1400
    assert d["compare"]["domestic_best"]["per100g"] == 4000 and d["compare"]["overseas_best"]["per100g"] == q["per100g_krw"]
    assert d["compare"]["cheaper"] in ("직구", "국내")
