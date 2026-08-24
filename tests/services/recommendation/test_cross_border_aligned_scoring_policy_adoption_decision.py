from __future__ import annotations

from dataclasses import FrozenInstanceError
from unittest.mock import patch

import pytest

from app.services.recommendation.cross_border_aligned_scoring_policy_adoption_decision import (
    AlignedCrossBorderPolicyAdoptionDecision,
    AlignedCrossBorderPolicyAdoptionDecisionState,
    record_aligned_cross_border_policy_adoption_decision,
)
from app.services.recommendation.cross_border_aligned_scoring_policy_adoption_readiness import (
    AlignedCrossBorderPolicyAdoptionReadiness,
    AlignedCrossBorderPolicyAdoptionReadinessState,
)
from app.services.recommendation.cross_border_scoring_policy_adoption_decision import (
    CrossBorderPolicyAdoptionAuthority,
    CrossBorderPolicyAdoptionDecision,
    CrossBorderPolicyAdoptionDecisionOutcome,
    record_cross_border_policy_adoption_decision,
)
from app.services.recommendation.cross_border_scoring_policy_adoption_readiness import (
    CrossBorderPolicyAdoptionReadiness,
    CrossBorderPolicyAdoptionReadinessState,
)


def _authority() -> CrossBorderPolicyAdoptionAuthority:
    return CrossBorderPolicyAdoptionAuthority(
        authority_id="architecture-authority",
        authority_role="policy-adoption-authority",
    )


def _readiness(
    state: CrossBorderPolicyAdoptionReadinessState,
) -> CrossBorderPolicyAdoptionReadiness:
    ready = state is CrossBorderPolicyAdoptionReadinessState.READY

    return CrossBorderPolicyAdoptionReadiness(
        state=state,
        baseline_policy_id="baseline-policy",
        candidate_policy_id="candidate-policy",
        comparison_ready=ready,
        policy_identity_ready=ready,
        delta_evidence_ready=ready,
        candidate_identity_ready=ready,
        direction_ready=ready,
        shadow_evidence_ready=ready,
        policy_roles_ready=ready,
        reasons=() if ready else ("comparison",),
    )


def _aligned_available(
    state: CrossBorderPolicyAdoptionReadinessState,
) -> AlignedCrossBorderPolicyAdoptionReadiness:
    return AlignedCrossBorderPolicyAdoptionReadiness(
        state=AlignedCrossBorderPolicyAdoptionReadinessState.AVAILABLE,
        aligned_comparison=None,  # type: ignore[arg-type]
        readiness=_readiness(state),
        reasons=(),
    )


def _aligned_blocked() -> AlignedCrossBorderPolicyAdoptionReadiness:
    return AlignedCrossBorderPolicyAdoptionReadiness(
        state=AlignedCrossBorderPolicyAdoptionReadinessState.BLOCKED,
        aligned_comparison=None,  # type: ignore[arg-type]
        readiness=None,
        reasons=("blocked_for_test",),
    )


def test_ready_adopt_delegates_to_canonical_authority():
    aligned = _aligned_available(
        CrossBorderPolicyAdoptionReadinessState.READY
    )
    authority = _authority()

    result = record_aligned_cross_border_policy_adoption_decision(
        aligned_readiness=aligned,
        authority=authority,
        outcome=CrossBorderPolicyAdoptionDecisionOutcome.ADOPT,
        reason="approved after governance review",
    )

    assert (
        result.state
        is AlignedCrossBorderPolicyAdoptionDecisionState.RECORDED
    )
    assert result.is_recorded is True
    assert result.aligned_readiness is aligned
    assert isinstance(
        result.decision,
        CrossBorderPolicyAdoptionDecision,
    )
    assert (
        result.decision.outcome
        is CrossBorderPolicyAdoptionDecisionOutcome.ADOPT
    )
    assert result.decision.readiness_confirmed is True
    assert result.decision.production_activation_authorized is False
    assert result.reasons == ()


def test_not_ready_adopt_is_rejected_by_canonical_authority():
    aligned = _aligned_available(
        CrossBorderPolicyAdoptionReadinessState.NOT_READY
    )

    with pytest.raises(
        ValueError,
        match="ADOPT requires adoption-ready evidence",
    ):
        record_aligned_cross_border_policy_adoption_decision(
            aligned_readiness=aligned,
            authority=_authority(),
            outcome=CrossBorderPolicyAdoptionDecisionOutcome.ADOPT,
            reason="request adoption",
        )


def test_not_ready_hold_remains_permitted_by_canonical_authority():
    aligned = _aligned_available(
        CrossBorderPolicyAdoptionReadinessState.NOT_READY
    )

    result = record_aligned_cross_border_policy_adoption_decision(
        aligned_readiness=aligned,
        authority=_authority(),
        outcome=CrossBorderPolicyAdoptionDecisionOutcome.HOLD,
        reason="hold pending evidence",
    )

    assert result.decision is not None
    assert (
        result.decision.outcome
        is CrossBorderPolicyAdoptionDecisionOutcome.HOLD
    )
    assert result.decision.readiness_confirmed is False
    assert result.decision.production_activation_authorized is False


