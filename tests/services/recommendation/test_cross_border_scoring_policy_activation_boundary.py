from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

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
    **overrides,
) -> CrossBorderPolicyActivationDecision:
    values = {
        "outcome": (
            CrossBorderPolicyActivationDecisionOutcome.AUTHORIZE
        ),
        "baseline_policy_id": "baseline-v1",
        "candidate_policy_id": "candidate-v1",
        "adoption_authority_id": "recommendation-governance",
        "adoption_authority_role": "policy_adoption_authority",
        "activation_authority_id": "production-governance",
        "activation_authority_role": "policy_activation_authority",
        "activation_readiness_confirmed": True,
        "reason": "controlled activation authorized",
        "production_enabled": False,
        "rollout_started": False,
        "traffic_routed": False,
    }

    values.update(overrides)

    return CrossBorderPolicyActivationDecision(
        **values
    )


def test_authorized_safe_decision_is_eligible():
    result = (
        evaluate_cross_border_scoring_activation_boundary(
            _decision()
        )
    )

    assert (
        result.state
        is CrossBorderActivationBoundaryState.ELIGIBLE
    )

    assert result.reasons == ()


def test_result_is_canonical_boundary_type():
    result = (
        evaluate_cross_border_scoring_activation_boundary(
            _decision()
        )
    )

    assert isinstance(
        result,
        CrossBorderScoringActivationBoundary,
    )


def test_all_boundary_dimensions_are_true_when_eligible():
    result = (
        evaluate_cross_border_scoring_activation_boundary(
            _decision()
        )
    )

    assert result.authorization_ready is True
    assert result.policy_identity_ready is True
    assert result.authority_identity_ready is True
    assert result.activation_state_safe is True


def test_hold_decision_falls_back():
    result = (
        evaluate_cross_border_scoring_activation_boundary(
            _decision(
                outcome=(
                    CrossBorderPolicyActivationDecisionOutcome.HOLD
                )
            )
        )
    )

    assert (
        result.state
        is CrossBorderActivationBoundaryState.FALLBACK
    )

    assert "authorization" in result.reasons


def test_deny_decision_falls_back():
    result = (
        evaluate_cross_border_scoring_activation_boundary(
            _decision(
                outcome=(
                    CrossBorderPolicyActivationDecisionOutcome.DENY
                )
            )
        )
    )

    assert (
        result.state
        is CrossBorderActivationBoundaryState.FALLBACK
    )

    assert "authorization" in result.reasons


def test_unconfirmed_activation_readiness_falls_back():
    result = (
        evaluate_cross_border_scoring_activation_boundary(
            _decision(
                activation_readiness_confirmed=False,
            )
        )
    )

    assert (
        result.state
        is CrossBorderActivationBoundaryState.FALLBACK
    )

    assert "authorization" in result.reasons


def test_blank_baseline_policy_id_falls_back():
    result = (
        evaluate_cross_border_scoring_activation_boundary(
            _decision(
                baseline_policy_id=" ",
            )
        )
    )

    assert (
        result.state
        is CrossBorderActivationBoundaryState.FALLBACK
    )

    assert "policy_identity" in result.reasons


def test_blank_candidate_policy_id_falls_back():
    result = (
        evaluate_cross_border_scoring_activation_boundary(
            _decision(
                candidate_policy_id=" ",
            )
        )
    )

    assert (
        result.state
        is CrossBorderActivationBoundaryState.FALLBACK
    )

    assert "policy_identity" in result.reasons


def test_same_policy_identity_falls_back():
    result = (
        evaluate_cross_border_scoring_activation_boundary(
            _decision(
                candidate_policy_id="baseline-v1",
            )
        )
    )

    assert (
        result.state
        is CrossBorderActivationBoundaryState.FALLBACK
    )

    assert "policy_identity" in result.reasons


def test_blank_activation_authority_id_falls_back():
    result = (
        evaluate_cross_border_scoring_activation_boundary(
            _decision(
                activation_authority_id=" ",
            )
        )
    )

    assert (
        result.state
        is CrossBorderActivationBoundaryState.FALLBACK
    )

    assert "authority_identity" in result.reasons


