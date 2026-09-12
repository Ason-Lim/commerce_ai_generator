"""Behavioral characterization for the preserved legacy compare engine."""

from app.services.recommendation.compare_engine import (
    build_compare_message,
    build_info_chips,
)


def test_build_compare_message_preserves_fallback_and_determinism():
    fallback = build_compare_message({}, priority="trust")
    item = {
        "rating": 4.7,
        "review_count": 500,
        "price_per_100g": 500,
        "discount_rate": 15,
        "brix": 14,
        "is_high_brix": True,
    }
    detailed = build_compare_message(item, priority="trust")

    assert fallback == "가격, 품질, 사용자 반응을 함께 비교했어요"
    assert isinstance(detailed, str)
    assert detailed == build_compare_message(dict(item), priority="trust")
    assert detailed


def test_build_info_chips_preserves_empty_and_ordered_unique_outputs():
    assert build_info_chips({}) == ([], [])

    item = {
        "rating": 4.7,
        "review_count": 500,
        "price_per_100g": 500,
        "discount_rate": 15,
        "brix": 14,
        "is_high_brix": True,
        "seller_name": "주식회사 테스트상점",
        "platform": "쿠팡",
        "display_weight": "500g",
    }
    highlight_chips, normal_chips = build_info_chips(item)
    flattened = highlight_chips + normal_chips

    assert isinstance(highlight_chips, list)
    assert isinstance(normal_chips, list)
    assert (highlight_chips, normal_chips) == build_info_chips(dict(item))
    assert highlight_chips == list(dict.fromkeys(highlight_chips))
    assert normal_chips == list(dict.fromkeys(normal_chips))
    assert flattened
    assert any("⭐" in chip for chip in flattened)
