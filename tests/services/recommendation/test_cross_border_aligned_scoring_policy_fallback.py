from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

import app.services.recommendation.cross_border_aligned_scoring_policy_fallback as module
from app.services.recommendation.cross_border_aligned_scoring_policy_fallback import (
    AlignedCrossBorderScoringFallback,
    AlignedCrossBorderScoringFallbackState,
    evaluate_aligned_cross_border_scoring_fallback,
)
from app.services.recommendation.cross_border_aligned_scoring_policy_activation_boundary import (
    AlignedCrossBorderPolicyActivationBoundary,
)


def _aligned_boundary(
    *,
    boundary,
    aligned_decision=None,
):
    return AlignedCrossBorderPolicyActivationBoundary(
        state=(
            "available"
            if boundary is not None
            else "blocked"
        ),
        aligned_decision=aligned_decision,
        boundary=boundary,
        reasons=(),
    )


def test_state_vocabulary_is_bounded():
    assert {
        item.value
        for item in AlignedCrossBorderScoringFallbackState
    } == {
        "available",
        "blocked",
    }


def test_result_is_frozen():
    assert (
        AlignedCrossBorderScoringFallback.__dataclass_params__.frozen
        is True
    )


def test_blocked_does_not_call_canonical_fallback(
    monkeypatch,
):
    aligned_boundary = _aligned_boundary(
        boundary=None,
        aligned_decision=object(),
    )

    called = False

    def forbidden(_boundary):
        nonlocal called
        called = True
        raise AssertionError(
            "canonical fallback must not be called"
        )

    monkeypatch.setattr(
        module,
        "evaluate_cross_border_scoring_fallback",
        forbidden,
    )

    result = evaluate_aligned_cross_border_scoring_fallback(
        aligned_boundary,
    )

    assert called is False
    assert (
        result.state
        is AlignedCrossBorderScoringFallbackState.BLOCKED
    )
    assert result.fallback is None


def test_blocked_preserves_exact_aligned_boundary():
    aligned_boundary = _aligned_boundary(
        boundary=None,
        aligned_decision=object(),
    )

    result = evaluate_aligned_cross_border_scoring_fallback(
        aligned_boundary,
    )

    assert result.aligned_boundary is aligned_boundary


def test_blocked_is_not_rewritten_as_canonical_baseline():
    aligned_boundary = _aligned_boundary(
        boundary=None,
    )

    result = evaluate_aligned_cross_border_scoring_fallback(
        aligned_boundary,
    )

    assert result.fallback is None
    assert result.state.value == "blocked"


def test_available_delegates_exact_nested_boundary(
    monkeypatch,
):
    canonical_boundary = object()
    aligned_boundary = _aligned_boundary(
        boundary=canonical_boundary,
        aligned_decision=object(),
    )
    sentinel = object()
    received = []

    def fake(boundary):
        received.append(boundary)
        return sentinel

    monkeypatch.setattr(
        module,
        "evaluate_cross_border_scoring_fallback",
        fake,
    )

    result = evaluate_aligned_cross_border_scoring_fallback(
        aligned_boundary,
    )

    assert received == [canonical_boundary]
    assert (
        result.state
        is AlignedCrossBorderScoringFallbackState.AVAILABLE
    )
    assert result.fallback is sentinel


def test_available_preserves_exact_aligned_boundary(
    monkeypatch,
):
    canonical_boundary = object()
    aligned_boundary = _aligned_boundary(
        boundary=canonical_boundary,
        aligned_decision=object(),
    )

    monkeypatch.setattr(
        module,
        "evaluate_cross_border_scoring_fallback",
        lambda boundary: object(),
    )

    result = evaluate_aligned_cross_border_scoring_fallback(
        aligned_boundary,
    )

    assert result.aligned_boundary is aligned_boundary


def test_available_preserves_exact_canonical_fallback_result(
    monkeypatch,
):
    canonical_boundary = object()
    aligned_boundary = _aligned_boundary(
        boundary=canonical_boundary,
    )
    canonical_fallback = object()

    monkeypatch.setattr(
        module,
        "evaluate_cross_border_scoring_fallback",
        lambda boundary: canonical_fallback,
    )

    result = evaluate_aligned_cross_border_scoring_fallback(
        aligned_boundary,
    )

    assert result.fallback is canonical_fallback


def test_available_does_not_add_local_policy_reasons(
    monkeypatch,
):
    aligned_boundary = _aligned_boundary(
        boundary=object(),
    )

    monkeypatch.setattr(
        module,
        "evaluate_cross_border_scoring_fallback",
        lambda boundary: object(),
    )

    result = evaluate_aligned_cross_border_scoring_fallback(
        aligned_boundary,
    )

    assert result.reasons == ()


def test_blocked_reason_is_entry_state_only():
    aligned_boundary = _aligned_boundary(
        boundary=None,
    )

    result = evaluate_aligned_cross_border_scoring_fallback(
        aligned_boundary,
    )

    assert result.reasons == (
        "aligned_activation_boundary_blocked",
    )


def test_result_rejects_mutation():
    result = AlignedCrossBorderScoringFallback(
        state=AlignedCrossBorderScoringFallbackState.BLOCKED,
        aligned_boundary=object(),
        fallback=None,
        reasons=(),
    )

    with pytest.raises(FrozenInstanceError):
        result.fallback = object()


def test_module_has_no_controlled_scoring_authority():
    assert not hasattr(
        module,
        "evaluate_cross_border_controlled_scoring",
    )


def test_module_has_no_ranking_or_recommendation_authority():
    forbidden = (
        "rank",
        "recommend",
        "select_recommendation",
        "activate_runtime",
        "route_traffic",
    )

    for name in forbidden:
        assert not hasattr(module, name)