def test_not_ready_reject_remains_permitted_by_canonical_authority():
    aligned = _aligned_available(
        CrossBorderPolicyAdoptionReadinessState.NOT_READY
    )

    result = record_aligned_cross_border_policy_adoption_decision(
        aligned_readiness=aligned,
        authority=_authority(),
        outcome=CrossBorderPolicyAdoptionDecisionOutcome.REJECT,
        reason="reject insufficient proposal",
    )

    assert result.decision is not None
    assert (
        result.decision.outcome
        is CrossBorderPolicyAdoptionDecisionOutcome.REJECT
    )
    assert result.decision.readiness_confirmed is False
    assert result.decision.production_activation_authorized is False


@pytest.mark.parametrize(
    "outcome",
    tuple(CrossBorderPolicyAdoptionDecisionOutcome),
)
def test_blocked_provenance_never_invokes_canonical_decision_authority(
    outcome: CrossBorderPolicyAdoptionDecisionOutcome,
):
    aligned = _aligned_blocked()

    target = (
        "app.services.recommendation."
        "cross_border_aligned_scoring_policy_adoption_decision."
        "record_cross_border_policy_adoption_decision"
    )

    with patch(target) as authority:
        result = record_aligned_cross_border_policy_adoption_decision(
            aligned_readiness=aligned,
            authority=_authority(),
            outcome=outcome,
            reason="governance request",
        )

    authority.assert_not_called()

    assert (
        result.state
        is AlignedCrossBorderPolicyAdoptionDecisionState.BLOCKED
    )
    assert result.is_recorded is False
    assert result.decision is None
    assert result.reasons == (
        "aligned_adoption_readiness_not_available",
    )


def test_exact_governance_inputs_are_delegated_unchanged():
    aligned = _aligned_available(
        CrossBorderPolicyAdoptionReadinessState.READY
    )

    readiness = aligned.readiness
    authority = _authority()
    outcome = CrossBorderPolicyAdoptionDecisionOutcome.HOLD
    reason = "explicit governance reason"

    assert readiness is not None

    expected = record_cross_border_policy_adoption_decision(
        readiness=readiness,
        authority=authority,
        outcome=outcome,
        reason=reason,
    )

    target = (
        "app.services.recommendation."
        "cross_border_aligned_scoring_policy_adoption_decision."
        "record_cross_border_policy_adoption_decision"
    )

    with patch(
        target,
        return_value=expected,
    ) as canonical:
        result = record_aligned_cross_border_policy_adoption_decision(
            aligned_readiness=aligned,
            authority=authority,
            outcome=outcome,
            reason=reason,
        )

    canonical.assert_called_once_with(
        readiness=readiness,
        authority=authority,
        outcome=outcome,
        reason=reason,
    )

    assert result.decision is expected


def test_available_without_canonical_readiness_fails_closed():
    aligned = AlignedCrossBorderPolicyAdoptionReadiness(
        state=AlignedCrossBorderPolicyAdoptionReadinessState.AVAILABLE,
        aligned_comparison=None,  # type: ignore[arg-type]
        readiness=None,
        reasons=(),
    )

    with pytest.raises(
        ValueError,
        match="must contain canonical readiness",
    ):
        record_aligned_cross_border_policy_adoption_decision(
            aligned_readiness=aligned,
            authority=_authority(),
            outcome=CrossBorderPolicyAdoptionDecisionOutcome.HOLD,
            reason="hold",
        )


def test_blank_reason_semantics_remain_canonical():
    aligned = _aligned_available(
        CrossBorderPolicyAdoptionReadinessState.READY
    )

    with pytest.raises(
        ValueError,
        match="reason must not be blank",
    ):
        record_aligned_cross_border_policy_adoption_decision(
            aligned_readiness=aligned,
            authority=_authority(),
            outcome=CrossBorderPolicyAdoptionDecisionOutcome.HOLD,
            reason="   ",
        )


def test_result_is_immutable():
    result = record_aligned_cross_border_policy_adoption_decision(
        aligned_readiness=_aligned_available(
            CrossBorderPolicyAdoptionReadinessState.READY
        ),
        authority=_authority(),
        outcome=CrossBorderPolicyAdoptionDecisionOutcome.HOLD,
        reason="hold",
    )

    with pytest.raises(FrozenInstanceError):
        result.reasons = ("changed",)


def test_adapter_exposes_no_activation_scoring_or_ranking_authority():
    result = record_aligned_cross_border_policy_adoption_decision(
        aligned_readiness=_aligned_available(
            CrossBorderPolicyAdoptionReadinessState.READY
        ),
        authority=_authority(),
        outcome=CrossBorderPolicyAdoptionDecisionOutcome.ADOPT,
        reason="adopt",
    )

    forbidden = {
        "activation",
        "activation_authorized",
        "deployment",
        "scoring",
        "score",
        "rank",
        "winner",
        "recommendation",
        "route",
    }

    assert forbidden.isdisjoint(
        vars(result)
    )


def test_adopt_does_not_authorize_production_activation():
    result = record_aligned_cross_border_policy_adoption_decision(
        aligned_readiness=_aligned_available(
            CrossBorderPolicyAdoptionReadinessState.READY
        ),
        authority=_authority(),
        outcome=CrossBorderPolicyAdoptionDecisionOutcome.ADOPT,
        reason="adopt policy",
    )

    assert result.decision is not None
    assert result.decision.production_activation_authorized is False
