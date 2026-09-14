"""Behavioral characterization for the preserved legacy score engine."""

import pytest

from app.services.recommendation import (
    calculate_ai_scores,
    calculate_hidden_gem_score,
    calculate_mode_score,
    calculate_price_value_score,
    calculate_reaction_trust_score,
    get_brix_value,
)


@pytest.mark.parametrize(
    ("field", "value", "expected"),
    [('click_count', 0.0, 0),
 ('click_count', 1.0, 6),
 ('click_count', 2.0, 6),
 ('click_count', 3.0, 12),
 ('click_count', 4.0, 12),
 ('click_count', 5.0, 18),
 ('click_count', 6.0, 18),
 ('click_count', 9.0, 18),
 ('click_count', 10.0, 25),
 ('click_count', 11.0, 25),
 ('ctr_pct', 0.0, 0),
 ('ctr_pct', 1.0, 5),
 ('ctr_pct', 2.0, 5),
 ('ctr_pct', 3.0, 10),
 ('ctr_pct', 4.0, 10),
 ('ctr_pct', 5.0, 18),
 ('ctr_pct', 6.0, 18),
 ('ctr_pct', 9.0, 18),
 ('ctr_pct', 10.0, 25),
 ('ctr_pct', 11.0, 25)],
)
def test_reaction_entrypoint_preserves_safe_number_fallback_indirectly(field, value, expected):
    item = {field: value}
    before = dict(item)

    assert calculate_reaction_trust_score(item) == expected
    assert item == before
    assert calculate_reaction_trust_score(dict(item)) == expected


def test_mode_entrypoint_preserves_identity_cache_contract_indirectly():
    miss_item = {"title": "관찰용 상품", "name": "관찰용 상품"}
    miss_scores = calculate_ai_scores(dict(miss_item), priority="trust")
    before_miss = dict(miss_item)
    miss_result = calculate_mode_score(miss_item, miss_scores, "trust", search_context=None)

    assert isinstance(miss_result, (int, float))
    assert miss_result == calculate_mode_score(dict(miss_item), dict(miss_scores), "trust", search_context=None)
    assert miss_item == before_miss
    assert "_identity_validation" not in miss_item

    cached = {"identity_score": 87.0, "warnings": ["kept"]}
    cached_item = {"_identity_validation": cached}
    cached_scores = calculate_ai_scores(dict(cached_item), priority="trust")
    cached_result = calculate_mode_score(cached_item, cached_scores, "trust", search_context=None)

    assert isinstance(cached_result, (int, float))
    assert cached_result == calculate_mode_score(cached_item, dict(cached_scores), "trust", search_context=None)
    assert cached_item["_identity_validation"] is cached
    assert cached_item == {"_identity_validation": cached}


@pytest.mark.parametrize(
    ("price_per_100g", "expected"),
    [(0, 0), (400, 90), (401, 80), (600, 80), (1501, 15)],
)
def test_calculate_price_value_score_preserves_thresholds(price_per_100g, expected):
    assert calculate_price_value_score({"price_per_100g": price_per_100g}) == expected


def test_get_brix_value_preserves_direct_and_text_fallbacks():
    assert get_brix_value({"brix": 12.5}) == 12.5
    assert get_brix_value({"title": "프리미엄 과일 당도 14 brix"}) == 14.0
    assert get_brix_value({}) == 0


def test_calculate_reaction_trust_score_preserves_exact_values_and_boundaries():
    signaled = {"final_recommendation_label": "사용자 반응 우수 추천", "click_count": 25, "ctr_pct": 12}
    assert calculate_reaction_trust_score({}) == 0
    assert calculate_reaction_trust_score(dict(signaled)) == 45
    assert calculate_reaction_trust_score(dict(signaled)) == 45
    for field, value, expected in [('click_count', 0.0, 0),
 ('click_count', 1.0, 6),
 ('click_count', 2.0, 6),
 ('click_count', 3.0, 12),
 ('click_count', 4.0, 12),
 ('click_count', 5.0, 18),
 ('click_count', 6.0, 18),
 ('click_count', 9.0, 18),
 ('click_count', 10.0, 25),
 ('click_count', 11.0, 25),
 ('ctr_pct', 0.0, 0),
 ('ctr_pct', 1.0, 5),
 ('ctr_pct', 2.0, 5),
 ('ctr_pct', 3.0, 10),
 ('ctr_pct', 4.0, 10),
 ('ctr_pct', 5.0, 18),
 ('ctr_pct', 6.0, 18),
 ('ctr_pct', 9.0, 18),
 ('ctr_pct', 10.0, 25),
 ('ctr_pct', 11.0, 25)]:
        item = {field: value}
        before = dict(item)
        assert calculate_reaction_trust_score(item) == expected
        assert item == before


