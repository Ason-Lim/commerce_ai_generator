from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

import app.services.recommendation.cross_border_aligned_controlled_scoring as module
from app.services.recommendation.cross_border_aligned_controlled_scoring import (
    AlignedControlledScoringResult,
    calculate_aligned_controlled_recommendation_score,
)
from app.services.recommendation.cross_border_aligned_scoring_policy_fallback import (
    AlignedCrossBorderScoringFallback,
    AlignedCrossBorderScoringFallbackState,
)
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


def _components() -> RecommendationScoreComponents:
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
) -> CrossBorderScoringFallbackDecision:
    return CrossBorderScoringFallbackDecision(
        target=target,
        baseline_policy_id="canonical-v8",
        candidate_policy_id="cross-border-candidate-v1",
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


def _aligned(
    *,
    state=AlignedCrossBorderScoringFallbackState.AVAILABLE,
    fallback=None,
) -> AlignedCrossBorderScoringFallback:
    if (
        fallback is None
        and state
        is AlignedCrossBorderScoringFallbackState.AVAILABLE
    ):
        fallback = _fallback()

    return AlignedCrossBorderScoringFallback(
        state=state,
        aligned_boundary=object(),  # type: ignore[arg-type]
        fallback=fallback,
        reasons=(
            ()
            if state
            is AlignedCrossBorderScoringFallbackState.AVAILABLE
            else ("aligned_activation_boundary_blocked",)
        ),
    )


def _candidate(
    components: RecommendationScoreComponents,
    priority: RecommendationPriority,
) -> RecommendationScoreResult:
    return calculate_recommendation_score(
        components,
        priority,
        version="cross-border-candidate-v1",
    )


def test_available_candidate_preserves_candidate_path():
    aligned = _aligned()

    result = calculate_aligned_controlled_recommendation_score(
        _components(),
        RecommendationPriority.MIX,
        aligned_fallback=aligned,
        candidate_scorer=_candidate,
    )

    assert isinstance(
        result,
        AlignedControlledScoringResult,
    )
    assert (
        result.controlled_result.path
        is ControlledScoringPath.CANDIDATE
    )
    assert (
        result.controlled_result.score.version
        == "cross-border-candidate-v1"
    )


def test_available_baseline_preserves_baseline_path():
    aligned = _aligned(
        fallback=_fallback(
            target=CrossBorderScoringFallbackTarget.BASELINE,
            fallback_required=True,
            activation_allowed=False,
            fallback_reason="boundary",
        )
    )

    result = calculate_aligned_controlled_recommendation_score(
        _components(),
        RecommendationPriority.MIX,
        aligned_fallback=aligned,
        candidate_scorer=_candidate,
    )

    assert (
        result.controlled_result.path
        is ControlledScoringPath.BASELINE
    )
    assert result.controlled_result.score.version == "canonical-v8"
    assert result.controlled_result.fallback_reason == "boundary"


def test_blocked_does_not_synthesize_canonical_fallback():
    aligned = _aligned(
        state=AlignedCrossBorderScoringFallbackState.BLOCKED,
        fallback=None,
    )

    result = calculate_aligned_controlled_recommendation_score(
        _components(),
        RecommendationPriority.MIX,
        aligned_fallback=aligned,
        candidate_scorer=_candidate,
    )

    assert aligned.fallback is None
    assert (
        result.controlled_result.path
        is ControlledScoringPath.BASELINE
    )
    assert result.controlled_result.fallback_applied is False


def test_blocked_baseline_is_owned_by_canonical_controlled_scoring():
    aligned = _aligned(
        state=AlignedCrossBorderScoringFallbackState.BLOCKED,
        fallback=None,
    )

    expected = calculate_controlled_recommendation_score(
        _components(),
        RecommendationPriority.PRICE,
        fallback=None,
        candidate_scorer=_candidate,
    )

    actual = calculate_aligned_controlled_recommendation_score(
        _components(),
        RecommendationPriority.PRICE,
        aligned_fallback=aligned,
        candidate_scorer=_candidate,
    )

    assert actual.controlled_result == expected


def test_exact_aligned_fallback_is_preserved():
    aligned = _aligned()

    result = calculate_aligned_controlled_recommendation_score(
        _components(),
        RecommendationPriority.MIX,
        aligned_fallback=aligned,
        candidate_scorer=_candidate,
    )

    assert result.aligned_fallback is aligned


def test_exact_nested_canonical_fallback_is_delegated(
    monkeypatch,
):
    canonical_fallback = _fallback()
    aligned = _aligned(
        fallback=canonical_fallback,
    )

    captured = {}
    sentinel = ControlledScoringResult(
        score=calculate_recommendation_score(
            _components(),
            RecommendationPriority.MIX,
        ),
        path=ControlledScoringPath.BASELINE,
        fallback_applied=False,
        fallback_reason=None,
    )

    def capture(
        components,
        priority,
        *,
        fallback=None,
        candidate_scorer=None,
    ):
        captured["components"] = components
        captured["priority"] = priority
        captured["fallback"] = fallback
        captured["candidate_scorer"] = candidate_scorer
        return sentinel

    monkeypatch.setattr(
        module,
        "calculate_controlled_recommendation_score",
        capture,
    )

    components = _components()

    result = calculate_aligned_controlled_recommendation_score(
        components,
        RecommendationPriority.QUALITY,
        aligned_fallback=aligned,
        candidate_scorer=_candidate,
    )

    assert captured["components"] is components
    assert (
        captured["priority"]
        is RecommendationPriority.QUALITY
    )
    assert captured["fallback"] is canonical_fallback
    assert captured["candidate_scorer"] is _candidate
    assert result.controlled_result is sentinel


def test_blocked_delegates_none_fallback_exactly(
    monkeypatch,
):
    aligned = _aligned(
        state=AlignedCrossBorderScoringFallbackState.BLOCKED,
        fallback=None,
    )

    captured = []

    expected = calculate_controlled_recommendation_score(
        _components(),
        RecommendationPriority.MIX,
    )

    def capture(
        components,
        priority,
        *,
        fallback=None,
        candidate_scorer=None,
    ):
        captured.append(fallback)
        return expected

    monkeypatch.setattr(
        module,
        "calculate_controlled_recommendation_score",
        capture,
    )

    result = calculate_aligned_controlled_recommendation_score(
        _components(),
        RecommendationPriority.MIX,
        aligned_fallback=aligned,
        candidate_scorer=_candidate,
    )

    assert captured == [None]
    assert result.controlled_result is expected


def test_missing_candidate_scorer_remains_canonical_fail_closed():
    aligned = _aligned()

    result = calculate_aligned_controlled_recommendation_score(
        _components(),
        RecommendationPriority.MIX,
        aligned_fallback=aligned,
    )

    assert (
        result.controlled_result.path
        is ControlledScoringPath.BASELINE
    )
    assert (
        result.controlled_result.fallback_reason
        == "candidate_scorer_unavailable"
    )


def test_candidate_failure_remains_canonical_fail_closed():
    aligned = _aligned()

    def broken(
        components,
        priority,
    ):
        raise RuntimeError("candidate failure")

    result = calculate_aligned_controlled_recommendation_score(
        _components(),
        RecommendationPriority.MIX,
        aligned_fallback=aligned,
        candidate_scorer=broken,
    )

    assert (
        result.controlled_result.path
        is ControlledScoringPath.BASELINE
    )
    assert (
        result.controlled_result.fallback_reason
        == "candidate_scorer_error"
    )


def test_result_is_immutable():
    result = calculate_aligned_controlled_recommendation_score(
        _components(),
        RecommendationPriority.MIX,
        aligned_fallback=_aligned(),
        candidate_scorer=_candidate,
    )

    with pytest.raises(FrozenInstanceError):
        result.controlled_result = object()


def test_result_has_no_provider_binding_surface():
    result = calculate_aligned_controlled_recommendation_score(
        _components(),
        RecommendationPriority.MIX,
        aligned_fallback=_aligned(),
        candidate_scorer=_candidate,
    )

    forbidden = {
        "provider",
        "bind_provider",
        "recommend",
        "recommendation",
        "ranking",
        "winner",
        "selected_candidate",
    }

    public_names = {
        name.lower()
        for name in dir(result)
        if not name.startswith("_")
    }

    assert forbidden.isdisjoint(public_names)


def test_result_has_no_runtime_or_transaction_surface():
    result = calculate_aligned_controlled_recommendation_score(
        _components(),
        RecommendationPriority.MIX,
        aligned_fallback=_aligned(),
        candidate_scorer=_candidate,
    )

    forbidden = {
        "route_traffic",
        "rollout",
        "production_enabled",
        "purchase",
        "checkout",
        "transaction",
    }

    public_names = {
        name.lower()
        for name in dir(result)
        if not name.startswith("_")
    }

    assert forbidden.isdisjoint(public_names)
