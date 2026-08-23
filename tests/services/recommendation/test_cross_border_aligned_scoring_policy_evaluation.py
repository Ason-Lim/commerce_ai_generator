from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from decimal import Decimal
from unittest.mock import patch

import pytest

from app.services.cross_border.context import (
    CrossBorderEvaluationContext,
)
from app.services.cross_border.landed_cost_aggregation import (
    LandedCostAggregationQuality,
)
from app.services.cross_border.landed_cost_candidate_comparison import (
    LandedCostCandidateComparison,
    LandedCostCandidateComparisonState,
    LandedCostCandidateRelation,
)
from app.services.cross_border.landed_cost_comparison_binding import (
    bind_landed_cost_comparison_candidates,
)
from app.services.recommendation.cross_border_aligned_consumption_gate import (
    gate_aligned_cross_border_consumption,
)
from app.services.recommendation.cross_border_aligned_evaluation_readiness import (
    evaluate_aligned_cross_border_readiness,
)
from app.services.recommendation.cross_border_aligned_landed_cost_signal import (
    build_aligned_cross_border_landed_cost_signal,
)
from app.services.recommendation.cross_border_aligned_scoring_binding import (
    AlignedCrossBorderScoringBindingState,
    bind_aligned_cross_border_scoring_input,
)
from app.services.recommendation.cross_border_aligned_scoring_policy_evaluation import (
    AlignedCrossBorderScoringPolicyEvaluation,
    AlignedCrossBorderScoringPolicyEvaluationState,
    evaluate_aligned_cross_border_scoring_policy,
)
from app.services.recommendation.cross_border_aligned_scoring_readiness import (
    evaluate_aligned_cross_border_scoring_readiness,
)
from app.services.recommendation.cross_border_bound_evidence_alignment import (
    align_cross_border_bound_evidence,
)
from app.services.recommendation.cross_border_candidate_reference_binding import (
    bind_cross_border_candidate_reference,
)
from app.services.recommendation.cross_border_candidate_reference_binding_set import (
    validate_cross_border_candidate_reference_bindings,
)
from app.services.recommendation.cross_border_evidence import (
    CanonicalCrossBorderRecommendationEvidence,
)
from app.services.recommendation.cross_border_scoring_policy_evaluation import (
    CrossBorderScoringPolicy,
    CrossBorderScoringPolicyEvaluation,
    CrossBorderScoringPolicyKind,
    evaluate_cross_border_scoring_policy,
)


def _comparison():
    return LandedCostCandidateComparison(
        state=LandedCostCandidateComparisonState.COMPARED,
        relation=LandedCostCandidateRelation.FIRST_LESS,
        first_total=Decimal("100"),
        second_total=Decimal("120"),
        currency="USD",
        context=CrossBorderEvaluationContext(
            origin_country="KR",
            destination_country="US",
        ),
        first_quality=LandedCostAggregationQuality.KNOWN,
        second_quality=LandedCostAggregationQuality.KNOWN,
        reason="bounded comparison",
    )


def _alignment():
    first = bind_cross_border_candidate_reference(
        candidate_position=1,
        candidate_ref="candidate:first",
        binding_source="cross_border_handoff",
    )
    second = bind_cross_border_candidate_reference(
        candidate_position=2,
        candidate_ref="candidate:second",
        binding_source="cross_border_handoff",
    )

    binding_set = (
        validate_cross_border_candidate_reference_bindings(
            (second, first)
        )
    )

    bound = bind_landed_cost_comparison_candidates(
        first_candidate_ref="candidate:first",
        second_candidate_ref="candidate:second",
        comparison=_comparison(),
    )

    return align_cross_border_bound_evidence(
        binding_set=binding_set,
        bound_comparison=bound,
    )


def _evidence():
    return CanonicalCrossBorderRecommendationEvidence(
        first_candidate_ref="candidate:first",
        second_candidate_ref="candidate:second",
        landed_cost_relation="first_less",
        first_landed_cost=Decimal("100"),
        second_landed_cost=Decimal("120"),
        currency="USD",
        origin_country="KR",
        destination_country="US",
        first_evidence_quality="known",
        second_evidence_quality="known",
        source_schema_id="cross-border.recommendation-handoff",
        source_schema_version="1.0",
    )


def _policy(
    kind: CrossBorderScoringPolicyKind = (
        CrossBorderScoringPolicyKind.CANDIDATE
    ),
):
    return CrossBorderScoringPolicy(
        policy_id=(
            "candidate-policy"
            if kind is CrossBorderScoringPolicyKind.CANDIDATE
            else "baseline-policy"
        ),
        kind=kind,
        directional_delta=Decimal("3"),
    )


def _aligned_binding(
    evidence: CanonicalCrossBorderRecommendationEvidence | None = None,
):
    gate = gate_aligned_cross_border_consumption(
        evidence=evidence or _evidence(),
        alignment=_alignment(),
    )

    evaluation = evaluate_aligned_cross_border_readiness(
        gate
    )

    signal = build_aligned_cross_border_landed_cost_signal(
        evaluation
    )

    readiness = evaluate_aligned_cross_border_scoring_readiness(
        signal
    )

    return bind_aligned_cross_border_scoring_input(
        readiness
    )


