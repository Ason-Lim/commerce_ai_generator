from __future__ import annotations

from dataclasses import FrozenInstanceError
from decimal import Decimal

import pytest

from app.services.recommendation.cross_border_scoring_binding import (
    BoundCrossBorderScoringInput,
    CrossBorderScoringDirection,
)
from app.services.recommendation.cross_border_scoring_policy_evaluation import (
    CrossBorderScoringPolicy,
    CrossBorderScoringPolicyEvaluation,
    CrossBorderScoringPolicyKind,
    evaluate_cross_border_scoring_policy,
)


def _input(
    *,
    direction=CrossBorderScoringDirection.FIRST,
) -> BoundCrossBorderScoringInput:
    return BoundCrossBorderScoringInput(
        first_candidate_ref="candidate:first",
        second_candidate_ref="candidate:second",
        first_landed_cost=Decimal("100"),
        second_landed_cost=Decimal("120"),
        currency="USD",
        direction=direction,
        first_evidence_quality="known",
        second_evidence_quality="estimated",
        source_schema_id=(
            "commerce_ai.cross_border."
            "recommendation_handoff"
        ),
        source_schema_version="1.0",
    )


def _candidate_policy(
    delta="1.5",
) -> CrossBorderScoringPolicy:
    return CrossBorderScoringPolicy(
        policy_id="candidate-policy-v1",
        kind=CrossBorderScoringPolicyKind.CANDIDATE,
        directional_delta=Decimal(delta),
    )


def test_baseline_policy_produces_zero_deltas():
    result = evaluate_cross_border_scoring_policy(
        scoring_input=_input(),
        policy=CrossBorderScoringPolicy(
            policy_id="baseline",
            kind=CrossBorderScoringPolicyKind.BASELINE,
            directional_delta=Decimal("99"),
        ),
    )

    assert result.first_delta == Decimal("0")
    assert result.second_delta == Decimal("0")


def test_first_direction_candidate_policy_affects_first_shadow_delta():
    result = evaluate_cross_border_scoring_policy(
        scoring_input=_input(
            direction=CrossBorderScoringDirection.FIRST
        ),
        policy=_candidate_policy("1.5"),
    )

    assert result.first_delta == Decimal("1.5")
    assert result.second_delta == Decimal("0")


def test_second_direction_candidate_policy_affects_second_shadow_delta():
    result = evaluate_cross_border_scoring_policy(
        scoring_input=_input(
            direction=CrossBorderScoringDirection.SECOND
        ),
        policy=_candidate_policy("2.0"),
    )

    assert result.first_delta == Decimal("0")
    assert result.second_delta == Decimal("2.0")


def test_equal_direction_produces_zero_shadow_deltas():
    result = evaluate_cross_border_scoring_policy(
        scoring_input=_input(
            direction=CrossBorderScoringDirection.EQUAL
        ),
        policy=_candidate_policy("4.0"),
    )

    assert result.first_delta == Decimal("0")
    assert result.second_delta == Decimal("0")


def test_result_is_shadow_only():
    result = evaluate_cross_border_scoring_policy(
        scoring_input=_input(),
        policy=_candidate_policy(),
    )

    assert result.shadow_only is True


def test_result_preserves_policy_identity():
    result = evaluate_cross_border_scoring_policy(
        scoring_input=_input(),
        policy=_candidate_policy(),
    )

    assert result.policy_id == "candidate-policy-v1"
    assert (
        result.policy_kind
        is CrossBorderScoringPolicyKind.CANDIDATE
    )


def test_result_preserves_candidate_refs():
    result = evaluate_cross_border_scoring_policy(
        scoring_input=_input(),
        policy=_candidate_policy(),
    )

    assert result.first_candidate_ref == "candidate:first"
    assert result.second_candidate_ref == "candidate:second"


def test_policy_id_is_normalized():
    policy = CrossBorderScoringPolicy(
        policy_id="  policy-v1  ",
        kind=CrossBorderScoringPolicyKind.CANDIDATE,
        directional_delta=Decimal("1"),
    )

    assert policy.policy_id == "policy-v1"


def test_blank_policy_id_is_rejected():
    with pytest.raises(
        ValueError,
        match="policy_id",
    ):
        CrossBorderScoringPolicy(
            policy_id=" ",
            kind=CrossBorderScoringPolicyKind.CANDIDATE,
            directional_delta=Decimal("1"),
        )


def test_negative_directional_delta_is_rejected():
    with pytest.raises(
        ValueError,
        match="non-negative",
    ):
        CrossBorderScoringPolicy(
            policy_id="candidate",
            kind=CrossBorderScoringPolicyKind.CANDIDATE,
            directional_delta=Decimal("-1"),
        )


def test_policy_is_immutable():
    policy = _candidate_policy()

    with pytest.raises(
        FrozenInstanceError,
    ):
        policy.policy_id = "changed"


def test_evaluation_result_is_immutable():
    result = evaluate_cross_border_scoring_policy(
        scoring_input=_input(),
        policy=_candidate_policy(),
    )

    with pytest.raises(
        FrozenInstanceError,
    ):
        result.first_delta = Decimal("9")


def test_policy_kind_vocabulary_is_bounded():
    assert {
        item.value
        for item in CrossBorderScoringPolicyKind
    } == {
        "baseline",
        "candidate",
    }


def test_evaluation_has_no_production_score_surface():
    result = evaluate_cross_border_scoring_policy(
        scoring_input=_input(),
        policy=_candidate_policy(),
    )

    forbidden = {
        "score",
        "final_score",
        "price_score",
        "ranking_score",
        "production_score",
    }

    public_names = {
        name.lower()
        for name in dir(result)
        if not name.startswith("_")
    }

    assert forbidden.isdisjoint(public_names)


def test_evaluation_has_no_ranking_surface():
    result = evaluate_cross_border_scoring_policy(
        scoring_input=_input(),
        policy=_candidate_policy(),
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


def test_evaluation_has_no_recommendation_surface():
    result = evaluate_cross_border_scoring_policy(
        scoring_input=_input(),
        policy=_candidate_policy(),
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


def test_evaluation_does_not_mutate_input():
    scoring_input = _input()

    original_first = scoring_input.first_landed_cost
    original_direction = scoring_input.direction

    evaluate_cross_border_scoring_policy(
        scoring_input=scoring_input,
        policy=_candidate_policy(),
    )

    assert scoring_input.first_landed_cost == original_first
    assert scoring_input.direction is original_direction


def test_evaluation_does_not_mutate_policy():
    policy = _candidate_policy("1.5")

    original_delta = policy.directional_delta

    evaluate_cross_border_scoring_policy(
        scoring_input=_input(),
        policy=policy,
    )

    assert policy.directional_delta == original_delta
