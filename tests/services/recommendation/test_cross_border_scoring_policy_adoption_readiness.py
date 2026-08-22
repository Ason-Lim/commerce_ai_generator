from __future__ import annotations

from dataclasses import FrozenInstanceError
from decimal import Decimal

import pytest

from app.services.recommendation.cross_border_scoring_policy_adoption_readiness import (
    CrossBorderPolicyAdoptionReadiness,
    CrossBorderPolicyAdoptionReadinessState,
    evaluate_cross_border_policy_adoption_readiness,
)
from app.services.recommendation.cross_border_scoring_policy_comparison import (
    CrossBorderPolicyComparisonState,
    CrossBorderScoringPolicyComparison,
)


def _comparison(
    **overrides,
) -> CrossBorderScoringPolicyComparison:
    values = {
        "state": CrossBorderPolicyComparisonState.COMPARABLE,
        "baseline_policy_id": "baseline-v1",
        "candidate_policy_id": "candidate-v1",
        "first_candidate_ref": "candidate:first",
        "second_candidate_ref": "candidate:second",
        "first_delta_difference": Decimal("1.5"),
        "second_delta_difference": Decimal("0"),
        "candidate_identity_aligned": True,
        "direction_aligned": True,
        "shadow_mode_aligned": True,
        "policy_roles_valid": True,
        "reasons": (),
    }

    values.update(overrides)

    return CrossBorderScoringPolicyComparison(
        **values
    )


def test_valid_comparison_is_adoption_ready():
    result = (
        evaluate_cross_border_policy_adoption_readiness(
            _comparison()
        )
    )

    assert (
        result.state
        is CrossBorderPolicyAdoptionReadinessState.READY
    )

    assert result.reasons == ()


def test_result_is_canonical_readiness_type():
    result = (
        evaluate_cross_border_policy_adoption_readiness(
            _comparison()
        )
    )

    assert isinstance(
        result,
        CrossBorderPolicyAdoptionReadiness,
    )


def test_all_readiness_dimensions_are_true():
    result = (
        evaluate_cross_border_policy_adoption_readiness(
            _comparison()
        )
    )

    assert result.comparison_ready is True
    assert result.policy_identity_ready is True
    assert result.delta_evidence_ready is True
    assert result.candidate_identity_ready is True
    assert result.direction_ready is True
    assert result.shadow_evidence_ready is True
    assert result.policy_roles_ready is True


def test_not_comparable_is_not_ready():
    result = (
        evaluate_cross_border_policy_adoption_readiness(
            _comparison(
                state=(
                    CrossBorderPolicyComparisonState.NOT_COMPARABLE
                ),
                first_delta_difference=None,
                second_delta_difference=None,
            )
        )
    )

    assert (
        result.state
        is CrossBorderPolicyAdoptionReadinessState.NOT_READY
    )

    assert "comparison" in result.reasons
    assert "delta_evidence" in result.reasons


def test_same_policy_identity_is_not_ready():
    result = (
        evaluate_cross_border_policy_adoption_readiness(
            _comparison(
                candidate_policy_id="baseline-v1",
            )
        )
    )

    assert (
        result.state
        is CrossBorderPolicyAdoptionReadinessState.NOT_READY
    )

    assert "policy_identity" in result.reasons


def test_blank_baseline_policy_id_is_not_ready():
    result = (
        evaluate_cross_border_policy_adoption_readiness(
            _comparison(
                baseline_policy_id=" ",
            )
        )
    )

    assert (
        result.state
        is CrossBorderPolicyAdoptionReadinessState.NOT_READY
    )

    assert "policy_identity" in result.reasons


def test_blank_candidate_policy_id_is_not_ready():
    result = (
        evaluate_cross_border_policy_adoption_readiness(
            _comparison(
                candidate_policy_id=" ",
            )
        )
    )

    assert (
        result.state
        is CrossBorderPolicyAdoptionReadinessState.NOT_READY
    )

    assert "policy_identity" in result.reasons


