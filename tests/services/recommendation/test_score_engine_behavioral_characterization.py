"""Behavioral characterization for the preserved legacy score engine."""

import pytest

from app.services.recommendation.score_engine import (
    calculate_ai_scores,
    calculate_hidden_gem_score,
    calculate_mode_score,
    calculate_price_value_score,
    calculate_reaction_trust_score,
    get_brix_value,
    get_cached_identity_validation,
    get_safe_number,
)


@pytest.mark.parametrize(
    ("value", "default", "expected"),
    [
        (None, 7.0, 7.0),
        ("", 6.0, 6.0),
        ("1,234.5", 0.0, 1234.5),
        ("not-a-number", 5.0, 5.0),
        (12, 0.0, 12.0),
    ],
)
def test_get_safe_number_preserves_coercion_and_fallback(value, default, expected):
    assert get_safe_number(value, default) == expected


def test_get_cached_identity_validation_preserves_cached_object_and_mutation():
    cached = {"identity_score": 87.0, "warnings": ["kept"]}
    item = {"_identity_validation": cached}

    result = get_cached_identity_validation(item)

    assert result is cached
    assert item["_identity_validation"] is cached


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


def test_calculate_reaction_trust_score_preserves_signal_monotonicity():
    baseline = calculate_reaction_trust_score({})
    signaled = calculate_reaction_trust_score(
        {
            "final_recommendation_label": "사용자 반응 우수 추천",
            "click_count": 25,
            "ctr_pct": 12,
        }
    )

    assert isinstance(baseline, (int, float))
    assert signaled >= baseline
    assert signaled == calculate_reaction_trust_score(
        {
            "final_recommendation_label": "사용자 반응 우수 추천",
            "click_count": 25,
            "ctr_pct": 12,
        }
    )


def test_calculate_hidden_gem_score_preserves_low_exposure_signal():
    baseline = calculate_hidden_gem_score({})
    candidate = {"impression_count": 100, "click_count": 20, "ctr_pct": 10}
    signaled = calculate_hidden_gem_score(candidate)

    assert isinstance(baseline, (int, float))
    assert signaled >= baseline
    assert signaled == calculate_hidden_gem_score(dict(candidate))


def test_calculate_ai_scores_preserves_shape_priority_and_determinism():
    item = {
        "rating": 4.7,
        "review_count": 500,
        "price_per_100g": 600,
        "discount_rate": 15,
        "click_count": 25,
        "ctr_pct": 12,
        "impression_count": 100,
        "brix": 14,
    }

    result = calculate_ai_scores(dict(item), priority="trust")

    assert isinstance(result, dict)
    assert {"quality", "price", "trust", "popularity", "total"} <= set(result)
    assert result == calculate_ai_scores(dict(item), priority="trust")


def test_calculate_mode_score_preserves_numeric_deterministic_result():
    item = {"impression_count": 100, "click_count": 20, "ctr_pct": 10}
    scores = calculate_ai_scores(dict(item), priority="trust")

    result = calculate_mode_score(item, scores, "trust", search_context=None)

    assert isinstance(result, (int, float))
    assert result == calculate_mode_score(
        dict(item), dict(scores), "trust", search_context=None
    )
