from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from app.services.recommendation.cross_border_scoring_policy_activation_boundary import (
    CrossBorderActivationBoundaryState,
    CrossBorderScoringActivationBoundary,
)
from app.services.recommendation.cross_border_scoring_policy_fallback import (
    CrossBorderScoringFallbackDecision,
    CrossBorderScoringFallbackTarget,
    evaluate_cross_border_scoring_fallback,
)


def _boundary(
    **overrides,
) -> CrossBorderScoringActivationBoundary:
    values = {
        "state": CrossBorderActivationBoundaryState.ELIGIBLE,
        "baseline_policy_id": "baseline-v1",
        "candidate_policy_id": "candidate-v1",
        "activation_authority_id": "production-governance",
        "activation_authority_role": "policy_activation_authority",
        "authorization_ready": True,
        "policy_identity_ready": True,
        "authority_identity_ready": True,
        "activation_state_safe": True,
        "reasons": (),
    }

    values.update(overrides)

    return CrossBorderScoringActivationBoundary(
        **values
    )


def test_eligible_boundary_selects_candidate_path():
    result = evaluate_cross_border_scoring_fallback(
        _boundary()
    )

    assert (
        result.target
        is CrossBorderScoringFallbackTarget.CANDIDATE
    )

    assert result.fallback_required is False
    assert result.activation_allowed is True
    assert result.fallback_reason is None


def test_result_is_canonical_type():
    result = evaluate_cross_border_scoring_fallback(
        _boundary()
    )

    assert isinstance(
        result,
        CrossBorderScoringFallbackDecision,
    )


def test_fallback_boundary_selects_baseline():
    result = evaluate_cross_border_scoring_fallback(
        _boundary(
            state=CrossBorderActivationBoundaryState.FALLBACK,
            authorization_ready=False,
            reasons=("authorization",),
        )
    )

    assert (
        result.target
        is CrossBorderScoringFallbackTarget.BASELINE
    )

    assert result.fallback_required is True
    assert result.activation_allowed is False


def test_blank_baseline_policy_forces_baseline():
    result = evaluate_cross_border_scoring_fallback(
        _boundary(
            baseline_policy_id=" ",
        )
    )

    assert (
        result.target
        is CrossBorderScoringFallbackTarget.BASELINE
    )

    assert "policy_identity" in result.fallback_reason


def test_blank_candidate_policy_forces_baseline():
    result = evaluate_cross_border_scoring_fallback(
        _boundary(
            candidate_policy_id=" ",
        )
    )

    assert (
        result.target
        is CrossBorderScoringFallbackTarget.BASELINE
    )

    assert "policy_identity" in result.fallback_reason


def test_same_policy_identity_forces_baseline():
    result = evaluate_cross_border_scoring_fallback(
        _boundary(
            candidate_policy_id="baseline-v1",
        )
    )

    assert (
        result.target
        is CrossBorderScoringFallbackTarget.BASELINE
    )

    assert "policy_identity" in result.fallback_reason


def test_false_policy_identity_flag_forces_baseline():
    result = evaluate_cross_border_scoring_fallback(
        _boundary(
            policy_identity_ready=False,
        )
    )

    assert (
        result.target
        is CrossBorderScoringFallbackTarget.BASELINE
    )


def test_false_authority_identity_flag_forces_baseline():
    result = evaluate_cross_border_scoring_fallback(
        _boundary(
            authority_identity_ready=False,
        )
    )

    assert (
        result.target
        is CrossBorderScoringFallbackTarget.BASELINE
    )

    assert "authority_identity" in result.fallback_reason


def test_blank_authority_id_forces_baseline():
    result = evaluate_cross_border_scoring_fallback(
        _boundary(
            activation_authority_id=" ",
        )
    )

    assert (
        result.target
        is CrossBorderScoringFallbackTarget.BASELINE
    )

    assert "authority_identity" in result.fallback_reason


def test_blank_authority_role_forces_baseline():
    result = evaluate_cross_border_scoring_fallback(
        _boundary(
            activation_authority_role=" ",
        )
    )

    assert (
        result.target
        is CrossBorderScoringFallbackTarget.BASELINE
    )

    assert "authority_identity" in result.fallback_reason


def test_unsafe_activation_state_forces_baseline():
    result = evaluate_cross_border_scoring_fallback(
        _boundary(
            activation_state_safe=False,
        )
    )

    assert (
        result.target
        is CrossBorderScoringFallbackTarget.BASELINE
    )

    assert "activation_state" in result.fallback_reason


def test_multiple_failures_are_reported_deterministically():
    result = evaluate_cross_border_scoring_fallback(
        _boundary(
            state=CrossBorderActivationBoundaryState.FALLBACK,
            candidate_policy_id="baseline-v1",
            activation_authority_id=" ",
            activation_state_safe=False,
        )
    )

    assert result.fallback_reason == (
        "boundary,"
        "policy_identity,"
        "authority_identity,"
        "activation_state"
    )


def test_policy_ids_are_normalized():
    result = evaluate_cross_border_scoring_fallback(
        _boundary(
            baseline_policy_id="  baseline-v1  ",
            candidate_policy_id="  candidate-v1  ",
        )
    )

    assert result.baseline_policy_id == "baseline-v1"
    assert result.candidate_policy_id == "candidate-v1"


def test_target_vocabulary_is_bounded():
    assert {
        target.value
        for target in CrossBorderScoringFallbackTarget
    } == {
        "candidate",
        "baseline",
    }


def test_result_is_immutable():
    result = evaluate_cross_border_scoring_fallback(
        _boundary()
    )

    with pytest.raises(
        FrozenInstanceError,
    ):
        result.activation_allowed = False


def test_baseline_fallback_never_allows_activation():
    result = evaluate_cross_border_scoring_fallback(
        _boundary(
            state=CrossBorderActivationBoundaryState.FALLBACK,
        )
    )

    assert (
        result.target
        is CrossBorderScoringFallbackTarget.BASELINE
    )

    assert result.activation_allowed is False


def test_candidate_path_never_claims_runtime_activation():
    result = evaluate_cross_border_scoring_fallback(
        _boundary()
    )

    forbidden = {
        "production_enabled",
        "traffic_routed",
        "rollout_started",
        "activate_runtime",
        "enable_runtime",
        "deploy",
    }

    public_names = {
        name.lower()
        for name in dir(result)
        if not name.startswith("_")
    }

    assert forbidden.isdisjoint(public_names)


def test_result_has_no_score_surface():
    result = evaluate_cross_border_scoring_fallback(
        _boundary()
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
    result = evaluate_cross_border_scoring_fallback(
        _boundary()
    )

    forbidden = {
        "rank",
        "ranking",
        "winner",
        "selected_candidate",
        "best_candidate",
    }

    public_names = {
        name.lower()
        for name in dir(result)
        if not name.startswith("_")
    }

    assert forbidden.isdisjoint(public_names)


def test_result_has_no_recommendation_surface():
    result = evaluate_cross_border_scoring_fallback(
        _boundary()
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
    result = evaluate_cross_border_scoring_fallback(
        _boundary()
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


def test_evaluation_does_not_mutate_boundary():
    boundary = _boundary()

    original_state = boundary.state
    original_candidate = boundary.candidate_policy_id

    evaluate_cross_border_scoring_fallback(
        boundary
    )

    assert boundary.state is original_state
    assert boundary.candidate_policy_id == original_candidate
