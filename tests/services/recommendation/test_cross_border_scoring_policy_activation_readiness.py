from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from app.services.recommendation.cross_border_scoring_policy_activation_readiness import (
    CrossBorderPolicyActivationReadiness,
    CrossBorderPolicyActivationReadinessState,
    evaluate_cross_border_policy_activation_readiness,
)
from app.services.recommendation.cross_border_scoring_policy_adoption_decision import (
    CrossBorderPolicyAdoptionDecision,
    CrossBorderPolicyAdoptionDecisionOutcome,
)


def _decision(
    **overrides,
) -> CrossBorderPolicyAdoptionDecision:
    values = {
        "outcome": (
            CrossBorderPolicyAdoptionDecisionOutcome.ADOPT
        ),
        "baseline_policy_id": "baseline-v1",
        "candidate_policy_id": "candidate-v1",
        "authority_id": "recommendation-governance",
        "authority_role": "policy_adoption_authority",
        "readiness_confirmed": True,
        "reason": "adoption decision recorded",
        "production_activation_authorized": False,
    }

    values.update(overrides)

    return CrossBorderPolicyAdoptionDecision(
        **values
    )


def test_valid_adopt_decision_is_activation_ready():
    result = (
        evaluate_cross_border_policy_activation_readiness(
            _decision()
        )
    )

    assert (
        result.state
        is CrossBorderPolicyActivationReadinessState.READY
    )

    assert result.reasons == ()


def test_result_is_canonical_activation_readiness_type():
    result = (
        evaluate_cross_border_policy_activation_readiness(
            _decision()
        )
    )

    assert isinstance(
        result,
        CrossBorderPolicyActivationReadiness,
    )


def test_all_readiness_dimensions_are_true():
    result = (
        evaluate_cross_border_policy_activation_readiness(
            _decision()
        )
    )

    assert result.adoption_decision_ready is True
    assert result.readiness_evidence_ready is True
    assert result.policy_identity_ready is True
    assert result.authority_identity_ready is True
    assert result.activation_boundary_ready is True


def test_hold_decision_is_not_activation_ready():
    result = (
        evaluate_cross_border_policy_activation_readiness(
            _decision(
                outcome=(
                    CrossBorderPolicyAdoptionDecisionOutcome.HOLD
                )
            )
        )
    )

    assert (
        result.state
        is CrossBorderPolicyActivationReadinessState.NOT_READY
    )

    assert "adoption_decision" in result.reasons


def test_reject_decision_is_not_activation_ready():
    result = (
        evaluate_cross_border_policy_activation_readiness(
            _decision(
                outcome=(
                    CrossBorderPolicyAdoptionDecisionOutcome.REJECT
                )
            )
        )
    )

    assert (
        result.state
        is CrossBorderPolicyActivationReadinessState.NOT_READY
    )

    assert "adoption_decision" in result.reasons


def test_unconfirmed_readiness_is_not_activation_ready():
    result = (
        evaluate_cross_border_policy_activation_readiness(
            _decision(
                readiness_confirmed=False,
            )
        )
    )

    assert (
        result.state
        is CrossBorderPolicyActivationReadinessState.NOT_READY
    )

    assert "readiness_evidence" in result.reasons


def test_blank_baseline_policy_id_is_not_ready():
    result = (
        evaluate_cross_border_policy_activation_readiness(
            _decision(
                baseline_policy_id=" ",
            )
        )
    )

    assert (
        result.state
        is CrossBorderPolicyActivationReadinessState.NOT_READY
    )

    assert "policy_identity" in result.reasons


def test_blank_candidate_policy_id_is_not_ready():
    result = (
        evaluate_cross_border_policy_activation_readiness(
            _decision(
                candidate_policy_id=" ",
            )
        )
    )

    assert (
        result.state
        is CrossBorderPolicyActivationReadinessState.NOT_READY
    )

    assert "policy_identity" in result.reasons


def test_same_policy_identity_is_not_ready():
    result = (
        evaluate_cross_border_policy_activation_readiness(
            _decision(
                candidate_policy_id="baseline-v1",
            )
        )
    )

    assert (
        result.state
        is CrossBorderPolicyActivationReadinessState.NOT_READY
    )

    assert "policy_identity" in result.reasons


