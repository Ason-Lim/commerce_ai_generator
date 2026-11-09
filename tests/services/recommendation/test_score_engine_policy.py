"""score_engine 정책·버그 수정 회귀 테스트 (2026-11-09 리팩터링)."""

import pytest

from app.services.recommendation import score_engine as se
from app.services.recommendation import calculate_ai_scores, calculate_mode_score

BASE = {
    "rating": 4.9,
    "review_count": 12000,
    "price_per_100g": 600,
    "brix": 14,
    "click_count": 0,
    "ctr_pct": 0,
}


# --- 평점·리뷰 점수 제외 정책 -------------------------------------------------

def test_unverified_rating_is_excluded_by_default():
    with_rating = calculate_ai_scores(dict(BASE), priority="trust")
    without_rating = calculate_ai_scores(
        {k: v for k, v in BASE.items() if k not in ("rating", "review_count")},
        priority="trust",
    )
    assert with_rating == without_rating
    assert with_rating["trust"] == 0


@pytest.mark.parametrize("flag", [None, False, "true", 1, "yes"])
def test_only_literal_true_flag_opens_rating(flag):
    item = dict(BASE, rating_score_usable=flag)
    assert se.rating_signals_usable(item) is False
    assert calculate_ai_scores(item)["trust"] == 0


def test_verified_rating_is_used_when_flagged():
    scores = calculate_ai_scores(dict(BASE, rating_score_usable=True), priority="trust")
    # 35(평점) + 35(리뷰) + 20(조합) = 90
    assert scores["trust"] == 90


def test_scraped_source_marker_does_not_open_rating():
    item = dict(BASE, review_source="kurly_page")
    assert calculate_ai_scores(item)["trust"] == 0
    info = se.explain_score_inputs(item)
    assert info["rating_used"] is False
    assert info["excluded"][0]["source"] == "kurly_page"


def test_affiliate_flag_has_no_effect_on_scores():
    plain = calculate_ai_scores(dict(BASE), priority="price")
    for key in ("is_affiliate", "affiliate", "coupang_partners", "commission_rate"):
        assert calculate_ai_scores(dict(BASE, **{key: True}), priority="price") == plain


# --- 상한·합계 일관성 ---------------------------------------------------------

def test_component_scores_are_capped_at_100():
    item = dict(BASE, rating_score_usable=True, brix=18,
                discount_rate=20, price_drop_boost=10, price_per_100g=300)
    scores = calculate_ai_scores(item, priority="quality")
    for key in ("quality", "trust", "price", "popularity"):
        assert 0 <= scores[key] <= 100


def test_total_uses_capped_components():
    item = dict(BASE, discount_rate=20, price_drop_boost=10, price_per_100g=300)
    scores = calculate_ai_scores(item, priority="price")
    expected = scores["quality"] * 0.25 + scores["price"] * 0.60 + scores["popularity"] * 0.15
    assert scores["price"] == 100
    assert scores["total"] == round(expected, 1)


@pytest.mark.parametrize("priority", ["price", "quality", "trust"])
def test_adaptive_priority_uses_same_total_weights(priority):
    item = dict(BASE, discount_rate=10)
    assert (
        calculate_ai_scores(dict(item), priority=f"{priority}_adaptive")["total"]
        == calculate_ai_scores(dict(item), priority=priority)["total"]
    )


# --- 버그 수정 ----------------------------------------------------------------

def test_exploration_mode_no_longer_raises():
    item = {"impression_count": 0, "click_count": 0}
    scores = calculate_ai_scores(dict(item), priority="exploration")
    result = calculate_mode_score(item, scores, "exploration")
    # novelty 35 + 15 = 50 → 50 * 0.35
    assert result == pytest.approx(scores["quality"] * 0.55 + 50 * 0.35 + scores["price"] * 0.10)


def test_novelty_matches_streamlit_formula():
    assert se.calculate_novelty_score({}) == 50
    assert se.calculate_novelty_score({"impression_count": 5, "click_count": 1, "ctr_pct": 12}) == 63
    assert se.calculate_novelty_score({"impression_count": 999, "click_count": 9,
                                       "recommendation_mode": "exploration"}) == 20


def test_cached_zero_confidence_stays_zero():
    v = se.get_cached_identity_validation({"_brix_confidence": 0, "_price_confidence": "0"})
    assert v["brix_confidence"] == 0
    assert v["price_confidence"] == 0
    assert v["identity_score"] == 50  # 값이 없을 때만 중립 50


def test_bad_cached_values_do_not_raise():
    v = se.get_cached_identity_validation({"_identity_score": "n/a"})
    assert v["identity_score"] == 50


def test_dict_search_context_trend_boost_is_applied():
    scores = {"quality": 50, "trust": 50, "price": 50, "popularity": 0}
    base = calculate_mode_score({}, scores, "mix")
    assert calculate_mode_score({}, scores, "mix", {"trend_boost": 5}) == base + 5
    assert calculate_mode_score({}, scores, "mix", {"trend_boost": "x"}) == base


def test_string_numbers_do_not_raise():
    item = {"price_drop_boost": "7", "ctr_pct": "25", "ctr_feedback_boost": "8",
            "click_count": "1,200", "price_per_100g": "550"}
    scores = calculate_ai_scores(item)
    assert scores["price"] == 95  # 80 + 15
    assert scores["popularity"] == 50  # 30 + 20


# --- 근거 표시 ----------------------------------------------------------------

def test_explain_score_inputs_reports_version_and_no_affiliate_bonus():
    info = se.explain_score_inputs({"brix": 15})
    assert info["score_engine_version"] == se.SCORE_ENGINE_VERSION
    assert info["affiliate_bonus"] is False
    assert info["excluded"] == []
    assert info["brix_value"] == 15
