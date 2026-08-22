from __future__ import annotations

from dataclasses import FrozenInstanceError
from decimal import Decimal

import pytest

from app.services.recommendation.cross_border_scoring_binding import (
    CrossBorderScoringDirection,
)
from app.services.recommendation.cross_border_scoring_policy_comparison import (
    CrossBorderPolicyComparisonState,
    CrossBorderScoringPolicyComparison,
    compare_cross_border_scoring_policies,
)
from app.services.recommendation.cross_border_scoring_policy_evaluation import (
    CrossBorderScoringPolicyEvaluation,
    CrossBorderScoringPolicyKind,
)


def _baseline(
    **overrides,
) -> CrossBorderScoringPolicyEvaluation:
    values = {
        "policy_id": "baseline-v1",
        "policy_kind": CrossBorderScoringPolicyKind.BASELINE,
        "first_candidate_ref": "candidate:first",
        "second_candidate_ref": "candidate:second",
        "first_delta": Decimal("0"),
        "second_delta": Decimal("0"),
        "direction": CrossBorderScoringDirection.FIRST,
        "shadow_only": True,
    }

    values.update(overrides)

    return CrossBorderScoringPolicyEvaluation(
        **values
    )


def _candidate(
    **overrides,
) -> CrossBorderScoringPolicyEvaluation:
    values = {
        "policy_id": "candidate-v1",
        "policy_kind": CrossBorderScoringPolicyKind.CANDIDATE,
        "first_candidate_ref": "candidate:first",
        "second_candidate_ref": "candidate:second",
        "first_delta": Decimal("1.5"),
        "second_delta": Decimal("0"),
        "direction": CrossBorderScoringDirection.FIRST,
        "shadow_only": True,
    }

    values.update(overrides)

    return CrossBorderScoringPolicyEvaluation(
        **values
    )


def test_aligned_evaluations_are_comparable():
    result = compare_cross_border_scoring_policies(
        baseline=_baseline(),
        candidate=_candidate(),
    )

    assert (
        result.state
        is CrossBorderPolicyComparisonState.COMPARABLE
    )

    assert result.reasons == ()


def test_result_is_canonical_comparison_type():
    result = compare_cross_border_scoring_policies(
        baseline=_baseline(),
        candidate=_candidate(),
    )

    assert isinstance(
        result,
        CrossBorderScoringPolicyComparison,
    )


def test_first_delta_difference_is_candidate_minus_baseline():
    result = compare_cross_border_scoring_policies(
        baseline=_baseline(
            first_delta=Decimal("0"),
        ),
        candidate=_candidate(
            first_delta=Decimal("1.5"),
        ),
    )

    assert (
        result.first_delta_difference
        == Decimal("1.5")
    )


def test_second_delta_difference_is_candidate_minus_baseline():
    result = compare_cross_border_scoring_policies(
        baseline=_baseline(
            second_delta=Decimal("0.5"),
        ),
        candidate=_candidate(
            second_delta=Decimal("2.0"),
        ),
    )

    assert (
        result.second_delta_difference
        == Decimal("1.5")
    )


def test_zero_difference_is_valid_comparison():
    result = compare_cross_border_scoring_policies(
        baseline=_baseline(
            first_delta=Decimal("0"),
            second_delta=Decimal("0"),
        ),
        candidate=_candidate(
            first_delta=Decimal("0"),
            second_delta=Decimal("0"),
        ),
    )

    assert (
        result.state
        is CrossBorderPolicyComparisonState.COMPARABLE
    )

    assert (
        result.first_delta_difference
        == Decimal("0")
    )

    assert (
        result.second_delta_difference
        == Decimal("0")
    )


def test_negative_difference_is_observable_not_rejected():
    result = compare_cross_border_scoring_policies(
        baseline=_baseline(
            first_delta=Decimal("2"),
        ),
        candidate=_candidate(
            first_delta=Decimal("1"),
        ),
    )

    assert (
        result.first_delta_difference
        == Decimal("-1")
    )


def test_candidate_identity_mismatch_is_not_comparable():
    result = compare_cross_border_scoring_policies(
        baseline=_baseline(),
        candidate=_candidate(
            second_candidate_ref="candidate:third",
        ),
    )

    assert (
        result.state
        is CrossBorderPolicyComparisonState.NOT_COMPARABLE
    )

    assert "candidate_identity" in result.reasons

    assert result.first_delta_difference is None
    assert result.second_delta_difference is None


def test_direction_mismatch_is_not_comparable():
    result = compare_cross_border_scoring_policies(
        baseline=_baseline(
            direction=CrossBorderScoringDirection.FIRST,
        ),
        candidate=_candidate(
            direction=CrossBorderScoringDirection.SECOND,
        ),
    )

    assert (
        result.state
        is CrossBorderPolicyComparisonState.NOT_COMPARABLE
    )

    assert "direction" in result.reasons


def test_non_shadow_baseline_is_not_comparable():
    result = compare_cross_border_scoring_policies(
        baseline=_baseline(
            shadow_only=False,
        ),
        candidate=_candidate(),
    )

    assert (
        result.state
        is CrossBorderPolicyComparisonState.NOT_COMPARABLE
    )

    assert "shadow_mode" in result.reasons


