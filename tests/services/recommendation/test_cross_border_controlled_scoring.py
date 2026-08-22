from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from app.services.recommendation.cross_border_controlled_scoring import (
    ControlledScoringPath,
    ControlledScoringResult,
    calculate_controlled_recommendation_score,
)
from app.services.recommendation.cross_border_scoring_policy_fallback import (
    CrossBorderScoringFallbackDecision,
    CrossBorderScoringFallbackTarget,
)
from app.services.recommendation.models import (
    RecommendationPriority,
    RecommendationScoreComponents,
    RecommendationScoreResult,
)
from app.services.recommendation.scoring import (
    calculate_recommendation_score,
)


def _components():
    return RecommendationScoreComponents(
        quality=80,
        price=70,
        trust=90,
        popularity=60,
        market=50,
        identity=85,
    )


def _fallback(
    *,
    target=CrossBorderScoringFallbackTarget.CANDIDATE,
    fallback_required=False,
    activation_allowed=True,
    fallback_reason=None,
):
    return CrossBorderScoringFallbackDecision(
        target=target,
        baseline_policy_id="baseline-v1",
        candidate_policy_id="candidate-v1",
        fallback_required=fallback_required,
        activation_allowed=activation_allowed,
        boundary_eligible=(
            target
            is CrossBorderScoringFallbackTarget.CANDIDATE
        ),
        policy_identity_ready=True,
        authority_identity_ready=True,
        activation_state_safe=True,
        fallback_reason=fallback_reason,
    )


def _candidate(
    components,
    priority,
):
    return calculate_recommendation_score(
        components,
        priority,
        version="candidate-v1",
    )


def test_no_control_context_uses_baseline():
    result = calculate_controlled_recommendation_score(
        _components(),
        RecommendationPriority.MIX,
    )

    assert result.path is ControlledScoringPath.BASELINE
    assert result.score.version == "canonical-v8"
    assert result.fallback_applied is False


def test_baseline_target_uses_baseline():
    result = calculate_controlled_recommendation_score(
        _components(),
        RecommendationPriority.MIX,
        fallback=_fallback(
            target=CrossBorderScoringFallbackTarget.BASELINE,
            fallback_required=True,
            activation_allowed=False,
            fallback_reason="boundary",
        ),
        candidate_scorer=_candidate,
    )

    assert result.path is ControlledScoringPath.BASELINE
    assert result.score.version == "canonical-v8"
    assert result.fallback_applied is True
    assert result.fallback_reason == "boundary"


def test_candidate_target_uses_candidate_scorer():
    result = calculate_controlled_recommendation_score(
        _components(),
        RecommendationPriority.MIX,
        fallback=_fallback(),
        candidate_scorer=_candidate,
    )

    assert result.path is ControlledScoringPath.CANDIDATE
    assert result.score.version == "candidate-v1"
    assert result.fallback_applied is False
    assert result.fallback_reason is None


def test_candidate_requires_activation_allowed():
    result = calculate_controlled_recommendation_score(
        _components(),
        RecommendationPriority.MIX,
        fallback=_fallback(
            activation_allowed=False,
        ),
        candidate_scorer=_candidate,
    )

    assert result.path is ControlledScoringPath.BASELINE
    assert result.fallback_reason == "activation_not_allowed"


def test_candidate_rejects_fallback_required():
    result = calculate_controlled_recommendation_score(
        _components(),
        RecommendationPriority.MIX,
        fallback=_fallback(
            fallback_required=True,
            fallback_reason="governance",
        ),
        candidate_scorer=_candidate,
    )

    assert result.path is ControlledScoringPath.BASELINE
    assert result.fallback_reason == "governance"


def test_missing_candidate_scorer_falls_back():
    result = calculate_controlled_recommendation_score(
        _components(),
        RecommendationPriority.MIX,
        fallback=_fallback(),
    )

    assert result.path is ControlledScoringPath.BASELINE
    assert (
        result.fallback_reason
        == "candidate_scorer_unavailable"
    )


def test_candidate_exception_falls_back():
    def broken(
        components,
        priority,
    ):
        raise RuntimeError(
            "candidate failure"
        )

    result = calculate_controlled_recommendation_score(
        _components(),
        RecommendationPriority.MIX,
        fallback=_fallback(),
        candidate_scorer=broken,
    )

    assert result.path is ControlledScoringPath.BASELINE
    assert result.score.version == "canonical-v8"
    assert result.fallback_reason == "candidate_scorer_error"


def test_invalid_candidate_result_falls_back():
    def invalid(
        components,
        priority,
    ):
        return object()

    result = calculate_controlled_recommendation_score(
        _components(),
        RecommendationPriority.MIX,
        fallback=_fallback(),
        candidate_scorer=invalid,
    )

    assert result.path is ControlledScoringPath.BASELINE
    assert result.fallback_reason == "invalid_candidate_result"


def test_baseline_result_matches_canonical_scoring():
    expected = calculate_recommendation_score(
        _components(),
        RecommendationPriority.PRICE,
    )

    actual = calculate_controlled_recommendation_score(
        _components(),
        RecommendationPriority.PRICE,
    )

    assert actual.score == expected


def test_result_is_canonical_type():
    result = calculate_controlled_recommendation_score(
        _components(),
        RecommendationPriority.MIX,
    )

    assert isinstance(
        result,
        ControlledScoringResult,
    )

    assert isinstance(
        result.score,
        RecommendationScoreResult,
    )


def test_result_is_immutable():
    result = calculate_controlled_recommendation_score(
        _components(),
        RecommendationPriority.MIX,
    )

    with pytest.raises(
        FrozenInstanceError,
    ):
        result.path = ControlledScoringPath.CANDIDATE


def test_path_vocabulary_is_bounded():
    assert {
        path.value
        for path in ControlledScoringPath
    } == {
        "baseline",
        "candidate",
    }


def test_controlled_result_has_no_ranking_surface():
    result = calculate_controlled_recommendation_score(
        _components(),
        RecommendationPriority.MIX,
    )

    forbidden = {
        "rank",
        "ranking",
        "winner",
        "selected_candidate",
        "best_candidate",
    }

    public_names = {
        name.lower()
        for name in dir(result)
        if not name.startswith("_")
    }

    assert forbidden.isdisjoint(
        public_names
    )


def test_controlled_result_has_no_transaction_surface():
    result = calculate_controlled_recommendation_score(
        _components(),
        RecommendationPriority.MIX,
    )

    forbidden = {
        "checkout",
        "payment",
        "purchase",
        "dispatch",
        "book_shipment",
    }

    public_names = {
        name.lower()
        for name in dir(result)
        if not name.startswith("_")
    }

    assert forbidden.isdisjoint(
        public_names
    )