def test_blank_authority_id_is_not_ready():
    result = (
        evaluate_cross_border_policy_activation_readiness(
            _decision(
                authority_id=" ",
            )
        )
    )

    assert (
        result.state
        is CrossBorderPolicyActivationReadinessState.NOT_READY
    )

    assert "authority_identity" in result.reasons


def test_blank_authority_role_is_not_ready():
    result = (
        evaluate_cross_border_policy_activation_readiness(
            _decision(
                authority_role=" ",
            )
        )
    )

    assert (
        result.state
        is CrossBorderPolicyActivationReadinessState.NOT_READY
    )

    assert "authority_identity" in result.reasons


def test_existing_activation_authorization_is_not_ready():
    result = (
        evaluate_cross_border_policy_activation_readiness(
            _decision(
                production_activation_authorized=True,
            )
        )
    )

    assert (
        result.state
        is CrossBorderPolicyActivationReadinessState.NOT_READY
    )

    assert "activation_boundary" in result.reasons


def test_policy_ids_are_normalized():
    result = (
        evaluate_cross_border_policy_activation_readiness(
            _decision(
                baseline_policy_id="  baseline-v1  ",
                candidate_policy_id="  candidate-v1  ",
            )
        )
    )

    assert result.baseline_policy_id == "baseline-v1"
    assert result.candidate_policy_id == "candidate-v1"


def test_authority_identity_is_normalized():
    result = (
        evaluate_cross_border_policy_activation_readiness(
            _decision(
                authority_id="  governance  ",
                authority_role="  policy_authority  ",
            )
        )
    )

    assert result.authority_id == "governance"
    assert result.authority_role == "policy_authority"


def test_multiple_failures_are_reported():
    result = (
        evaluate_cross_border_policy_activation_readiness(
            _decision(
                outcome=(
                    CrossBorderPolicyAdoptionDecisionOutcome.HOLD
                ),
                readiness_confirmed=False,
                candidate_policy_id="baseline-v1",
                authority_id=" ",
                authority_role=" ",
                production_activation_authorized=True,
            )
        )
    )

    assert set(result.reasons) == {
        "adoption_decision",
        "readiness_evidence",
        "policy_identity",
        "authority_identity",
        "activation_boundary",
    }


def test_readiness_state_vocabulary_is_bounded():
    assert {
        state.value
        for state in CrossBorderPolicyActivationReadinessState
    } == {
        "ready",
        "not_ready",
    }


def test_result_is_immutable():
    result = (
        evaluate_cross_border_policy_activation_readiness(
            _decision()
        )
    )

    with pytest.raises(
        FrozenInstanceError,
    ):
        result.state = (
            CrossBorderPolicyActivationReadinessState.NOT_READY
        )


def test_ready_does_not_create_activation_authority():
    result = (
        evaluate_cross_border_policy_activation_readiness(
            _decision()
        )
    )

    forbidden = {
        "activate",
        "activate_policy",
        "activation_authorized",
        "production_enabled",
        "deploy",
        "rollout",
        "traffic_percentage",
    }

    public_names = {
        name.lower()
        for name in dir(result)
        if not name.startswith("_")
    }

    assert forbidden.isdisjoint(public_names)


def test_result_has_no_score_surface():
    result = (
        evaluate_cross_border_policy_activation_readiness(
            _decision()
        )
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


def test_result_has_no_ranking_surface():
    result = (
        evaluate_cross_border_policy_activation_readiness(
            _decision()
        )
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


def test_result_has_no_recommendation_surface():
    result = (
        evaluate_cross_border_policy_activation_readiness(
            _decision()
        )
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


def test_result_has_no_transaction_surface():
    result = (
        evaluate_cross_border_policy_activation_readiness(
            _decision()
        )
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


def test_evaluation_does_not_mutate_decision():
    decision = _decision()

    original_outcome = decision.outcome
    original_candidate = decision.candidate_policy_id

    evaluate_cross_border_policy_activation_readiness(
        decision
    )

    assert decision.outcome is original_outcome
    assert decision.candidate_policy_id == original_candidate
