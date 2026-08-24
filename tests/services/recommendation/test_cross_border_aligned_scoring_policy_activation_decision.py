from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from app.services.recommendation.cross_border_aligned_scoring_policy_activation_decision import (
    AlignedCrossBorderPolicyActivationDecision,
    AlignedCrossBorderPolicyActivationDecisionState,
    record_aligned_cross_border_policy_activation_decision,
)
from app.services.recommendation.cross_border_aligned_scoring_policy_activation_readiness import (
    AlignedCrossBorderPolicyActivationReadiness,
    AlignedCrossBorderPolicyActivationReadinessState,
)
from app.services.recommendation.cross_border_scoring_policy_activation_decision import (
    CrossBorderPolicyActivationAuthority,
    CrossBorderPolicyActivationDecision,
    CrossBorderPolicyActivationDecisionOutcome,
)
from app.services.recommendation.cross_border_scoring_policy_activation_readiness import (
    CrossBorderPolicyActivationReadiness,
    CrossBorderPolicyActivationReadinessState,
)


def _canonical_readiness(
    *,
    state=CrossBorderPolicyActivationReadinessState.READY,
) -> CrossBorderPolicyActivationReadiness:
    ready = (
        state
        is CrossBorderPolicyActivationReadinessState.READY
    )
    return CrossBorderPolicyActivationReadiness(
        state=state,
        baseline_policy_id="baseline-v1",
        candidate_policy_id="candidate-v1",
        authority_id="recommendation-governance",
        authority_role="policy_adoption_authority",
        adoption_decision_ready=ready,
        readiness_evidence_ready=ready,
        policy_identity_ready=ready,
        authority_identity_ready=ready,
        activation_boundary_ready=ready,
        reasons=() if ready else ("adoption_decision",),
    )


def _aligned_readiness(
    *,
    state=AlignedCrossBorderPolicyActivationReadinessState.AVAILABLE,
    canonical_state=CrossBorderPolicyActivationReadinessState.READY,
) -> AlignedCrossBorderPolicyActivationReadiness:
    return AlignedCrossBorderPolicyActivationReadiness(
        state=state,
        aligned_decision=None,  # type: ignore[arg-type]
        readiness=(
            _canonical_readiness(state=canonical_state)
            if state
            is AlignedCrossBorderPolicyActivationReadinessState.AVAILABLE
            else None
        ),
        reasons=(
            ()
            if state
            is AlignedCrossBorderPolicyActivationReadinessState.AVAILABLE
            else ("aligned_adoption_decision_not_recorded",)
        ),
    )


def _authority() -> CrossBorderPolicyActivationAuthority:
    return CrossBorderPolicyActivationAuthority(
        authority_id="production-governance",
        authority_role="policy_activation_authority",
    )


def test_available_ready_can_record_authorize():
    result = record_aligned_cross_border_policy_activation_decision(
        aligned_readiness=_aligned_readiness(),
        authority=_authority(),
        outcome=CrossBorderPolicyActivationDecisionOutcome.AUTHORIZE,
        reason="controlled activation authorized",
    )

    assert (
        result.state
        is AlignedCrossBorderPolicyActivationDecisionState.RECORDED
    )
    assert isinstance(
        result.decision,
        CrossBorderPolicyActivationDecision,
    )
    assert (
        result.decision.outcome
        is CrossBorderPolicyActivationDecisionOutcome.AUTHORIZE
    )


def test_available_ready_can_record_hold():
    result = record_aligned_cross_border_policy_activation_decision(
        aligned_readiness=_aligned_readiness(),
        authority=_authority(),
        outcome=CrossBorderPolicyActivationDecisionOutcome.HOLD,
        reason="additional controls required",
    )

    assert (
        result.state
        is AlignedCrossBorderPolicyActivationDecisionState.RECORDED
    )
    assert (
        result.decision.outcome
        is CrossBorderPolicyActivationDecisionOutcome.HOLD
    )


def test_available_ready_can_record_deny():
    result = record_aligned_cross_border_policy_activation_decision(
        aligned_readiness=_aligned_readiness(),
        authority=_authority(),
        outcome=CrossBorderPolicyActivationDecisionOutcome.DENY,
        reason="activation denied",
    )

    assert (
        result.decision.outcome
        is CrossBorderPolicyActivationDecisionOutcome.DENY
    )


def test_available_not_ready_can_record_hold():
    result = record_aligned_cross_border_policy_activation_decision(
        aligned_readiness=_aligned_readiness(
            canonical_state=(
                CrossBorderPolicyActivationReadinessState.NOT_READY
            )
        ),
        authority=_authority(),
        outcome=CrossBorderPolicyActivationDecisionOutcome.HOLD,
        reason="activation evidence incomplete",
    )

    assert (
        result.state
        is AlignedCrossBorderPolicyActivationDecisionState.RECORDED
    )
    assert result.decision.activation_readiness_confirmed is False


def test_available_not_ready_can_record_deny():
    result = record_aligned_cross_border_policy_activation_decision(
        aligned_readiness=_aligned_readiness(
            canonical_state=(
                CrossBorderPolicyActivationReadinessState.NOT_READY
            )
        ),
        authority=_authority(),
        outcome=CrossBorderPolicyActivationDecisionOutcome.DENY,
        reason="activation evidence rejected",
    )

    assert (
        result.decision.outcome
        is CrossBorderPolicyActivationDecisionOutcome.DENY
    )


