from app.services.recommendation.cross_border_aligned_scoring_policy_fallback import (
    AlignedCrossBorderScoringFallback,
    AlignedCrossBorderScoringFallbackState,
)
from app.services.recommendation.cross_border_aligned_scoring_runtime_composition import (
    compose_aligned_cross_border_runtime_scorer,
)
from app.services.recommendation.models import (
    RecommendationPriority,
    RecommendationScoreComponents,
)
from app.services.recommendation.scoring import (
    calculate_recommendation_score,
)


def _components() -> RecommendationScoreComponents:
    return RecommendationScoreComponents(
        quality=80.0,
        price=70.0,
        trust=90.0,
        popularity=60.0,
        market=50.0,
        identity=85.0,
    )


def _aligned_fallback(
    *,
    state,
    fallback=None,
):
    return AlignedCrossBorderScoringFallback(
        state=state,
        aligned_boundary=None,
        fallback=fallback,
        reasons=(
            ("aligned_activation_boundary_blocked",)
            if state is AlignedCrossBorderScoringFallbackState.BLOCKED
            else ()
        ),
    )


def test_blocked_authority_returns_canonical_baseline_scorer():
    aligned_fallback = _aligned_fallback(
        state=AlignedCrossBorderScoringFallbackState.BLOCKED,
    )

    scorer = compose_aligned_cross_border_runtime_scorer(
        aligned_fallback,
    )

    assert scorer is calculate_recommendation_score


def test_blocked_authority_cannot_execute_candidate_scorer():
    calls = []

    def candidate_scorer(components, priority):
        calls.append(
            (
                components,
                priority,
            )
        )
        raise AssertionError(
            "candidate scorer must not execute under BLOCKED authority"
        )

    scorer = compose_aligned_cross_border_runtime_scorer(
        _aligned_fallback(
            state=AlignedCrossBorderScoringFallbackState.BLOCKED,
        ),
        candidate_scorer=candidate_scorer,
    )

    result = scorer(
        _components(),
        RecommendationPriority.MIX,
    )

    assert calls == []
    assert result == calculate_recommendation_score(
        _components(),
        RecommendationPriority.MIX,
    )


def test_available_authority_composes_provider_compatible_controlled_scorer(
    monkeypatch,
):
    expected_score = calculate_recommendation_score(
        _components(),
        RecommendationPriority.PRICE,
        version="controlled-test",
    )

    captured = {}

    class ControlledResult:
        score = expected_score

    class AlignedResult:
        controlled_result = ControlledResult()

    def fake_aligned_controlled_scorer(
        components,
        priority,
        *,
        aligned_fallback,
        candidate_scorer=None,
    ):
        captured["components"] = components
        captured["priority"] = priority
        captured["aligned_fallback"] = aligned_fallback
        captured["candidate_scorer"] = candidate_scorer
        return AlignedResult()

    monkeypatch.setattr(
        "app.services.recommendation."
        "cross_border_aligned_scoring_runtime_composition."
        "calculate_aligned_controlled_recommendation_score",
        fake_aligned_controlled_scorer,
    )

    aligned_fallback = _aligned_fallback(
        state=AlignedCrossBorderScoringFallbackState.AVAILABLE,
    )

    candidate_scorer = object()

    scorer = compose_aligned_cross_border_runtime_scorer(
        aligned_fallback,
        candidate_scorer=candidate_scorer,
    )

    result = scorer(
        _components(),
        RecommendationPriority.PRICE,
    )

    assert result is expected_score
    assert captured["aligned_fallback"] is aligned_fallback
    assert captured["candidate_scorer"] is candidate_scorer
    assert captured["priority"] is RecommendationPriority.PRICE


def test_available_composed_scorer_has_provider_call_shape(
    monkeypatch,
):
    expected_score = calculate_recommendation_score(
        _components(),
        RecommendationPriority.QUALITY,
    )

    class ControlledResult:
        score = expected_score

    class AlignedResult:
        controlled_result = ControlledResult()

    monkeypatch.setattr(
        "app.services.recommendation."
        "cross_border_aligned_scoring_runtime_composition."
        "calculate_aligned_controlled_recommendation_score",
        lambda components, priority, **kwargs: AlignedResult(),
    )

    scorer = compose_aligned_cross_border_runtime_scorer(
        _aligned_fallback(
            state=AlignedCrossBorderScoringFallbackState.AVAILABLE,
        ),
    )

    result = scorer(
        _components(),
        RecommendationPriority.QUALITY,
    )

    assert result is expected_score
