from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

import app.services.recommendation.cross_border_aligned_scoring_policy_activation_boundary as module
from app.services.recommendation.cross_border_aligned_scoring_policy_activation_boundary import (
    AlignedCrossBorderPolicyActivationBoundary,
    AlignedCrossBorderPolicyActivationBoundaryState,
    evaluate_aligned_cross_border_policy_activation_boundary,
)
from app.services.recommendation.cross_border_aligned_scoring_policy_activation_decision import (
    AlignedCrossBorderPolicyActivationDecision,
    AlignedCrossBorderPolicyActivationDecisionState,
)
from app.services.recommendation.cross_border_scoring_policy_activation_boundary import (
    CrossBorderActivationBoundaryState,
    CrossBorderScoringActivationBoundary,
    evaluate_cross_border_scoring_activation_boundary,
)
from app.services.recommendation.cross_border_scoring_policy_activation_decision import (
    CrossBorderPolicyActivationDecision,
    CrossBorderPolicyActivationDecisionOutcome,
)


def _decision(
    *,
    outcome=CrossBorderPolicyActivationDecisionOutcome.AUTHORIZE,
    activation_readiness_confirmed=True,
    baseline_policy_id="baseline-v1",
    candidate_policy_id="candidate-v1",
    activation_authority_id="production-governance",
    activation_authority_role="policy_activation_authority",
    production_enabled=False,
    rollout_started=False,
    traffic_routed=False,
) -> CrossBorderPolicyActivationDecision:
    return CrossBorderPolicyActivationDecision(
        outcome=outcome,
        baseline_policy_id=baseline_policy_id,
        candidate_policy_id=candidate_policy_id,
        adoption_authority_id="recommendation-governance",
        adoption_authority_role="policy_adoption_authority",
        activation_authority_id=activation_authority_id,
        activation_authority_role=activation_authority_role,
        activation_readiness_confirmed=(
            activation_readiness_confirmed
        ),
        reason="recorded activation decision",
        production_enabled=production_enabled,
        rollout_started=rollout_started,
        traffic_routed=traffic_routed,
    )


def _aligned(
    *,
    state=AlignedCrossBorderPolicyActivationDecisionState.RECORDED,
    decision=None,
) -> AlignedCrossBorderPolicyActivationDecision:
    if (
        decision is None
        and state
        is AlignedCrossBorderPolicyActivationDecisionState.RECORDED
    ):
        decision = _decision()

    return AlignedCrossBorderPolicyActivationDecision(
        state=state,
        aligned_readiness=None,  # type: ignore[arg-type]
        decision=decision,
        reasons=(
            ()
            if state
            is AlignedCrossBorderPolicyActivationDecisionState.RECORDED
            else ("blocked_for_test",)
        ),
    )


def test_recorded_authorized_safe_decision_is_available_and_eligible():
    result = evaluate_aligned_cross_border_policy_activation_boundary(
        _aligned()
    )

    assert (
        result.state
        is AlignedCrossBorderPolicyActivationBoundaryState.AVAILABLE
    )
    assert isinstance(
        result.boundary,
        CrossBorderScoringActivationBoundary,
    )
    assert (
        result.boundary.state
        is CrossBorderActivationBoundaryState.ELIGIBLE
    )
    assert result.reasons == ()


@pytest.mark.parametrize(
    "outcome",
    (
        CrossBorderPolicyActivationDecisionOutcome.HOLD,
        CrossBorderPolicyActivationDecisionOutcome.DENY,
    ),
)
def test_recorded_non_authorize_decision_is_available_but_fallback(
    outcome,
):
    result = evaluate_aligned_cross_border_policy_activation_boundary(
        _aligned(
            decision=_decision(
                outcome=outcome,
            )
        )
    )

    assert (
        result.state
        is AlignedCrossBorderPolicyActivationBoundaryState.AVAILABLE
    )
    assert result.boundary is not None
    assert (
        result.boundary.state
        is CrossBorderActivationBoundaryState.FALLBACK
    )
    assert "authorization" in result.boundary.reasons
    assert result.reasons == ()


def test_recorded_unconfirmed_readiness_is_available_but_fallback():
    result = evaluate_aligned_cross_border_policy_activation_boundary(
        _aligned(
            decision=_decision(
                activation_readiness_confirmed=False,
            )
        )
    )

    assert result.is_available is True
    assert result.boundary is not None
    assert (
        result.boundary.state
        is CrossBorderActivationBoundaryState.FALLBACK
    )
    assert "authorization" in result.boundary.reasons


def test_recorded_invalid_policy_identity_is_available_but_fallback():
    result = evaluate_aligned_cross_border_policy_activation_boundary(
        _aligned(
            decision=_decision(
                candidate_policy_id="baseline-v1",
            )
        )
    )

    assert result.is_available is True
    assert result.boundary is not None
    assert (
        result.boundary.state
        is CrossBorderActivationBoundaryState.FALLBACK
    )
    assert "policy_identity" in result.boundary.reasons


def test_recorded_invalid_authority_identity_is_available_but_fallback():
    result = evaluate_aligned_cross_border_policy_activation_boundary(
        _aligned(
            decision=_decision(
                activation_authority_id=" ",
            )
        )
    )

    assert result.is_available is True
    assert result.boundary is not None
    assert (
        result.boundary.state
        is CrossBorderActivationBoundaryState.FALLBACK
    )
    assert "authority_identity" in result.boundary.reasons


