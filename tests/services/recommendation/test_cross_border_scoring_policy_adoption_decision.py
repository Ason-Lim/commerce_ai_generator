from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

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


def _readiness(
    *,
    state=CrossBorderPolicyAdoptionReadinessState.READY,
) -> CrossBorderPolicyAdoptionReadiness:
    ready = (
        state
        is CrossBorderPolicyAdoptionReadinessState.READY
    )

    return CrossBorderPolicyAdoptionReadiness(
        state=state,
        baseline_policy_id="baseline-v1",
        candidate_policy_id="candidate-v1",
        comparison_ready=ready,
        policy_identity_ready=ready,
        delta_evidence_ready=ready,
        candidate_identity_ready=ready,
        direction_ready=ready,
        shadow_evidence_ready=ready,
        policy_roles_ready=ready,
        reasons=() if ready else ("comparison",),
    )


def _authority() -> CrossBorderPolicyAdoptionAuthority:
    return CrossBorderPolicyAdoptionAuthority(
        authority_id="recommendation-governance",
        authority_role="policy_adoption_authority",
    )


def test_ready_evidence_can_record_adopt_decision():
    result = record_cross_border_policy_adoption_decision(
        readiness=_readiness(),
        authority=_authority(),
        outcome=(
            CrossBorderPolicyAdoptionDecisionOutcome.ADOPT
        ),
        reason="candidate approved for later activation review",
    )

    assert (
        result.outcome
        is CrossBorderPolicyAdoptionDecisionOutcome.ADOPT
    )

    assert result.readiness_confirmed is True


def test_decision_is_canonical_type():
    result = record_cross_border_policy_adoption_decision(
        readiness=_readiness(),
        authority=_authority(),
        outcome=(
            CrossBorderPolicyAdoptionDecisionOutcome.HOLD
        ),
        reason="additional evaluation requested",
    )

    assert isinstance(
        result,
        CrossBorderPolicyAdoptionDecision,
    )


def test_adopt_does_not_authorize_production_activation():
    result = record_cross_border_policy_adoption_decision(
        readiness=_readiness(),
        authority=_authority(),
        outcome=(
            CrossBorderPolicyAdoptionDecisionOutcome.ADOPT
        ),
        reason="adoption decision recorded",
    )

    assert (
        result.production_activation_authorized
        is False
    )


def test_not_ready_evidence_cannot_be_adopted():
    with pytest.raises(
        ValueError,
        match="requires adoption-ready evidence",
    ):
        record_cross_border_policy_adoption_decision(
            readiness=_readiness(
                state=(
                    CrossBorderPolicyAdoptionReadinessState.NOT_READY
                )
            ),
            authority=_authority(),
            outcome=(
                CrossBorderPolicyAdoptionDecisionOutcome.ADOPT
            ),
            reason="attempted adoption",
        )


def test_not_ready_evidence_can_be_held():
    result = record_cross_border_policy_adoption_decision(
        readiness=_readiness(
            state=(
                CrossBorderPolicyAdoptionReadinessState.NOT_READY
            )
        ),
        authority=_authority(),
        outcome=(
            CrossBorderPolicyAdoptionDecisionOutcome.HOLD
        ),
        reason="evidence incomplete",
    )

    assert (
        result.outcome
        is CrossBorderPolicyAdoptionDecisionOutcome.HOLD
    )

    assert result.readiness_confirmed is False


def test_not_ready_evidence_can_be_rejected():
    result = record_cross_border_policy_adoption_decision(
        readiness=_readiness(
            state=(
                CrossBorderPolicyAdoptionReadinessState.NOT_READY
            )
        ),
        authority=_authority(),
        outcome=(
            CrossBorderPolicyAdoptionDecisionOutcome.REJECT
        ),
        reason="evidence insufficient",
    )

    assert (
        result.outcome
        is CrossBorderPolicyAdoptionDecisionOutcome.REJECT
    )


def test_ready_evidence_does_not_force_adoption():
    result = record_cross_border_policy_adoption_decision(
        readiness=_readiness(),
        authority=_authority(),
        outcome=(
            CrossBorderPolicyAdoptionDecisionOutcome.HOLD
        ),
        reason="more shadow evidence requested",
    )

    assert (
        result.outcome
        is CrossBorderPolicyAdoptionDecisionOutcome.HOLD
    )


def test_ready_evidence_can_still_be_rejected():
    result = record_cross_border_policy_adoption_decision(
        readiness=_readiness(),
        authority=_authority(),
        outcome=(
            CrossBorderPolicyAdoptionDecisionOutcome.REJECT
        ),
        reason="candidate policy not accepted",
    )

    assert (
        result.outcome
        is CrossBorderPolicyAdoptionDecisionOutcome.REJECT
    )


def test_policy_identity_is_preserved():
    result = record_cross_border_policy_adoption_decision(
        readiness=_readiness(),
        authority=_authority(),
        outcome=(
            CrossBorderPolicyAdoptionDecisionOutcome.HOLD
        ),
        reason="review pending",
    )

    assert result.baseline_policy_id == "baseline-v1"
    assert result.candidate_policy_id == "candidate-v1"


