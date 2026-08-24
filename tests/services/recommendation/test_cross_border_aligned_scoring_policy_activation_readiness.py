from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

import app.services.recommendation.cross_border_aligned_scoring_policy_activation_readiness as module
from app.services.recommendation.cross_border_aligned_scoring_policy_activation_readiness import (
    AlignedCrossBorderPolicyActivationReadiness,
    AlignedCrossBorderPolicyActivationReadinessState,
    evaluate_aligned_cross_border_policy_activation_readiness,
)
from app.services.recommendation.cross_border_aligned_scoring_policy_adoption_decision import (
    AlignedCrossBorderPolicyAdoptionDecision,
    AlignedCrossBorderPolicyAdoptionDecisionState,
)
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
    *,
    outcome=CrossBorderPolicyAdoptionDecisionOutcome.ADOPT,
) -> CrossBorderPolicyAdoptionDecision:
    return CrossBorderPolicyAdoptionDecision(
        outcome=outcome,
        baseline_policy_id="baseline-v1",
        candidate_policy_id="candidate-v1",
        authority_id="recommendation-governance",
        authority_role="policy_adoption_authority",
        readiness_confirmed=True,
        reason="decision recorded",
        production_activation_authorized=False,
    )


def _aligned(
    *,
    state=AlignedCrossBorderPolicyAdoptionDecisionState.RECORDED,
    decision=None,
) -> AlignedCrossBorderPolicyAdoptionDecision:
    if decision is None and (
        state
        is AlignedCrossBorderPolicyAdoptionDecisionState.RECORDED
    ):
        decision = _decision()

    return AlignedCrossBorderPolicyAdoptionDecision(
        state=state,
        aligned_readiness=None,  # type: ignore[arg-type]
        decision=decision,
        reasons=(
            ()
            if state
            is AlignedCrossBorderPolicyAdoptionDecisionState.RECORDED
            else ("blocked",)
        ),
    )


def test_recorded_adopt_decision_is_available_and_ready():
    result = evaluate_aligned_cross_border_policy_activation_readiness(
        _aligned()
    )

    assert (
        result.state
        is AlignedCrossBorderPolicyActivationReadinessState.AVAILABLE
    )
    assert isinstance(
        result.readiness,
        CrossBorderPolicyActivationReadiness,
    )
    assert (
        result.readiness.state
        is CrossBorderPolicyActivationReadinessState.READY
    )
    assert result.reasons == ()


@pytest.mark.parametrize(
    "outcome",
    [
        CrossBorderPolicyAdoptionDecisionOutcome.HOLD,
        CrossBorderPolicyAdoptionDecisionOutcome.REJECT,
    ],
)
def test_recorded_non_adopt_decision_is_available_but_not_ready(
    outcome,
):
    result = evaluate_aligned_cross_border_policy_activation_readiness(
        _aligned(
            decision=_decision(outcome=outcome),
        )
    )

    assert (
        result.state
        is AlignedCrossBorderPolicyActivationReadinessState.AVAILABLE
    )
    assert result.readiness is not None
    assert (
        result.readiness.state
        is CrossBorderPolicyActivationReadinessState.NOT_READY
    )
    assert "adoption_decision" in result.readiness.reasons
    assert result.reasons == ()


def test_blocked_aligned_decision_blocks_canonical_evaluation(
    monkeypatch,
):
    called = False

    def fail_if_called(decision):
        nonlocal called
        called = True
        raise AssertionError("canonical evaluator must not be called")

    monkeypatch.setattr(
        module,
        "evaluate_cross_border_policy_activation_readiness",
        fail_if_called,
    )

    result = evaluate_aligned_cross_border_policy_activation_readiness(
        _aligned(
            state=AlignedCrossBorderPolicyAdoptionDecisionState.BLOCKED,
            decision=None,
        )
    )

    assert called is False
    assert (
        result.state
        is AlignedCrossBorderPolicyActivationReadinessState.BLOCKED
    )
    assert result.readiness is None
    assert result.reasons == (
        "aligned_adoption_decision_not_recorded",
    )


def test_recorded_state_without_decision_is_invalid():
    aligned = AlignedCrossBorderPolicyAdoptionDecision(
        state=AlignedCrossBorderPolicyAdoptionDecisionState.RECORDED,
        aligned_readiness=None,  # type: ignore[arg-type]
        decision=None,
        reasons=(),
    )

    with pytest.raises(
        ValueError,
        match="must contain canonical decision",
    ):
        evaluate_aligned_cross_border_policy_activation_readiness(
            aligned
        )


def test_exact_canonical_decision_is_delegated(monkeypatch):
    decision = _decision()
    captured = None

    expected = evaluate_cross_border_policy_activation_readiness(
        decision
    )

    def capture(value):
        nonlocal captured
        captured = value
        return expected

    monkeypatch.setattr(
        module,
        "evaluate_cross_border_policy_activation_readiness",
        capture,
    )

    result = evaluate_aligned_cross_border_policy_activation_readiness(
        _aligned(decision=decision)
    )

    assert captured is decision
    assert result.readiness is expected


def test_result_is_canonical_aligned_type():
    result = evaluate_aligned_cross_border_policy_activation_readiness(
        _aligned()
    )

    assert isinstance(
        result,
        AlignedCrossBorderPolicyActivationReadiness,
    )


def test_state_vocabulary_is_bounded():
    assert {
        state.value
        for state in AlignedCrossBorderPolicyActivationReadinessState
    } == {
        "available",
        "blocked",
    }


def test_result_is_immutable():
    result = evaluate_aligned_cross_border_policy_activation_readiness(
        _aligned()
    )

    with pytest.raises(FrozenInstanceError):
        result.state = (
            AlignedCrossBorderPolicyActivationReadinessState.BLOCKED
        )


def test_available_is_not_alias_for_ready():
    result = evaluate_aligned_cross_border_policy_activation_readiness(
        _aligned(
            decision=_decision(
                outcome=CrossBorderPolicyAdoptionDecisionOutcome.HOLD
            )
        )
    )

    assert result.is_available is True
    assert result.readiness is not None
    assert (
        result.readiness.state
        is CrossBorderPolicyActivationReadinessState.NOT_READY
    )


def test_result_has_no_activation_authority_surface():
    result = evaluate_aligned_cross_border_policy_activation_readiness(
        _aligned()
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


def test_result_has_no_scoring_or_ranking_surface():
    result = evaluate_aligned_cross_border_policy_activation_readiness(
        _aligned()
    )

    forbidden = {
        "score",
        "final_score",
        "production_score",
        "apply_score",
        "rank",
        "ranking",
        "winner",
        "selected_candidate",
    }
    public_names = {
        name.lower()
        for name in dir(result)
        if not name.startswith("_")
    }

    assert forbidden.isdisjoint(public_names)


def test_result_has_no_recommendation_or_transaction_surface():
    result = evaluate_aligned_cross_border_policy_activation_readiness(
        _aligned()
    )

    forbidden = {
        "recommend",
        "recommended_candidate",
        "preferred_candidate",
        "purchase",
        "checkout",
        "transaction",
        "execute",
    }
    public_names = {
        name.lower()
        for name in dir(result)
        if not name.startswith("_")
    }

    assert forbidden.isdisjoint(public_names)