def test_policy_ids_are_normalized():
    result = (
        evaluate_cross_border_policy_adoption_readiness(
            _comparison(
                baseline_policy_id="  baseline-v1  ",
                candidate_policy_id="  candidate-v1  ",
            )
        )
    )

    assert result.baseline_policy_id == "baseline-v1"
    assert result.candidate_policy_id == "candidate-v1"


def test_missing_first_delta_is_not_ready():
    result = (
        evaluate_cross_border_policy_adoption_readiness(
            _comparison(
                first_delta_difference=None,
            )
        )
    )

    assert (
        result.state
        is CrossBorderPolicyAdoptionReadinessState.NOT_READY
    )

    assert "delta_evidence" in result.reasons


def test_missing_second_delta_is_not_ready():
    result = (
        evaluate_cross_border_policy_adoption_readiness(
            _comparison(
                second_delta_difference=None,
            )
        )
    )

    assert (
        result.state
        is CrossBorderPolicyAdoptionReadinessState.NOT_READY
    )

    assert "delta_evidence" in result.reasons


@pytest.mark.parametrize(
    "delta",
    [
        Decimal("NaN"),
        Decimal("Infinity"),
        Decimal("-Infinity"),
    ],
)
def test_non_finite_first_delta_is_not_ready(
    delta: Decimal,
):
    result = (
        evaluate_cross_border_policy_adoption_readiness(
            _comparison(
                first_delta_difference=delta,
            )
        )
    )

    assert (
        result.state
        is CrossBorderPolicyAdoptionReadinessState.NOT_READY
    )

    assert "delta_evidence" in result.reasons


@pytest.mark.parametrize(
    "delta",
    [
        Decimal("NaN"),
        Decimal("Infinity"),
        Decimal("-Infinity"),
    ],
)
def test_non_finite_second_delta_is_not_ready(
    delta: Decimal,
):
    result = (
        evaluate_cross_border_policy_adoption_readiness(
            _comparison(
                second_delta_difference=delta,
            )
        )
    )

    assert (
        result.state
        is CrossBorderPolicyAdoptionReadinessState.NOT_READY
    )

    assert "delta_evidence" in result.reasons


def test_zero_deltas_can_still_be_ready():
    result = (
        evaluate_cross_border_policy_adoption_readiness(
            _comparison(
                first_delta_difference=Decimal("0"),
                second_delta_difference=Decimal("0"),
            )
        )
    )

    assert (
        result.state
        is CrossBorderPolicyAdoptionReadinessState.READY
    )


def test_negative_delta_can_still_be_ready():
    result = (
        evaluate_cross_border_policy_adoption_readiness(
            _comparison(
                first_delta_difference=Decimal("-1"),
            )
        )
    )

    assert (
        result.state
        is CrossBorderPolicyAdoptionReadinessState.READY
    )


def test_positive_delta_does_not_create_adoption_authority():
    result = (
        evaluate_cross_border_policy_adoption_readiness(
            _comparison(
                first_delta_difference=Decimal("100"),
            )
        )
    )

    assert (
        result.state
        is CrossBorderPolicyAdoptionReadinessState.READY
    )

    forbidden = {
        "adopted",
        "approved",
        "selected_policy",
        "winning_policy",
        "preferred_policy",
        "best_policy",
    }

    public_names = {
        name.lower()
        for name in dir(result)
        if not name.startswith("_")
    }

    assert forbidden.isdisjoint(public_names)


def test_candidate_identity_misalignment_is_not_ready():
    result = (
        evaluate_cross_border_policy_adoption_readiness(
            _comparison(
                candidate_identity_aligned=False,
            )
        )
    )

    assert (
        result.state
        is CrossBorderPolicyAdoptionReadinessState.NOT_READY
    )

    assert "candidate_identity" in result.reasons


