from dataclasses import FrozenInstanceError

import pytest

from app.services.recommendation.models import (
    RecommendationContext,
    RecommendationPriority,
    RecommendationReason,
    RecommendationScoreComponents,
    RecommendationScoreResult,
)


def test_recommendation_priority_contains_canonical_modes() -> None:
    assert RecommendationPriority.MIX.value == "mix"
    assert RecommendationPriority.PRICE.value == "price"
    assert RecommendationPriority.QUALITY.value == "quality"
    assert RecommendationPriority.TRUST.value == "trust"
    assert RecommendationPriority.EXPLORATION.value == "exploration"
    assert RecommendationPriority.DISCOVERY.value == "discovery"
    assert RecommendationPriority.REVISIT.value == "revisit"


def test_recommendation_priority_does_not_encode_legacy_aliases() -> None:
    values = {
        priority.value
        for priority in RecommendationPriority
    }

    assert "ranking" not in values
    assert "quality_adaptive" not in values
    assert "balanced_adaptive" not in values


def test_score_components_are_immutable() -> None:
    components = RecommendationScoreComponents(
        quality=80,
        price=70,
    )

    with pytest.raises(FrozenInstanceError):
        components.quality = 90  # type: ignore[misc]


def test_score_components_as_mapping_exposes_canonical_axes() -> None:
    components = RecommendationScoreComponents(
        quality=80,
        price=70,
        trust=60,
        popularity=50,
        market=40,
        identity=90,
    )

    assert dict(
        components.as_mapping()
    ) == {
        "quality": 80,
        "price": 70,
        "trust": 60,
        "popularity": 50,
        "market": 40,
        "identity": 90,
    }


def test_score_result_accepts_valid_score() -> None:
    result = RecommendationScoreResult(
        final_score=81.5,
        priority=RecommendationPriority.MIX,
        components=RecommendationScoreComponents(
            quality=80,
        ),
        weights={
            "quality": 1.0,
        },
        reason_codes=(
            "high_quality",
        ),
        version="canonical-test",
    )

    assert result.final_score == 81.5
    assert result.priority is RecommendationPriority.MIX
    assert result.reason_codes == (
        "high_quality",
    )


@pytest.mark.parametrize(
    "score",
    [
        -0.1,
        100.1,
        999,
    ],
)
def test_score_result_rejects_out_of_range_final_score(
    score: float,
) -> None:
    with pytest.raises(ValueError):
        RecommendationScoreResult(
            final_score=score,
            priority=RecommendationPriority.MIX,
            components=RecommendationScoreComponents(),
        )


def test_score_result_weights_are_read_only() -> None:
    result = RecommendationScoreResult(
        final_score=50,
        priority=RecommendationPriority.MIX,
        components=RecommendationScoreComponents(),
        weights={
            "quality": 0.5,
            "price": 0.5,
        },
    )

    with pytest.raises(TypeError):
        result.weights["quality"] = 1.0  # type: ignore[index]


def test_recommendation_reason_is_structured_and_immutable() -> None:
    reason = RecommendationReason(
        code="high_quality",
        message="품질 신호가 높은 상품입니다.",
        weight=90,
        source="domain_quality",
    )

    assert reason.code == "high_quality"
    assert reason.source == "domain_quality"

    with pytest.raises(FrozenInstanceError):
        reason.weight = 0  # type: ignore[misc]


def test_recommendation_context_defaults_to_mix() -> None:
    context = RecommendationContext(
        query="사과",
    )

    assert context.priority is RecommendationPriority.MIX
    assert context.limit == 10
    assert context.adaptive is False


def test_recommendation_context_rejects_non_positive_limit() -> None:
    with pytest.raises(ValueError):
        RecommendationContext(
            query="사과",
            limit=0,
        )


def test_recommendation_context_metadata_is_read_only() -> None:
    context = RecommendationContext(
        metadata={
            "source": "test",
        },
    )

    with pytest.raises(TypeError):
        context.metadata["source"] = "changed"  # type: ignore[index]