def test_authority_identity_is_preserved():
    result = record_cross_border_policy_adoption_decision(
        readiness=_readiness(),
        authority=_authority(),
        outcome=(
            CrossBorderPolicyAdoptionDecisionOutcome.HOLD
        ),
        reason="review pending",
    )

    assert (
        result.authority_id
        == "recommendation-governance"
    )

    assert (
        result.authority_role
        == "policy_adoption_authority"
    )


def test_authority_fields_are_normalized():
    authority = CrossBorderPolicyAdoptionAuthority(
        authority_id="  governance  ",
        authority_role="  adoption_authority  ",
    )

    assert authority.authority_id == "governance"
    assert authority.authority_role == "adoption_authority"


def test_blank_authority_id_is_rejected():
    with pytest.raises(
        ValueError,
        match="authority_id",
    ):
        CrossBorderPolicyAdoptionAuthority(
            authority_id=" ",
            authority_role="role",
        )


def test_blank_authority_role_is_rejected():
    with pytest.raises(
        ValueError,
        match="authority_role",
    ):
        CrossBorderPolicyAdoptionAuthority(
            authority_id="authority",
            authority_role=" ",
        )


def test_reason_is_normalized():
    result = record_cross_border_policy_adoption_decision(
        readiness=_readiness(),
        authority=_authority(),
        outcome=(
            CrossBorderPolicyAdoptionDecisionOutcome.HOLD
        ),
        reason="  additional review required  ",
    )

    assert (
        result.reason
        == "additional review required"
    )


def test_blank_reason_is_rejected():
    with pytest.raises(
        ValueError,
        match="reason",
    ):
        record_cross_border_policy_adoption_decision(
            readiness=_readiness(),
            authority=_authority(),
            outcome=(
                CrossBorderPolicyAdoptionDecisionOutcome.HOLD
            ),
            reason=" ",
        )


def test_outcome_vocabulary_is_bounded():
    assert {
        outcome.value
        for outcome in CrossBorderPolicyAdoptionDecisionOutcome
    } == {
        "adopt",
        "hold",
        "reject",
    }


def test_authority_is_immutable():
    authority = _authority()

    with pytest.raises(
        FrozenInstanceError,
    ):
        authority.authority_id = "changed"


def test_decision_is_immutable():
    result = record_cross_border_policy_adoption_decision(
        readiness=_readiness(),
        authority=_authority(),
        outcome=(
            CrossBorderPolicyAdoptionDecisionOutcome.HOLD
        ),
        reason="pending",
    )

    with pytest.raises(
        FrozenInstanceError,
    ):
        result.reason = "changed"


def test_decision_has_no_score_surface():
    result = record_cross_border_policy_adoption_decision(
        readiness=_readiness(),
        authority=_authority(),
        outcome=(
            CrossBorderPolicyAdoptionDecisionOutcome.ADOPT
        ),
        reason="governance decision",
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
    result = record_cross_border_policy_adoption_decision(
        readiness=_readiness(),
        authority=_authority(),
        outcome=(
            CrossBorderPolicyAdoptionDecisionOutcome.ADOPT
        ),
        reason="governance decision",
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
    result = record_cross_border_policy_adoption_decision(
        readiness=_readiness(),
        authority=_authority(),
        outcome=(
            CrossBorderPolicyAdoptionDecisionOutcome.ADOPT
        ),
        reason="governance decision",
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


def test_decision_has_no_deployment_surface():
    result = record_cross_border_policy_adoption_decision(
        readiness=_readiness(),
        authority=_authority(),
        outcome=(
            CrossBorderPolicyAdoptionDecisionOutcome.ADOPT
        ),
        reason="governance decision",
    )

    forbidden = {
        "deploy",
        "activate",
        "rollout",
        "traffic_percentage",
        "production_enabled",
    }

    public_names = {
        name.lower()
        for name in dir(result)
        if not name.startswith("_")
    }

    assert forbidden.isdisjoint(public_names)


def test_decision_has_no_transaction_surface():
    result = record_cross_border_policy_adoption_decision(
        readiness=_readiness(),
        authority=_authority(),
        outcome=(
            CrossBorderPolicyAdoptionDecisionOutcome.ADOPT
        ),
        reason="governance decision",
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

    record_cross_border_policy_adoption_decision(
        readiness=readiness,
        authority=_authority(),
        outcome=(
            CrossBorderPolicyAdoptionDecisionOutcome.HOLD
        ),
        reason="review",
    )

    assert readiness.state is original_state


def test_decision_does_not_mutate_authority():
    authority = _authority()

    original_id = authority.authority_id

    record_cross_border_policy_adoption_decision(
        readiness=_readiness(),
        authority=authority,
        outcome=(
            CrossBorderPolicyAdoptionDecisionOutcome.HOLD
        ),
        reason="review",
    )

    assert authority.authority_id == original_id