def test_blank_activation_authority_role_falls_back():
    result = (
        evaluate_cross_border_scoring_activation_boundary(
            _decision(
                activation_authority_role=" ",
            )
        )
    )

    assert (
        result.state
        is CrossBorderActivationBoundaryState.FALLBACK
    )

    assert "authority_identity" in result.reasons


def test_already_enabled_production_falls_back():
    result = (
        evaluate_cross_border_scoring_activation_boundary(
            _decision(
                production_enabled=True,
            )
        )
    )

    assert (
        result.state
        is CrossBorderActivationBoundaryState.FALLBACK
    )

    assert "activation_state" in result.reasons


def test_rollout_already_started_falls_back():
    result = (
        evaluate_cross_border_scoring_activation_boundary(
            _decision(
                rollout_started=True,
            )
        )
    )

    assert (
        result.state
        is CrossBorderActivationBoundaryState.FALLBACK
    )

    assert "activation_state" in result.reasons


def test_traffic_already_routed_falls_back():
    result = (
        evaluate_cross_border_scoring_activation_boundary(
            _decision(
                traffic_routed=True,
            )
        )
    )

    assert (
        result.state
        is CrossBorderActivationBoundaryState.FALLBACK
    )

    assert "activation_state" in result.reasons


def test_policy_ids_are_normalized():
    result = (
        evaluate_cross_border_scoring_activation_boundary(
            _decision(
                baseline_policy_id="  baseline-v1  ",
                candidate_policy_id="  candidate-v1  ",
            )
        )
    )

    assert result.baseline_policy_id == "baseline-v1"
    assert result.candidate_policy_id == "candidate-v1"


def test_activation_authority_identity_is_normalized():
    result = (
        evaluate_cross_border_scoring_activation_boundary(
            _decision(
                activation_authority_id="  production  ",
                activation_authority_role="  activation  ",
            )
        )
    )

    assert result.activation_authority_id == "production"
    assert result.activation_authority_role == "activation"


def test_multiple_failures_are_reported():
    result = (
        evaluate_cross_border_scoring_activation_boundary(
            _decision(
                outcome=(
                    CrossBorderPolicyActivationDecisionOutcome.HOLD
                ),
                activation_readiness_confirmed=False,
                candidate_policy_id="baseline-v1",
                activation_authority_id=" ",
                activation_authority_role=" ",
                production_enabled=True,
                rollout_started=True,
                traffic_routed=True,
            )
        )
    )

    assert set(result.reasons) == {
        "authorization",
        "policy_identity",
        "authority_identity",
        "activation_state",
    }


def test_state_vocabulary_is_bounded():
    assert {
        state.value
        for state in CrossBorderActivationBoundaryState
    } == {
        "eligible",
        "fallback",
    }


def test_result_is_immutable():
    result = (
        evaluate_cross_border_scoring_activation_boundary(
            _decision()
        )
    )

    with pytest.raises(
        FrozenInstanceError,
    ):
        result.state = (
            CrossBorderActivationBoundaryState.FALLBACK
        )


def test_eligible_has_no_runtime_activation_surface():
    result = (
        evaluate_cross_border_scoring_activation_boundary(
            _decision()
        )
    )

    forbidden = {
        "activate",
        "activate_runtime",
        "enable_runtime",
        "production_enabled",
        "rollout_started",
        "traffic_routed",
        "traffic_percentage",
        "rollout_percentage",
    }

    public_names = {
        name.lower()
        for name in dir(result)
        if not name.startswith("_")
    }

    assert forbidden.isdisjoint(public_names)


def test_result_has_no_score_surface():
    result = (
        evaluate_cross_border_scoring_activation_boundary(
            _decision()
        )
    )

    forbidden = {
        "score",
        "final_score",
        "production_score",
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
        evaluate_cross_border_scoring_activation_boundary(
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
        evaluate_cross_border_scoring_activation_boundary(
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
        evaluate_cross_border_scoring_activation_boundary(
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

    evaluate_cross_border_scoring_activation_boundary(
        decision
    )

    assert decision.outcome is original_outcome
    assert decision.candidate_policy_id == original_candidate
