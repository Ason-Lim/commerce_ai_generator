import pytest

from app.services.recommendation.models import (
    RecommendationPriority,
)

from app.services.recommendation.policy import (
    RecommendationPolicy,
    resolve_recommendation_policy,
)

from app.services.recommendation_pipeline import (
    normalize_priority as legacy_pipeline_normalize_priority,
)


@pytest.mark.parametrize(
    (
        "raw",
        "expected_priority",
        "expected_adaptive",
        "expected_requested",
    ),
    [
        (
            "ranking",
            RecommendationPriority.MIX,
            False,
            "ranking",
        ),
        (
            "mix",
            RecommendationPriority.MIX,
            False,
            "mix",
        ),
        (
            "balanced",
            RecommendationPriority.MIX,
            False,
            "balanced",
        ),
        (
            "value",
            RecommendationPriority.PRICE,
            False,
            "value",
        ),
        (
            "price",
            RecommendationPriority.PRICE,
            False,
            "price",
        ),
        (
            "quality",
            RecommendationPriority.QUALITY,
            False,
            "quality",
        ),
        (
            "taste",
            RecommendationPriority.QUALITY,
            False,
            "taste",
        ),
        (
            "trust",
            RecommendationPriority.TRUST,
            False,
            "trust",
        ),
        (
            "exploration",
            RecommendationPriority.EXPLORATION,
            False,
            "exploration",
        ),
        (
            "discovery",
            RecommendationPriority.DISCOVERY,
            False,
            "discovery",
        ),
        (
            "revisit",
            RecommendationPriority.REVISIT,
            False,
            "revisit",
        ),
    ],
)
def test_policy_resolves_legacy_vocabulary(
    raw: str,
    expected_priority: RecommendationPriority,
    expected_adaptive: bool,
    expected_requested: str,
) -> None:
    result = resolve_recommendation_policy(
        raw
    )

    assert result == RecommendationPolicy(
        priority=expected_priority,
        adaptive=expected_adaptive,
        requested_priority=expected_requested,
    )


@pytest.mark.parametrize(
    (
        "raw",
        "expected_priority",
        "expected_requested",
    ),
    [
        (
            "quality_adaptive",
            RecommendationPriority.QUALITY,
            "quality",
        ),
        (
            "price_adaptive",
            RecommendationPriority.PRICE,
            "price",
        ),
        (
            "trust_adaptive",
            RecommendationPriority.TRUST,
            "trust",
        ),
        (
            "exploration_adaptive",
            RecommendationPriority.EXPLORATION,
            "exploration",
        ),
        (
            "balanced_adaptive",
            RecommendationPriority.MIX,
            "balanced",
        ),
    ],
)
def test_policy_separates_adaptive_flag_from_priority(
    raw: str,
    expected_priority: RecommendationPriority,
    expected_requested: str,
) -> None:
    result = resolve_recommendation_policy(
        raw
    )

    assert result.priority is expected_priority
    assert result.adaptive is True
    assert result.requested_priority == expected_requested


@pytest.mark.parametrize(
    "raw",
    [
        None,
        "",
        "unknown",
    ],
)
def test_unknown_or_empty_priority_falls_back_to_mix(
    raw: str | None,
) -> None:
    result = resolve_recommendation_policy(
        raw
    )

    assert result.priority is RecommendationPriority.MIX


def test_policy_does_not_add_adaptive_priority_enum_values() -> None:
    values = {
        priority.value
        for priority in RecommendationPriority
    }

    assert "quality_adaptive" not in values
    assert "price_adaptive" not in values
    assert "balanced_adaptive" not in values


@pytest.mark.parametrize(
    "raw",
    [
        "ranking",
        "price",
        "value",
        "quality",
        "trust",
        "exploration",
        "discovery",
        "revisit",
        "balanced",
        "quality_adaptive",
        "price_adaptive",
        "trust_adaptive",
        "exploration_adaptive",
    ],
)
def test_policy_preserves_pipeline_adaptive_semantics(
    raw: str,
) -> None:
    legacy_mode, legacy_adaptive = (
        legacy_pipeline_normalize_priority(
            raw
        )
    )

    canonical = resolve_recommendation_policy(
        raw
    )

    assert canonical.adaptive == legacy_adaptive

    expected = {
        "ranking": RecommendationPriority.MIX,
        "price": RecommendationPriority.PRICE,
        "quality": RecommendationPriority.QUALITY,
        "trust": RecommendationPriority.TRUST,
        "exploration": RecommendationPriority.EXPLORATION,
        "discovery": RecommendationPriority.DISCOVERY,
        "revisit": RecommendationPriority.REVISIT,
        "balanced": RecommendationPriority.MIX,
    }

    base = legacy_mode

    if base == "ranking":
        assert canonical.priority is RecommendationPriority.MIX
    elif base == "balanced":
        assert canonical.priority is RecommendationPriority.MIX
    else:
        assert canonical.priority is expected[base]


def test_policy_resolution_is_pure_and_deterministic() -> None:
    first = resolve_recommendation_policy(
        "quality_adaptive"
    )

    second = resolve_recommendation_policy(
        "quality_adaptive"
    )

    assert first == second
