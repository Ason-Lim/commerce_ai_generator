from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from app.services.recommendation.cross_border_scoring_policy_activation_decision import (
    CrossBorderPolicyActivationAuthority,
    CrossBorderPolicyActivationDecision,
    CrossBorderPolicyActivationDecisionOutcome,
    record_cross_border_policy_activation_decision,
)
from app.services.recommendation.cross_border_scoring_policy_activation_readiness import (
    CrossBorderPolicyActivationReadiness,
    CrossBorderPolicyActivationReadinessState,
)


def _readiness(
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


def _authority() -> CrossBorderPolicyActivationAuthority:
    return CrossBorderPolicyActivationAuthority(
        authority_id="production-governance",
        authority_role="policy_activation_authority",
    )


def test_ready_evidence_can_record_authorize_decision():
    result = record_cross_border_policy_activation_decision(
        readiness=_readiness(),
        authority=_authority(),
        outcome=(
            CrossBorderPolicyActivationDecisionOutcome.AUTHORIZE
        ),
        reason="approved for controlled activation review",
    )

    assert (
        result.outcome
        is CrossBorderPolicyActivationDecisionOutcome.AUTHORIZE
    )

    assert result.activation_readiness_confirmed is True


def test_decision_is_canonical_type():
    result = record_cross_border_policy_activation_decision(
        readiness=_readiness(),
        authority=_authority(),
        outcome=(
            CrossBorderPolicyActivationDecisionOutcome.HOLD
        ),
        reason="additional review requested",
    )

    assert isinstance(
        result,
        CrossBorderPolicyActivationDecision,
    )


def test_authorize_does_not_enable_production():
    result = record_cross_border_policy_activation_decision(
        readiness=_readiness(),
        authority=_authority(),
        outcome=(
            CrossBorderPolicyActivationDecisionOutcome.AUTHORIZE
        ),
        reason="authorization recorded",
    )

    assert result.production_enabled is False
    assert result.rollout_started is False
    assert result.traffic_routed is False


def test_not_ready_cannot_be_authorized():
    with pytest.raises(
        ValueError,
        match="requires activation-ready evidence",
    ):
        record_cross_border_policy_activation_decision(
            readiness=_readiness(
                state=(
                    CrossBorderPolicyActivationReadinessState.NOT_READY
                )
            ),
            authority=_authority(),
            outcome=(
                CrossBorderPolicyActivationDecisionOutcome.AUTHORIZE
            ),
            reason="attempted authorization",
        )


def test_not_ready_can_be_held():
    result = record_cross_border_policy_activation_decision(
        readiness=_readiness(
            state=(
                CrossBorderPolicyActivationReadinessState.NOT_READY
            )
        ),
        authority=_authority(),
        outcome=(
            CrossBorderPolicyActivationDecisionOutcome.HOLD
        ),
        reason="activation evidence incomplete",
    )

    assert (
        result.outcome
        is CrossBorderPolicyActivationDecisionOutcome.HOLD
    )

    assert result.activation_readiness_confirmed is False


def test_not_ready_can_be_denied():
    result = record_cross_border_policy_activation_decision(
        readiness=_readiness(
            state=(
                CrossBorderPolicyActivationReadinessState.NOT_READY
            )
        ),
        authority=_authority(),
        outcome=(
            CrossBorderPolicyActivationDecisionOutcome.DENY
        ),
        reason="activation evidence rejected",
    )

    assert (
        result.outcome
        is CrossBorderPolicyActivationDecisionOutcome.DENY
    )


def test_ready_does_not_force_authorization():
    result = record_cross_border_policy_activation_decision(
        readiness=_readiness(),
        authority=_authority(),
        outcome=(
            CrossBorderPolicyActivationDecisionOutcome.HOLD
        ),
        reason="additional controls requested",
    )

    assert (
        result.outcome
        is CrossBorderPolicyActivationDecisionOutcome.HOLD
    )


def test_ready_can_still_be_denied():
    result = record_cross_border_policy_activation_decision(
        readiness=_readiness(),
        authority=_authority(),
        outcome=(
            CrossBorderPolicyActivationDecisionOutcome.DENY
        ),
        reason="activation not accepted",
    )

    assert (
        result.outcome
        is CrossBorderPolicyActivationDecisionOutcome.DENY
    )


def test_policy_identity_is_preserved():
    result = record_cross_border_policy_activation_decision(
        readiness=_readiness(),
        authority=_authority(),
        outcome=(
            CrossBorderPolicyActivationDecisionOutcome.HOLD
        ),
        reason="pending",
    )

    assert result.baseline_policy_id == "baseline-v1"
    assert result.candidate_policy_id == "candidate-v1"


def test_adoption_authority_identity_is_preserved():
    result = record_cross_border_policy_activation_decision(
        readiness=_readiness(),
        authority=_authority(),
        outcome=(
            CrossBorderPolicyActivationDecisionOutcome.HOLD
        ),
        reason="pending",
    )

    assert (
        result.adoption_authority_id
        == "recommendation-governance"
    )

    assert (
        result.adoption_authority_role
        == "policy_adoption_authority"
    )


def test_activation_authority_identity_is_preserved():
    result = record_cross_border_policy_activation_decision(
        readiness=_readiness(),
        authority=_authority(),
        outcome=(
            CrossBorderPolicyActivationDecisionOutcome.HOLD
        ),
        reason="pending",
    )

    assert (
        result.activation_authority_id
        == "production-governance"
    )

    assert (
        result.activation_authority_role
        == "policy_activation_authority"
    )


def test_authority_identity_is_normalized():
    authority = CrossBorderPolicyActivationAuthority(
        authority_id="  production  ",
        authority_role="  activation_authority  ",
    )

    assert authority.authority_id == "production"
    assert authority.authority_role == "activation_authority"


def test_blank_authority_id_is_rejected():
    with pytest.raises(
        ValueError,
        match="authority_id",
    ):
        CrossBorderPolicyActivationAuthority(
            authority_id=" ",
            authority_role="role",
        )


def test_blank_authority_role_is_rejected():
    with pytest.raises(
        ValueError,
        match="authority_role",
    ):
        CrossBorderPolicyActivationAuthority(
            authority_id="authority",
            authority_role=" ",
        )


def test_reason_is_normalized():
    result = record_cross_border_policy_activation_decision(
        readiness=_readiness(),
        authority=_authority(),
        outcome=(
            CrossBorderPolicyActivationDecisionOutcome.HOLD
        ),
        reason="  additional controls required  ",
    )

    assert (
        result.reason
        == "additional controls required"
    )


def test_blank_reason_is_rejected():
    with pytest.raises(
        ValueError,
        match="reason",
    ):
        record_cross_border_policy_activation_decision(
            readiness=_readiness(),
            authority=_authority(),
            outcome=(
                CrossBorderPolicyActivationDecisionOutcome.HOLD
            ),
            reason=" ",
        )


def test_outcome_vocabulary_is_bounded():
    assert {
        outcome.value
        for outcome in CrossBorderPolicyActivationDecisionOutcome
    } == {
        "authorize",
        "hold",
        "deny",
    }


def test_authority_is_immutable():
    authority = _authority()

    with pytest.raises(
        FrozenInstanceError,
    ):
        authority.authority_id = "changed"


def test_decision_is_immutable():
    result = record_cross_border_policy_activation_decision(
        readiness=_readiness(),
        authority=_authority(),
        outcome=(
            CrossBorderPolicyActivationDecisionOutcome.HOLD
        ),
        reason="pending",
    )

    with pytest.raises(
        FrozenInstanceError,
    ):
        result.reason = "changed"


def test_decision_has_no_score_surface():
    result = record_cross_border_policy_activation_decision(
        readiness=_readiness(),
        authority=_authority(),
        outcome=(
            CrossBorderPolicyActivationDecisionOutcome.AUTHORIZE
        ),
        reason="governance authorization",
    )

    forbidden = {
        "score",
        "final_score",
        "production_score",
        "price_score",
        "score_delta",
        "apply_score",
    }

    public_names = {
        name.lower()
        for name in dir(result)
        if not name.startswith("_")
    }

    assert forbidden.isdisjoint(public_names)


def test_decision_has_no_ranking_surface():
    result = record_cross_border_policy_activation_decision(
        readiness=_readiness(),
        authority=_authority(),
        outcome=(
            CrossBorderPolicyActivationDecisionOutcome.AUTHORIZE
        ),
        reason="governance authorization",
    )

    forbidden = {
        "rank",
        "ranking",
        "winner",
        "best_candidate",
        "selected_candidate",
    }

    public_names = {
        name.lower()
        for name in dir(result)
        if not name.startswith("_")
    }

    assert forbidden.isdisjoint(public_names)


def test_decision_has_no_recommendation_surface():
    result = record_cross_border_policy_activation_decision(
        readiness=_readiness(),
        authority=_authority(),
        outcome=(
            CrossBorderPolicyActivationDecisionOutcome.AUTHORIZE
        ),
        reason="governance authorization",
    )

    forbidden = {
        "recommend",
        "recommended_candidate",
        "preferred_candidate",
        "priority",
    }

    public_names = {
        name.lower()
        for name in dir(result)
        if not name.startswith("_")
    }

    assert forbidden.isdisjoint(public_names)


def test_authorize_has_no_rollout_control_surface():
    result = record_cross_border_policy_activation_decision(
        readiness=_readiness(),
        authority=_authority(),
        outcome=(
            CrossBorderPolicyActivationDecisionOutcome.AUTHORIZE
        ),
        reason="governance authorization",
    )

    forbidden = {
        "rollout_percentage",
        "traffic_percentage",
        "route_traffic",
        "enable_runtime",
        "activate_runtime",
    }

    public_names = {
        name.lower()
        for name in dir(result)
        if not name.startswith("_")
    }

    assert forbidden.isdisjoint(public_names)


def test_decision_has_no_transaction_surface():
    result = record_cross_border_policy_activation_decision(
        readiness=_readiness(),
        authority=_authority(),
        outcome=(
            CrossBorderPolicyActivationDecisionOutcome.AUTHORIZE
        ),
        reason="governance authorization",
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

    assert forbidden.isdisjoint(public_names)


def test_decision_does_not_mutate_readiness():
    readiness = _readiness()

    original_state = readiness.state
    original_candidate = readiness.candidate_policy_id

    record_cross_border_policy_activation_decision(
        readiness=readiness,
        authority=_authority(),
        outcome=(
            CrossBorderPolicyActivationDecisionOutcome.HOLD
        ),
        reason="review",
    )

    assert readiness.state is original_state
    assert readiness.candidate_policy_id == original_candidate


def test_decision_does_not_mutate_authority():
    authority = _authority()

    original_id = authority.authority_id

    record_cross_border_policy_activation_decision(
        readiness=_readiness(),
        authority=authority,
        outcome=(
            CrossBorderPolicyActivationDecisionOutcome.HOLD
        ),
        reason="review",
    )

    assert authority.authority_id == original_id
