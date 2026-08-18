import pytest

from app.services.recommendation.models import (
    RecommendationPriority,
    RecommendationScoreComponents,
)

from app.services.recommendation.provider import (
    build_score_components,
)

from app.services.recommendation.scoring import (
    calculate_recommendation_score,
)


def test_direct_component_construction_preserves_legacy_availability():
    components = RecommendationScoreComponents(
        quality=80,
    )

    assert components.is_available(
        "quality"
    )

    assert components.is_available(
        "price"
    )

    assert components.is_available(
        "identity"
    )


def test_provider_missing_signal_is_unavailable_not_observed_zero():
    components = build_score_components(
        {
            "food_intelligence_score": 80,
        }
    )

    assert components.quality == 80
    assert components.is_available(
        "quality"
    )

    assert components.price == 0
    assert not components.is_available(
        "price"
    )

    assert components.identity == 0
    assert not components.is_available(
        "identity"
    )


def test_observed_zero_remains_available_evidence():
    components = build_score_components(
        {
            "food_intelligence_score": 80,
            "_canonical_market_score": 0,
        }
    )

    assert components.market == 0
    assert components.is_available(
        "market"
    )


def test_missing_identity_is_not_synthesized_as_100():
    components = build_score_components(
        {}
    )

    assert components.identity != 100
    assert not components.is_available(
        "identity"
    )


def test_mix_weights_are_renormalized_over_available_evidence():
    components = RecommendationScoreComponents(
        quality=80,
        market=60,
        available=frozenset(
            {
                "quality",
                "market",
            }
        ),
    )

    result = calculate_recommendation_score(
        components,
        RecommendationPriority.MIX,
    )

    assert set(
        result.weights
    ) == {
        "quality",
        "market",
    }

    assert sum(
        result.weights.values()
    ) == pytest.approx(
        1.0
    )

    assert result.weights[
        "quality"
    ] == pytest.approx(
        0.75
    )

    assert result.weights[
        "market"
    ] == pytest.approx(
        0.25
    )

    assert result.final_score == 75.0


@pytest.mark.parametrize(
    "priority",
    [
        RecommendationPriority.MIX,
        RecommendationPriority.PRICE,
        RecommendationPriority.QUALITY,
        RecommendationPriority.TRUST,
        RecommendationPriority.EXPLORATION,
        RecommendationPriority.DISCOVERY,
        RecommendationPriority.REVISIT,
    ],
)
def test_effective_weights_sum_to_one_when_evidence_exists(
    priority,
):
    components = RecommendationScoreComponents(
        quality=80,
        price=70,
        available=frozenset(
            {
                "quality",
                "price",
            }
        ),
    )

    result = calculate_recommendation_score(
        components,
        priority,
    )

    assert sum(
        result.weights.values()
    ) == pytest.approx(
        1.0
    )


def test_unavailable_components_receive_no_effective_weight():
    components = RecommendationScoreComponents(
        quality=80,
        trust=100,
        available=frozenset(
            {
                "quality",
            }
        ),
    )

    result = calculate_recommendation_score(
        components,
        RecommendationPriority.TRUST,
    )

    assert set(
        result.weights
    ) == {
        "quality",
    }

    assert result.weights[
        "quality"
    ] == pytest.approx(
        1.0
    )

    assert result.final_score == 80.0


def test_all_signals_unavailable_returns_insufficient_evidence():
    components = RecommendationScoreComponents(
        available=frozenset()
    )

    result = calculate_recommendation_score(
        components,
        RecommendationPriority.MIX,
    )

    assert result.final_score == 0.0
    assert dict(
        result.weights
    ) == {}
    assert result.reason_codes == ()
    assert "insufficient_evidence" in (
        result.warnings
    )


def test_missing_identity_does_not_emit_identity_warning():
    components = RecommendationScoreComponents(
        quality=80,
        identity=0,
        available=frozenset(
            {
                "quality",
            }
        ),
    )

    result = calculate_recommendation_score(
        components,
        RecommendationPriority.MIX,
    )

    assert "identity_warning" not in (
        result.reason_codes
    )

    assert "identity_warning" not in (
        result.warnings
    )


def test_available_low_identity_emits_identity_warning():
    components = RecommendationScoreComponents(
        quality=80,
        identity=20,
        available=frozenset(
            {
                "quality",
                "identity",
            }
        ),
    )

    result = calculate_recommendation_score(
        components,
        RecommendationPriority.MIX,
    )

    assert "identity_warning" in (
        result.reason_codes
    )

    assert "identity_warning" in (
        result.warnings
    )


def test_unavailable_high_signal_does_not_create_reason_code():
    components = RecommendationScoreComponents(
        quality=95,
        price=95,
        trust=95,
        market=95,
        available=frozenset(),
    )

    result = calculate_recommendation_score(
        components,
        RecommendationPriority.MIX,
    )

    assert result.reason_codes == ()


def test_provider_tracks_all_observed_canonical_evidence():
    components = build_score_components(
        {
            "fruit_quality_score": 85,
            "v8_price_score": 70,
            "_canonical_trust_score": 75,
            "_canonical_popularity_score": 60,
            "_canonical_market_score": 65,
            "_canonical_identity_score": 88,
        }
    )

    assert components.available == frozenset(
        {
            "quality",
            "price",
            "trust",
            "popularity",
            "market",
            "identity",
        }
    )


def test_provider_does_not_invent_missing_evidence():
    components = build_score_components(
        {
            "food_intelligence_score": 80,
        }
    )

    assert components.available == frozenset(
        {
            "quality",
        }
    )


def test_scoring_is_deterministic_with_availability():
    components = RecommendationScoreComponents(
        quality=81,
        price=67,
        market=72,
        available=frozenset(
            {
                "quality",
                "price",
                "market",
            }
        ),
    )

    first = calculate_recommendation_score(
        components,
        RecommendationPriority.QUALITY,
    )

    second = calculate_recommendation_score(
        components,
        RecommendationPriority.QUALITY,
    )

    assert first == second


def test_unknown_availability_component_is_rejected():
    with pytest.raises(
        ValueError,
        match="unknown recommendation components",
    ):
        RecommendationScoreComponents(
            available=frozenset(
                {
                    "quality",
                    "unknown_signal",
                }
            )
        )