def test_available_not_ready_cannot_record_authorize():
    with pytest.raises(
        ValueError,
        match="requires activation-ready evidence",
    ):
        record_aligned_cross_border_policy_activation_decision(
            aligned_readiness=_aligned_readiness(
                canonical_state=(
                    CrossBorderPolicyActivationReadinessState.NOT_READY
                )
            ),
            authority=_authority(),
            outcome=(
                CrossBorderPolicyActivationDecisionOutcome.AUTHORIZE
            ),
            reason="attempted authorization",
        )


def test_available_is_not_alias_for_authorize():
    result = record_aligned_cross_border_policy_activation_decision(
        aligned_readiness=_aligned_readiness(),
        authority=_authority(),
        outcome=CrossBorderPolicyActivationDecisionOutcome.HOLD,
        reason="review remains open",
    )

    assert (
        result.state
        is AlignedCrossBorderPolicyActivationDecisionState.RECORDED
    )
    assert (
        result.decision.outcome
        is not CrossBorderPolicyActivationDecisionOutcome.AUTHORIZE
    )


def test_blocked_aligned_readiness_blocks_canonical_recording():
    result = record_aligned_cross_border_policy_activation_decision(
        aligned_readiness=_aligned_readiness(
            state=(
                AlignedCrossBorderPolicyActivationReadinessState.BLOCKED
            )
        ),
        authority=_authority(),
        outcome=CrossBorderPolicyActivationDecisionOutcome.AUTHORIZE,
        reason="must not enter canonical recorder",
    )

    assert (
        result.state
        is AlignedCrossBorderPolicyActivationDecisionState.BLOCKED
    )
    assert result.decision is None
    assert result.reasons == (
        "aligned_activation_readiness_not_available",
    )


def test_exact_canonical_readiness_is_delegated():
    aligned = _aligned_readiness()

    result = record_aligned_cross_border_policy_activation_decision(
        aligned_readiness=aligned,
        authority=_authority(),
        outcome=CrossBorderPolicyActivationDecisionOutcome.HOLD,
        reason="delegation check",
    )

    assert result.decision.baseline_policy_id == (
        aligned.readiness.baseline_policy_id
    )
    assert result.decision.candidate_policy_id == (
        aligned.readiness.candidate_policy_id
    )


def test_activation_authority_identity_is_preserved():
    result = record_aligned_cross_border_policy_activation_decision(
        aligned_readiness=_aligned_readiness(),
        authority=_authority(),
        outcome=CrossBorderPolicyActivationDecisionOutcome.HOLD,
        reason="authority preservation",
    )

    assert (
        result.decision.activation_authority_id
        == "production-governance"
    )
    assert (
        result.decision.activation_authority_role
        == "policy_activation_authority"
    )


def test_authorize_does_not_enable_production():
    result = record_aligned_cross_border_policy_activation_decision(
        aligned_readiness=_aligned_readiness(),
        authority=_authority(),
        outcome=CrossBorderPolicyActivationDecisionOutcome.AUTHORIZE,
        reason="governance authorization",
    )

    assert result.decision.production_enabled is False
    assert result.decision.rollout_started is False
    assert result.decision.traffic_routed is False


def test_state_vocabulary_is_bounded():
    assert {
        state.value
        for state in AlignedCrossBorderPolicyActivationDecisionState
    } == {
        "recorded",
        "blocked",
    }


def test_result_is_immutable():
    result = record_aligned_cross_border_policy_activation_decision(
        aligned_readiness=_aligned_readiness(),
        authority=_authority(),
        outcome=CrossBorderPolicyActivationDecisionOutcome.HOLD,
        reason="pending",
    )

    with pytest.raises(FrozenInstanceError):
        result.state = (
            AlignedCrossBorderPolicyActivationDecisionState.BLOCKED
        )


def test_recorded_has_no_runtime_activation_surface():
    result = record_aligned_cross_border_policy_activation_decision(
        aligned_readiness=_aligned_readiness(),
        authority=_authority(),
        outcome=CrossBorderPolicyActivationDecisionOutcome.AUTHORIZE,
        reason="governance authorization",
    )

    forbidden = {
        "activate",
        "activate_runtime",
        "enable_runtime",
        "traffic_percentage",
        "rollout_percentage",
        "route_traffic",
    }
    public_names = {
        name.lower()
        for name in dir(result)
        if not name.startswith("_")
    }

    assert forbidden.isdisjoint(public_names)


def test_recorded_does_not_enter_activation_boundary():
    result = record_aligned_cross_border_policy_activation_decision(
        aligned_readiness=_aligned_readiness(),
        authority=_authority(),
        outcome=CrossBorderPolicyActivationDecisionOutcome.AUTHORIZE,
        reason="boundary remains separate",
    )

    assert not hasattr(result, "activation_boundary")
    assert not hasattr(result, "eligible")


def test_available_without_canonical_readiness_is_rejected():
    aligned = AlignedCrossBorderPolicyActivationReadiness(
        state=(
            AlignedCrossBorderPolicyActivationReadinessState.AVAILABLE
        ),
        aligned_decision=None,  # type: ignore[arg-type]
        readiness=None,
        reasons=(),
    )

    with pytest.raises(
        ValueError,
        match="must contain canonical readiness",
    ):
        record_aligned_cross_border_policy_activation_decision(
            aligned_readiness=aligned,
            authority=_authority(),
            outcome=CrossBorderPolicyActivationDecisionOutcome.HOLD,
            reason="invalid aligned state",
        )
