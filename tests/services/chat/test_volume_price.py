"""2026-11-12: 액체 상품 100ml당 가격 — 용량끼리만 견주고, 중량(g)과 섞지 않는다."""
from app.services.chat import explain
from app.services.commerce import price_claims


def _card(title, price):
    return explain.enrich({"title": title, "price": price, "mall": "쿠팡", "shipping_fee": None, "total": None}, {})


def test_volume_parsing_follows_weight_rules():
    pv = explain.parse_volume
    assert pv("서울우유 1급A우유 900mL")["volume"] == 900
    assert pv("서울우유 2.3L")["volume"] == 2300
    assert pv("삼다수 2L x 6") == {"volume": 12000, "kind": "multiplied", "formula": "2L×6", "found": ["12L"]}
    # 쿠팡 '용량, 수량' 표기
    assert pv("매일유업 소화가잘되는우유 오리지널, 190ml, 12개")["volume"] == 2280
    assert pv("매일우유 멸균우유 오리지널, 1L, 2개")["formula"] == "1L×2"
    # 쓰지 않는 경우: 곱하기 없는 개수 · 서로 다른 용량 · 증정 · 중량 표기 함께 · 표기 없음
    assert pv("생수 500ml 20병")["volume"] == 10000           # 포장 단위 수는 곱함 (2026-11-12)
    for title, kind in [("생수 500ml 20개", "count_unclear"), ("간장 1.8L 500ml", "ambiguous"),
                        ("1+1 우유 1L", "bonus"), ("사골 500g 국물 1L", "has_weight"), ("곰곰 신선한 1A 우유", "none")]:
        got = pv(title)
        assert got["volume"] is None and got["kind"] == kind, title


def test_card_gets_per100ml_and_never_per100g_from_volume():
    c = _card("매일우유 멸균우유 오리지널, 1L, 2개", 7510)
    assert (c["volume_ml"], c["per100ml"], c["weight_g"], c["per100g"]) == (2000, 376, None, None)


def test_weight_wins_when_title_has_both():
    c = _card("사골곰탕 500g 국물 1L", 5000)
    assert c["per100g"] == 1000 and c.get("per100ml") is None


def test_value_role_compares_volume_only_among_liquids():
    cards = [_card("우유 오리지널, 190ml, 12개", 12900), _card("곰곰 신선한 1A 우유", 3690),
             _card("멸균우유 오리지널, 1L, 2개", 7510)]
    picked = explain.choose(cards, ask="우유")
    value = picked["picks"][0]
    assert value["role"] == "value" and value["title"].startswith("멸균우유")
    assert "100ml당 가장 저렴" in value["why"][0]["text"]
    assert explain.criteria_line(picked["picks"], None) == "100ml당 가격"


def test_weight_comparison_unchanged_when_weights_exist():
    cards = [_card("사과 5kg", 25000), _card("사과 3kg", 17000), _card("사과즙 1L, 2개", 9000)]
    value = next(p for p in explain.choose(cards, ask="사과")["picks"] if p["role"] == "value")
    assert "100g당" in value["why"][0]["text"]                     # 액체(사과즙)와 섞지 않고 중량끼리


def test_blocked_cards_drop_volume():
    c = explain.enrich({"title": "우유 1L, 2개", "price": 5000, "price_compare_blocked": True}, {})
    assert c.get("volume_ml") is None and c.get("per100ml") is None


def test_stale_price_strips_per100ml_part_too():
    assert price_claims.PER100G_PART.sub("", "2L, 100ml당 376원 (상품명 표기)") == "2L (상품명 표기)"
    assert price_claims.CLAIM.search("멸균우유와 100ml당 가격이 같아요")