def test_same_candidate_refs_are_not_ready():
    result = (
        evaluate_cross_border_policy_adoption_readiness(
            _comparison(
                second_candidate_ref="candidate:first",
            )
        )
    )

    assert (
        result.state
        is CrossBorderPolicyAdoptionReadinessState.NOT_READY
    )

    assert "candidate_identity" in result.reasons


def test_direction_misalignment_is_not_ready():
    result = (
        evaluate_cross_border_policy_adoption_readiness(
            _comparison(
                direction_aligned=False,
            )
        )
    )

    assert (
        result.state
        is CrossBorderPolicyAdoptionReadinessState.NOT_READY
    )

    assert "direction" in result.reasons


def test_non_shadow_evidence_is_not_ready():
    result = (
        evaluate_cross_border_policy_adoption_readiness(
            _comparison(
                shadow_mode_aligned=False,
            )
        )
    )

    assert (
        result.state
        is CrossBorderPolicyAdoptionReadinessState.NOT_READY
    )

    assert "shadow_evidence" in result.reasons


def test_invalid_policy_roles_are_not_ready():
    result = (
        evaluate_cross_border_policy_adoption_readiness(
            _comparison(
                policy_roles_valid=False,
            )
        )
    )

    assert (
        result.state
        is CrossBorderPolicyAdoptionReadinessState.NOT_READY
    )

    assert "policy_roles" in result.reasons


def test_multiple_failures_are_reported():
    result = (
        evaluate_cross_border_policy_adoption_readiness(
            _comparison(
                state=(
                    CrossBorderPolicyComparisonState.NOT_COMPARABLE
                ),
                candidate_policy_id="baseline-v1",
                first_delta_difference=None,
                second_candidate_ref="candidate:first",
                candidate_identity_aligned=False,
                direction_aligned=False,
                shadow_mode_aligned=False,
                policy_roles_valid=False,
            )
        )
    )

    assert set(result.reasons) == {
        "comparison",
        "policy_identity",
        "delta_evidence",
        "candidate_identity",
        "direction",
        "shadow_evidence",
        "policy_roles",
    }


def test_result_is_immutable():
    result = (
        evaluate_cross_border_policy_adoption_readiness(
            _comparison()
        )
    )

    with pytest.raises(
        FrozenInstanceError,
    ):
        result.comparison_ready = False


def test_readiness_vocabulary_is_bounded():
    assert {
        state.value
        for state in CrossBorderPolicyAdoptionReadinessState
    } == {
        "ready",
        "not_ready",
    }


def test_result_has_no_policy_adoption_surface():
    result = (
        evaluate_cross_border_policy_adoption_readiness(
            _comparison()
        )
    )

    forbidden = {
        "adopt",
        "adopt_policy",
        "adopted_policy",
        "activate_policy",
        "deploy_policy",
        "approved_policy",
    }

    public_names = {
        name.lower()
        for name in dir(result)
        if not name.startswith("_")
    }

    assert forbidden.isdisjoint(public_names)


def test_result_has_no_policy_selection_surface():
    result = (
        evaluate_cross_border_policy_adoption_readiness(
            _comparison()
        )
    )

    forbidden = {
        "winner",
        "winning_policy",
        "selected_policy",
        "preferred_policy",
        "best_policy",
    }

    public_names = {
        name.lower()
        for name in dir(result)
        if not name.startswith("_")
    }

    assert forbidden.isdisjoint(public_names)


def test_result_has_no_production_scoring_surface():
    result = (
        evaluate_cross_border_policy_adoption_readiness(
            _comparison()
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
        evaluate_cross_border_policy_adoption_readiness(
            _comparison()
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
        evaluate_cross_border_policy_adoption_readiness(
            _comparison()
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


def test_readiness_does_not_mutate_comparison():
    comparison = _comparison()

    original_state = comparison.state
    original_first_delta = (
        comparison.first_delta_difference
    )

    evaluate_cross_border_policy_adoption_readiness(
        comparison
    )

    assert comparison.state is original_state
    assert (
        comparison.first_delta_difference
        == original_first_delta
    )