def test_non_shadow_candidate_is_not_comparable():
    result = compare_cross_border_scoring_policies(
        baseline=_baseline(),
        candidate=_candidate(
            shadow_only=False,
        ),
    )

    assert (
        result.state
        is CrossBorderPolicyComparisonState.NOT_COMPARABLE
    )

    assert "shadow_mode" in result.reasons


def test_candidate_used_as_baseline_is_not_comparable():
    result = compare_cross_border_scoring_policies(
        baseline=_baseline(
            policy_kind=CrossBorderScoringPolicyKind.CANDIDATE,
        ),
        candidate=_candidate(),
    )

    assert (
        result.state
        is CrossBorderPolicyComparisonState.NOT_COMPARABLE
    )

    assert "policy_roles" in result.reasons


def test_baseline_used_as_candidate_is_not_comparable():
    result = compare_cross_border_scoring_policies(
        baseline=_baseline(),
        candidate=_candidate(
            policy_kind=CrossBorderScoringPolicyKind.BASELINE,
        ),
    )

    assert (
        result.state
        is CrossBorderPolicyComparisonState.NOT_COMPARABLE
    )

    assert "policy_roles" in result.reasons


def test_multiple_alignment_failures_are_reported():
    result = compare_cross_border_scoring_policies(
        baseline=_baseline(
            shadow_only=False,
        ),
        candidate=_candidate(
            second_candidate_ref="candidate:third",
            direction=CrossBorderScoringDirection.SECOND,
            policy_kind=CrossBorderScoringPolicyKind.BASELINE,
        ),
    )

    assert set(result.reasons) == {
        "candidate_identity",
        "direction",
        "shadow_mode",
        "policy_roles",
    }


def test_policy_identity_is_preserved():
    result = compare_cross_border_scoring_policies(
        baseline=_baseline(),
        candidate=_candidate(),
    )

    assert result.baseline_policy_id == "baseline-v1"
    assert result.candidate_policy_id == "candidate-v1"


def test_candidate_refs_are_preserved():
    result = compare_cross_border_scoring_policies(
        baseline=_baseline(),
        candidate=_candidate(),
    )

    assert (
        result.first_candidate_ref
        == "candidate:first"
    )

    assert (
        result.second_candidate_ref
        == "candidate:second"
    )


def test_alignment_dimensions_are_true_when_comparable():
    result = compare_cross_border_scoring_policies(
        baseline=_baseline(),
        candidate=_candidate(),
    )

    assert result.candidate_identity_aligned is True
    assert result.direction_aligned is True
    assert result.shadow_mode_aligned is True
    assert result.policy_roles_valid is True


def test_comparison_result_is_immutable():
    result = compare_cross_border_scoring_policies(
        baseline=_baseline(),
        candidate=_candidate(),
    )

    with pytest.raises(
        FrozenInstanceError,
    ):
        result.state = (
            CrossBorderPolicyComparisonState.NOT_COMPARABLE
        )


def test_comparison_state_vocabulary_is_bounded():
    assert {
        state.value
        for state in CrossBorderPolicyComparisonState
    } == {
        "comparable",
        "not_comparable",
    }


def test_result_has_no_policy_selection_surface():
    result = compare_cross_border_scoring_policies(
        baseline=_baseline(),
        candidate=_candidate(),
    )

    forbidden = {
        "winner",
        "winning_policy",
        "selected_policy",
        "preferred_policy",
        "best_policy",
        "adopted_policy",
    }

    public_names = {
        name.lower()
        for name in dir(result)
        if not name.startswith("_")
    }

    assert forbidden.isdisjoint(
        public_names
    )


def test_result_has_no_production_scoring_surface():
    result = compare_cross_border_scoring_policies(
        baseline=_baseline(),
        candidate=_candidate(),
    )

    forbidden = {
        "score",
        "final_score",
        "production_score",
        "price_score",
        "apply_score",
    }

    public_names = {
        name.lower()
        for name in dir(result)
        if not name.startswith("_")
    }

    assert forbidden.isdisjoint(
        public_names
    )


def test_result_has_no_ranking_surface():
    result = compare_cross_border_scoring_policies(
        baseline=_baseline(),
        candidate=_candidate(),
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

    assert forbidden.isdisjoint(
        public_names
    )


def test_result_has_no_recommendation_surface():
    result = compare_cross_border_scoring_policies(
        baseline=_baseline(),
        candidate=_candidate(),
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

    assert forbidden.isdisjoint(
        public_names
    )


def test_result_has_no_adoption_surface():
    result = compare_cross_border_scoring_policies(
        baseline=_baseline(),
        candidate=_candidate(),
    )

    forbidden = {
        "adopt",
        "adoption",
        "approved",
        "accepted",
        "deploy",
        "activate",
    }

    public_names = {
        name.lower()
        for name in dir(result)
        if not name.startswith("_")
    }

    assert forbidden.isdisjoint(
        public_names
    )


def test_comparison_does_not_mutate_baseline():
    baseline = _baseline()

    original_delta = baseline.first_delta

    compare_cross_border_scoring_policies(
        baseline=baseline,
        candidate=_candidate(),
    )

    assert baseline.first_delta == original_delta


def test_comparison_does_not_mutate_candidate():
    candidate = _candidate()

    original_delta = candidate.first_delta

    compare_cross_border_scoring_policies(
        baseline=_baseline(),
        candidate=candidate,
    )

    assert candidate.first_delta == original_delta
