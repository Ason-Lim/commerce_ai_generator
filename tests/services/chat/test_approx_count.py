"""2026-11-20: '천수무 5kg 3~7개 내외' — 대략의 낱개 수는 개수가 아니고, 1kg 이상 상자의 중량은 상자 전체다."""
import pytest

from app.services.chat import explain


def _card(title, price=14290):
    return explain.enrich({"key": "a", "title": title, "price": price}, {"product_name": title, "price": price})


@pytest.mark.parametrize("title,grams", [
    ("단단하고 아삭한 국내산 천수무 5kg 3~7개 내외, 1박스, 5kg, 5000g", 5000),
    ("배 5kg 8개 내외", 5000),
    ("사과 3kg 10~13과", 3000),
    ("감자 10kg 20개 정도", 10000),
])
def test_box_weight_kept_and_range_is_not_a_count(title, grams):
    c = _card(title)
    assert c["weight_g"] == grams and c["per100g"] is not None
    assert c["unit_count"] is None and c["per_unit"] is None       # '개당 2,041원' 같은 값을 만들지 않음


@pytest.mark.parametrize("title", ["만두 30g 10~12개", "우유 200ml 10~12개"])
def test_small_pieces_with_range_stay_unknown(title):
    c = _card(title)
    assert c.get("weight_g") is None and c.get("volume_ml") is None and c.get("per_unit") is None


def test_exact_count_rules_unchanged():
    assert _card("무 3개입 1박스")["unit_count"] == 3
    c = _card("사과 3kg 10개")
    assert c["weight_g"] is None and c["unit_count"] == 10           # p33 그대로 (정확한 개수는 개당·전체 불명)


def test_minimum_weight_box_stays_unknown():
    """'3kg이상'은 최소 중량 — 실제 중량을 몰라 100g당을 만들지 않는다 (11-20 d10: 선물세트가 '가정용 양' 1위로 올라옴)."""
    c = _card("고당도 사과 선물세트 3kg이상(10-12입/특품)")
    assert c["weight_g"] is None and c["per100g"] is None and c["per_unit"] is None
