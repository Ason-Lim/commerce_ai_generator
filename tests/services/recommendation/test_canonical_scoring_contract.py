from app.services.recommendation.models import (
    RecommendationPriority,
    RecommendationScoreComponents,
)

from app.services.recommendation.scoring import (
    MIX_WEIGHTS,
    PRICE_WEIGHTS,
    QUALITY_WEIGHTS,
    TRUST_WEIGHTS,
    build_reason_codes,
    calculate_recommendation_score,
    clamp_score,
    get_priority_weights,
    normalize_components,
)


def test_canonical_weight_table_matches_v8_characterization() -> None:
    assert dict(QUALITY_WEIGHTS) == {
        "quality": 0.55,
        "price": 0.15,
        "trust": 0.15,
        "popularity": 0.05,
        "market": 0.05,
        "identity": 0.05,
    }

    assert dict(PRICE_WEIGHTS) == {
        "quality": 0.10,
        "price": 0.55,
        "trust": 0.10,
        "popularity": 0.05,
        "market": 0.05,
        "identity": 0.15,
    }

    assert dict(TRUST_WEIGHTS) == {
        "quality": 0.15,
        "price": 0.10,
        "trust": 0.40,
        "popularity": 0.10,
        "market": 0.05,
        "identity": 0.20,
    }

    assert dict(MIX_WEIGHTS) == {
        "quality": 0.30,
        "price": 0.25,
        "trust": 0.15,
        "popularity": 0.10,
        "market": 0.10,
        "identity": 0.10,
    }


def test_canonical_priorities_select_expected_weights() -> None:
    assert get_priority_weights(
        RecommendationPriority.QUALITY
    ) is QUALITY_WEIGHTS

    assert get_priority_weights(
        RecommendationPriority.PRICE
    ) is PRICE_WEIGHTS

    assert get_priority_weights(
        RecommendationPriority.TRUST
    ) is TRUST_WEIGHTS

    assert get_priority_weights(
        RecommendationPriority.MIX
    ) is MIX_WEIGHTS


def test_exploration_discovery_and_revisit_retain_mix_weights() -> None:
    assert get_priority_weights(
        RecommendationPriority.EXPLORATION
    ) is MIX_WEIGHTS

    assert get_priority_weights(
        RecommendationPriority.DISCOVERY
    ) is MIX_WEIGHTS

    assert get_priority_weights(
        RecommendationPriority.REVISIT
    ) is MIX_WEIGHTS


def test_clamp_score_matches_v8_range_behavior() -> None:
    assert clamp_score(-50) == 0.0
    assert clamp_score(0) == 0.0
    assert clamp_score(50.04) == 50.0
    assert clamp_score(50.06) == 50.1
    assert clamp_score(100) == 100.0
    assert clamp_score(500) == 100.0


def test_normalize_components_clamps_each_axis() -> None:
    normalized = normalize_components(
        RecommendationScoreComponents(
            quality=500,
            price=-20,
            trust=70,
            popularity=110,
            market=65,
            identity=-1,
        )
    )

    assert normalized == RecommendationScoreComponents(
        quality=100.0,
        price=0.0,
        trust=70.0,
        popularity=100.0,
        market=65.0,
        identity=0.0,
    )


def test_mix_score_matches_characterized_component_sensitivity() -> None:
    cases = {
        "quality": (
            RecommendationScoreComponents(quality=100),
            30.0,
        ),
        "price": (
            RecommendationScoreComponents(price=100),
            25.0,
        ),
        "trust": (
            RecommendationScoreComponents(trust=100),
            15.0,
        ),
        "popularity": (
            RecommendationScoreComponents(popularity=100),
            10.0,
        ),
        "market": (
            RecommendationScoreComponents(market=100),
            10.0,
        ),
        "identity": (
            RecommendationScoreComponents(identity=100),
            10.0,
        ),
    }

    for components, expected in cases.values():
        result = calculate_recommendation_score(
            components,
            RecommendationPriority.MIX,
        )

        assert result.final_score == expected


def test_quality_score_matches_characterized_weighting() -> None:
    result = calculate_recommendation_score(
        RecommendationScoreComponents(
            quality=100,
        ),
        RecommendationPriority.QUALITY,
    )

    assert result.final_score == 55.0


def test_price_score_matches_characterized_weighting() -> None:
    result = calculate_recommendation_score(
        RecommendationScoreComponents(
            price=100,
        ),
        RecommendationPriority.PRICE,
    )

    assert result.final_score == 55.0


def test_trust_score_matches_characterized_weighting() -> None:
    result = calculate_recommendation_score(
        RecommendationScoreComponents(
            trust=100,
        ),
        RecommendationPriority.TRUST,
    )

    assert result.final_score == 40.0


def test_equal_components_produce_equal_final_score() -> None:
    components = RecommendationScoreComponents(
        quality=50,
        price=50,
        trust=50,
        popularity=50,
        market=50,
        identity=50,
    )

    for priority in RecommendationPriority:
        result = calculate_recommendation_score(
            components,
            priority,
        )

        assert result.final_score == 50.0


def test_reason_code_thresholds_match_v8_characterization() -> None:
    codes = build_reason_codes(
        RecommendationScoreComponents(
            quality=80,
            price=75,
            trust=70,
            popularity=0,
            market=70,
            identity=44,
        )
    )

    assert codes == (
        "high_quality",
        "good_price",
        "high_trust",
        "identity_warning",
        "market_interest",
    )


def test_identity_warning_is_machine_readable_result_evidence() -> None:
    result = calculate_recommendation_score(
        RecommendationScoreComponents(
            identity=44,
        ),
    )

    assert "identity_warning" in result.reason_codes
    assert result.warnings == (
        "identity_warning",
    )


def test_identity_at_threshold_is_not_warning() -> None:
    result = calculate_recommendation_score(
        RecommendationScoreComponents(
            identity=45,
        ),
    )

    assert "identity_warning" not in result.reason_codes
    assert result.warnings == ()


def test_canonical_scoring_does_not_mutate_input() -> None:
    components = RecommendationScoreComponents(
        quality=80,
        price=70,
        trust=60,
        popularity=50,
        market=40,
        identity=90,
    )

    before = components

    calculate_recommendation_score(
        components,
        RecommendationPriority.MIX,
    )

    assert components == before


def test_canonical_score_result_uses_canonical_models() -> None:
    result = calculate_recommendation_score(
        RecommendationScoreComponents(
            quality=80,
            price=70,
            trust=60,
            popularity=50,
            market=40,
            identity=90,
        ),
        RecommendationPriority.MIX,
    )

    assert result.priority is RecommendationPriority.MIX
    assert isinstance(
        result.components,
        RecommendationScoreComponents,
    )
    assert result.version == "canonical-v8"


def test_exploration_and_discovery_scores_match_current_v8_mix_behavior() -> None:
    components = RecommendationScoreComponents(
        quality=80,
        price=70,
        trust=60,
        popularity=50,
        market=40,
        identity=90,
    )

    mix = calculate_recommendation_score(
        components,
        RecommendationPriority.MIX,
    )

    exploration = calculate_recommendation_score(
        components,
        RecommendationPriority.EXPLORATION,
    )

    discovery = calculate_recommendation_score(
        components,
        RecommendationPriority.DISCOVERY,
    )

    assert exploration.final_score == mix.final_score
    assert discovery.final_score == mix.final_score
    assert dict(exploration.weights) == dict(mix.weights)
    assert dict(discovery.weights) == dict(mix.weights)