def test_recorded_unsafe_activation_state_is_available_but_fallback():
    result = evaluate_aligned_cross_border_policy_activation_boundary(
        _aligned(
            decision=_decision(
                production_enabled=True,
            )
        )
    )

    assert result.is_available is True
    assert result.boundary is not None
    assert (
        result.boundary.state
        is CrossBorderActivationBoundaryState.FALLBACK
    )
    assert "activation_state" in result.boundary.reasons


def test_blocked_aligned_decision_does_not_invoke_canonical_boundary(
    monkeypatch,
):
    called = False

    def fail_if_called(decision):
        nonlocal called
        called = True
        raise AssertionError(
            "canonical activation boundary must not be invoked"
        )

    monkeypatch.setattr(
        module,
        "evaluate_cross_border_scoring_activation_boundary",
        fail_if_called,
    )

    result = evaluate_aligned_cross_border_policy_activation_boundary(
        _aligned(
            state=AlignedCrossBorderPolicyActivationDecisionState.BLOCKED,
            decision=None,
        )
    )

    assert called is False
    assert (
        result.state
        is AlignedCrossBorderPolicyActivationBoundaryState.BLOCKED
    )
    assert result.boundary is None
    assert result.reasons == (
        "aligned_activation_decision_not_recorded",
    )


def test_recorded_state_without_canonical_decision_is_invalid():
    aligned = AlignedCrossBorderPolicyActivationDecision(
        state=AlignedCrossBorderPolicyActivationDecisionState.RECORDED,
        aligned_readiness=None,  # type: ignore[arg-type]
        decision=None,
        reasons=(),
    )

    with pytest.raises(
        ValueError,
        match="must contain canonical decision",
    ):
        evaluate_aligned_cross_border_policy_activation_boundary(
            aligned
        )


def test_exact_canonical_decision_is_delegated(monkeypatch):
    decision = _decision()

    expected = evaluate_cross_border_scoring_activation_boundary(
        decision
    )
    captured = None

    def capture(value):
        nonlocal captured
        captured = value
        return expected

    monkeypatch.setattr(
        module,
        "evaluate_cross_border_scoring_activation_boundary",
        capture,
    )

    result = evaluate_aligned_cross_border_policy_activation_boundary(
        _aligned(
            decision=decision,
        )
    )

    assert captured is decision
    assert result.boundary is expected


def test_available_is_not_alias_for_eligible():
    result = evaluate_aligned_cross_border_policy_activation_boundary(
        _aligned(
            decision=_decision(
                outcome=CrossBorderPolicyActivationDecisionOutcome.HOLD,
            )
        )
    )

    assert result.is_available is True
    assert result.boundary is not None
    assert (
        result.boundary.state
        is CrossBorderActivationBoundaryState.FALLBACK
    )


def test_blocked_is_not_alias_for_fallback():
    result = evaluate_aligned_cross_border_policy_activation_boundary(
        _aligned(
            state=AlignedCrossBorderPolicyActivationDecisionState.BLOCKED,
            decision=None,
        )
    )

    assert (
        result.state
        is AlignedCrossBorderPolicyActivationBoundaryState.BLOCKED
    )
    assert result.boundary is None


def test_state_vocabulary_is_bounded():
    assert {
        state.value
        for state in AlignedCrossBorderPolicyActivationBoundaryState
    } == {
        "available",
        "blocked",
    }


def test_result_is_explicit_aligned_boundary_type():
    result = evaluate_aligned_cross_border_policy_activation_boundary(
        _aligned()
    )

    assert isinstance(
        result,
        AlignedCrossBorderPolicyActivationBoundary,
    )


def test_result_is_immutable():
    result = evaluate_aligned_cross_border_policy_activation_boundary(
        _aligned()
    )

    with pytest.raises(FrozenInstanceError):
        result.state = (
            AlignedCrossBorderPolicyActivationBoundaryState.BLOCKED
        )


def test_result_has_no_runtime_activation_surface():
    result = evaluate_aligned_cross_border_policy_activation_boundary(
        _aligned()
    )

    forbidden = {
        "activate",
        "activate_runtime",
        "production_enabled",
        "rollout_started",
        "traffic_routed",
        "route_traffic",
    }

    public_names = {
        name.lower()
        for name in dir(result)
        if not name.startswith("_")
    }

    assert forbidden.isdisjoint(public_names)


def test_result_has_no_fallback_selection_surface():
    result = evaluate_aligned_cross_border_policy_activation_boundary(
        _aligned()
    )

    forbidden = {
        "target",
        "fallback_required",
        "fallback_reason",
        "activation_allowed",
    }

    public_names = {
        name.lower()
        for name in dir(result)
        if not name.startswith("_")
    }

    assert forbidden.isdisjoint(public_names)


def test_result_has_no_controlled_scoring_surface():
    result = evaluate_aligned_cross_border_policy_activation_boundary(
        _aligned()
    )

    forbidden = {
        "score",
        "final_score",
        "apply_score",
        "rank",
        "ranking",
        "winner",
        "recommend",
    }

    public_names = {
        name.lower()
        for name in dir(result)
        if not name.startswith("_")
    }

    assert forbidden.isdisjoint(public_names)