def _blocked_binding():
    return _aligned_binding(
        evidence=replace(
            _evidence(),
            first_candidate_ref="candidate:other",
        )
    )


def test_available_binding_enters_existing_policy_authority():
    aligned_binding = _aligned_binding()
    policy = _policy()

    result = evaluate_aligned_cross_border_scoring_policy(
        aligned_binding=aligned_binding,
        policy=policy,
    )

    assert isinstance(
        result,
        AlignedCrossBorderScoringPolicyEvaluation,
    )
    assert (
        result.state
        is AlignedCrossBorderScoringPolicyEvaluationState.AVAILABLE
    )
    assert result.is_available is True
    assert result.aligned_binding is aligned_binding
    assert isinstance(
        result.evaluation,
        CrossBorderScoringPolicyEvaluation,
    )
    assert result.reasons == ()


def test_available_result_matches_existing_policy_authority():
    aligned_binding = _aligned_binding()
    policy = _policy()

    expected = evaluate_cross_border_scoring_policy(
        scoring_input=aligned_binding.scoring_input,
        policy=policy,
    )

    result = evaluate_aligned_cross_border_scoring_policy(
        aligned_binding=aligned_binding,
        policy=policy,
    )

    assert result.evaluation == expected


def test_blocked_binding_blocks_policy_evaluation():
    aligned_binding = _blocked_binding()

    assert (
        aligned_binding.state
        is AlignedCrossBorderScoringBindingState.BLOCKED
    )

    result = evaluate_aligned_cross_border_scoring_policy(
        aligned_binding=aligned_binding,
        policy=_policy(),
    )

    assert (
        result.state
        is AlignedCrossBorderScoringPolicyEvaluationState.BLOCKED
    )
    assert result.is_available is False
    assert result.evaluation is None
    assert result.reasons == (
        "cross_border_scoring_binding_not_available",
    )


def test_blocked_binding_does_not_invoke_policy_authority():
    aligned_binding = _blocked_binding()

    target = (
        "app.services.recommendation."
        "cross_border_aligned_scoring_policy_evaluation."
        "evaluate_cross_border_scoring_policy"
    )

    with patch(target) as evaluator:
        result = evaluate_aligned_cross_border_scoring_policy(
            aligned_binding=aligned_binding,
            policy=_policy(),
        )

    evaluator.assert_not_called()
    assert result.evaluation is None


def test_exact_c4p_scoring_input_and_policy_are_delegated():
    aligned_binding = _aligned_binding()
    policy = _policy()

    canonical_evaluation = evaluate_cross_border_scoring_policy(
        scoring_input=aligned_binding.scoring_input,
        policy=policy,
    )

    target = (
        "app.services.recommendation."
        "cross_border_aligned_scoring_policy_evaluation."
        "evaluate_cross_border_scoring_policy"
    )

    with patch(
        target,
        return_value=canonical_evaluation,
    ) as evaluator:
        result = evaluate_aligned_cross_border_scoring_policy(
            aligned_binding=aligned_binding,
            policy=policy,
        )

    evaluator.assert_called_once_with(
        scoring_input=aligned_binding.scoring_input,
        policy=policy,
    )
    assert result.evaluation is canonical_evaluation


def test_baseline_policy_remains_existing_policy_semantics():
    aligned_binding = _aligned_binding()
    policy = _policy(
        CrossBorderScoringPolicyKind.BASELINE
    )

    result = evaluate_aligned_cross_border_scoring_policy(
        aligned_binding=aligned_binding,
        policy=policy,
    )

    assert result.evaluation is not None
    assert (
        result.evaluation.policy_kind
        is CrossBorderScoringPolicyKind.BASELINE
    )
    assert result.evaluation.first_delta == Decimal("0")
    assert result.evaluation.second_delta == Decimal("0")
    assert result.evaluation.shadow_only is True


def test_candidate_policy_remains_shadow_only():
    result = evaluate_aligned_cross_border_scoring_policy(
        aligned_binding=_aligned_binding(),
        policy=_policy(),
    )

    assert result.evaluation is not None
    assert result.evaluation.shadow_only is True


def test_result_is_immutable():
    result = evaluate_aligned_cross_border_scoring_policy(
        aligned_binding=_aligned_binding(),
        policy=_policy(),
    )

    with pytest.raises(FrozenInstanceError):
        result.reasons = ("changed",)


def test_adapter_exposes_no_comparison_adoption_or_activation_authority():
    result = evaluate_aligned_cross_border_scoring_policy(
        aligned_binding=_aligned_binding(),
        policy=_policy(),
    )

    forbidden = {
        "comparison",
        "adoption",
        "adoption_decision",
        "activation",
        "activation_decision",
        "fallback",
        "controlled_score",
        "rank",
        "winner",
        "recommendation",
    }

    assert forbidden.isdisjoint(
        vars(result)
    )


def test_adapter_does_not_mutate_aligned_binding():
    aligned_binding = _aligned_binding()

    original_input = aligned_binding.scoring_input
    original_readiness = aligned_binding.aligned_readiness

    evaluate_aligned_cross_border_scoring_policy(
        aligned_binding=aligned_binding,
        policy=_policy(),
    )

    assert aligned_binding.scoring_input is original_input
    assert (
        aligned_binding.aligned_readiness
        is original_readiness
    )