def test_calculate_hidden_gem_score_preserves_exact_values_and_boundaries():
    candidate = {"impression_count": 100, "click_count": 20, "ctr_pct": 10}
    assert calculate_hidden_gem_score({}) == 0
    assert calculate_hidden_gem_score(dict(candidate)) == 90
    assert calculate_hidden_gem_score(dict(candidate)) == 90
    for field, value, expected in [('impression_count', 0.0, 0),
 ('impression_count', 1.0, 0),
 ('impression_count', 2.0, 0),
 ('impression_count', 3.0, 0),
 ('impression_count', 4.0, 0),
 ('impression_count', 5.0, 0),
 ('impression_count', 6.0, 0),
 ('impression_count', 9.0, 0),
 ('impression_count', 10.0, 15),
 ('impression_count', 11.0, 15),
 ('impression_count', 19.0, 15),
 ('impression_count', 20.0, 15),
 ('impression_count', 21.0, 15),
 ('impression_count', 29.0, 15),
 ('impression_count', 30.0, 25),
 ('impression_count', 31.0, 25),
 ('impression_count', 149.0, 25),
 ('impression_count', 150.0, 25),
 ('impression_count', 151.0, 10),
 ('impression_count', 299.0, 10),
 ('impression_count', 300.0, 10),
 ('impression_count', 301.0, 0),
 ('click_count', 0.0, 0),
 ('click_count', 1.0, 15),
 ('click_count', 2.0, 15),
 ('click_count', 3.0, 25),
 ('click_count', 4.0, 25),
 ('click_count', 5.0, 30),
 ('click_count', 6.0, 30),
 ('click_count', 9.0, 30),
 ('click_count', 10.0, 35),
 ('click_count', 11.0, 35),
 ('click_count', 19.0, 35),
 ('click_count', 20.0, 35),
 ('click_count', 21.0, 35),
 ('click_count', 29.0, 35),
 ('click_count', 30.0, 35),
 ('click_count', 31.0, 35),
 ('click_count', 149.0, 35),
 ('click_count', 150.0, 35),
 ('click_count', 151.0, 35),
 ('click_count', 299.0, 35),
 ('click_count', 300.0, 35),
 ('click_count', 301.0, 35),
 ('ctr_pct', 0.0, 0),
 ('ctr_pct', 1.0, 0),
 ('ctr_pct', 2.0, 0),
 ('ctr_pct', 3.0, 10),
 ('ctr_pct', 4.0, 10),
 ('ctr_pct', 5.0, 20),
 ('ctr_pct', 6.0, 20),
 ('ctr_pct', 9.0, 20),
 ('ctr_pct', 10.0, 30),
 ('ctr_pct', 11.0, 30),
 ('ctr_pct', 19.0, 30),
 ('ctr_pct', 20.0, 40),
 ('ctr_pct', 21.0, 40),
 ('ctr_pct', 29.0, 40),
 ('ctr_pct', 30.0, 40),
 ('ctr_pct', 31.0, 40),
 ('ctr_pct', 149.0, 40),
 ('ctr_pct', 150.0, 40),
 ('ctr_pct', 151.0, 40),
 ('ctr_pct', 299.0, 40),
 ('ctr_pct', 300.0, 40),
 ('ctr_pct', 301.0, 40)]:
        item = {field: value}
        before = dict(item)
        assert calculate_hidden_gem_score(item) == expected
        assert item == before


def test_calculate_ai_scores_preserves_exact_supported_priority_contrast():
    item = {"rating": 4.7, "review_count": 500, "price_per_100g": 600, "discount_rate": 15,
            "click_count": 25, "ctr_pct": 12, "impression_count": 100, "brix": 14}
    expected_by_priority = {'price': {'popularity': 0, 'price': 90, 'quality': 72, 'total': 72.0, 'trust': 86},
 'quality': {'popularity': 0, 'price': 90, 'quality': 72, 'total': 56.7, 'trust': 86},
 'trust': {'popularity': 0, 'price': 90, 'quality': 72, 'total': 39.6, 'trust': 86}}
    assert set(expected_by_priority) == {'trust', 'price', 'quality'}
    assert len({repr(value) for value in expected_by_priority.values()}) == 3
    for priority, expected in expected_by_priority.items():
        candidate = dict(item)
        assert calculate_ai_scores(candidate, priority=priority) == expected
        assert candidate == item
        assert calculate_ai_scores(dict(item), priority=priority) == expected


def test_calculate_mode_score_preserves_numeric_deterministic_result():
    item = {"impression_count": 100, "click_count": 20, "ctr_pct": 10}
    scores = calculate_ai_scores(dict(item), priority="trust")

    result = calculate_mode_score(item, scores, "trust", search_context=None)

    assert isinstance(result, (int, float))
    assert result == calculate_mode_score(
        dict(item), dict(scores), "trust", search_context=None
    )
