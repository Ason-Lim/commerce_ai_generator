"""해외 직구 견적 — UCP 외화 옵션 → 도착 추정가 → 국내 100g당 비교 (2026-11-19 밤). 외부 호출 없음."""
from __future__ import annotations

from app.services.trends.forecast import overseas as ov

FX = {"USD": 1400.0, "EUR": 1500.0, "source": "test", "date": "2026-11-19"}


def test_weight_from_title():
    assert ov.weight_g_from_title("Extra Virgin Olive Oil 500ml") == 500
    assert ov.weight_g_from_title("Whole Bean Coffee 12 oz") == round(12 * 28.35, 1)
    assert ov.weight_g_from_title("Almonds 1 lb x 2") == round(453.6 * 2, 1)
    assert ov.weight_g_from_title("Olive Oil 750ml 2-pack") == 1500
    assert ov.weight_g_from_title("Olive Oil") is None


def test_foreign_variants_keep_only_non_krw_available():
    resp = {"products": [{"id": "p1", "title": "Olive Oil 500ml", "url": "https://shop.example.com/p1",
                          "variants": [{"id": "v1", "title": "Default", "price": {"amount": 2499, "currency": "USD"}},
                                       {"id": "v2", "title": "Case", "price": {"amount": 9999, "currency": "USD"}, "availability": {"available": False}},
                                       {"id": "v3", "title": "KR", "price": {"amount": 35000, "currency": "KRW"}}]}]}
    vs = ov.foreign_variants(resp, "shop.example.com")
    assert [v["variant_id"] for v in vs] == ["v1"]
    assert vs[0]["price"] == 24.99 and vs[0]["weight_g"] == 500 and vs[0]["title"] == "Olive Oil 500ml"


def test_quote_under_threshold_no_tax():
    v = {"title": "Olive Oil 500ml", "currency": "USD", "price": 24.99, "weight_g": 500, "host": "h"}
    q = ov.quote(v, group="수입식품", item="올리브유", fx=FX, origin="US")
    assert q["ok"] and q["allowed"] and q["under_de_minimis"] and q["duty_krw"] == 0 and q["vat_krw"] == 0
    assert q["item_krw"] == round(24.99 * 1400) and q["shipping_krw"] == round((10 + 4) * 1400)
    assert q["total_krw"] == q["item_krw"] + q["shipping_krw"] and q["per100g_krw"] == round(q["total_krw"] / 5)
    assert q["estimate"] and any("200달러" in n for n in q["notes"]) and any("참고 견적" in n for n in q["notes"])


def test_quote_over_threshold_adds_duty_and_vat_and_bundle():
    v = {"title": "Olive Oil 3L", "currency": "EUR", "price": 150.0, "weight_g": 3000}
    q = ov.quote(v, group="수입식품", item="올리브유", fx=FX, origin="ES")       # 150달러 한도 (150유로 ≈ 161달러)
    assert not q["under_de_minimis"] and q["threshold_usd"] == 150
    assert q["duty_krw"] == round((q["item_krw"] + q["shipping_krw"]) * 0.08)
    assert q["vat_krw"] == round((q["item_krw"] + q["shipping_krw"] + (q["item_krw"] + q["shipping_krw"]) * 0.08) * 0.10)
    q2 = ov.quote(v, group="수입식품", item="올리브유", fx=FX, origin="ES", fta=True)
    assert q2["duty_krw"] == 0 and q2["vat_krw"] > 0                            # FTA 0% 라도 부가세는 남음
    small = {"title": "Olive Oil 500ml", "currency": "USD", "price": 30.0, "weight_g": 500}
    assert ov.quote(small, group="수입식품", item="올리브유", fx=FX, bundle_usd=180)["under_de_minimis"] is False  # 합산


def test_quote_blocked_groups_and_missing_fx():
    v = {"title": "Lamb chops 1kg", "currency": "USD", "price": 40.0, "weight_g": 1000}
    q = ov.quote(v, group="축산", item="양고기", fx=FX)
    assert q["ok"] is False and q["allowed"] is False and "검역" in q["reason"]
    assert ov.quote(v, group="축산가공", item="치즈·버터", fx=FX)["allowed"] is False
    q2 = ov.quote({"title": "Coffee 1kg", "currency": "GBP", "price": 20.0, "weight_g": 1000}, group="수입식품", item="커피 원두", fx=FX)
    assert q2["ok"] is False and q2["allowed"] is True and "환율" in q2["reason"]


def test_compare_per100g_only():
    quotes = [ov.quote({"title": "Olive Oil 1L", "currency": "USD", "price": 20.0, "weight_g": 1000}, group="수입식품", item="올리브유", fx=FX),
              {"ok": False, "reason": "x"}]
    domestic = [{"title": "국산몰 올리브유 500ml", "price": 30000, "weight_g": 500, "url": "u"},
                {"title": "중량 미상", "price": 9000}]
    c = ov.compare(quotes, domestic)
    assert c["n_domestic"] == 1 and c["n_overseas"] == 1
    assert c["domestic_best"]["per100g"] == 6000 and c["overseas_best"]["per100g"] == quotes[0]["per100g_krw"]
    assert c["cheaper"] == "직구" and c["diff_pct"] < 0
    assert ov.compare([], [])["diff_pct"] is None
