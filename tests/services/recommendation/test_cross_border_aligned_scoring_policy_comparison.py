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
    bind_aligned_cross_border_scoring_input,
)
from app.services.recommendation.cross_border_aligned_scoring_policy_comparison import (
    AlignedCrossBorderScoringPolicyComparison,
    AlignedCrossBorderScoringPolicyComparisonState,
    compare_aligned_cross_border_scoring_policies,
)
from app.services.recommendation.cross_border_aligned_scoring_policy_evaluation import (
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
from app.services.recommendation.cross_border_scoring_policy_comparison import (
    CrossBorderPolicyComparisonState,
    CrossBorderScoringPolicyComparison,
    compare_cross_border_scoring_policies,
)
from app.services.recommendation.cross_border_scoring_policy_evaluation import (
    CrossBorderScoringPolicy,
    CrossBorderScoringPolicyKind,
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
    kind: CrossBorderScoringPolicyKind,
):
    return CrossBorderScoringPolicy(
        policy_id=(
            "baseline-policy"
            if kind is CrossBorderScoringPolicyKind.BASELINE
            else "candidate-policy"
        ),
        kind=kind,
        directional_delta=(
            Decimal("0")
            if kind is CrossBorderScoringPolicyKind.BASELINE
            else Decimal("3")
        ),
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


def _aligned_policy(
    kind: CrossBorderScoringPolicyKind,
    *,
    evidence: CanonicalCrossBorderRecommendationEvidence | None = None,
):
    return evaluate_aligned_cross_border_scoring_policy(
        aligned_binding=_aligned_binding(evidence),
        policy=_policy(kind),
    )


def _available_pair():
    baseline = _aligned_policy(
        CrossBorderScoringPolicyKind.BASELINE
    )
    candidate = _aligned_policy(
        CrossBorderScoringPolicyKind.CANDIDATE
    )
    return baseline, candidate


def _blocked_policy(
    kind: CrossBorderScoringPolicyKind,
):
    return _aligned_policy(
        kind,
        evidence=replace(
            _evidence(),
            first_candidate_ref="candidate:other",
        ),
    )


def test_available_pair_enters_existing_comparison_authority():
    baseline, candidate = _available_pair()

    result = compare_aligned_cross_border_scoring_policies(
        baseline=baseline,
        candidate=candidate,
    )

    assert isinstance(
        result,
        AlignedCrossBorderScoringPolicyComparison,
    )
    assert (
        result.state
        is AlignedCrossBorderScoringPolicyComparisonState.AVAILABLE
    )
    assert result.is_available is True
    assert result.baseline is baseline
    assert result.candidate is candidate
    assert isinstance(
        result.comparison,
        CrossBorderScoringPolicyComparison,
    )
    assert result.reasons == ()


def test_available_result_matches_existing_comparison_authority():
    baseline, candidate = _available_pair()

    expected = compare_cross_border_scoring_policies(
        baseline=baseline.evaluation,
        candidate=candidate.evaluation,
    )

    result = compare_aligned_cross_border_scoring_policies(
        baseline=baseline,
        candidate=candidate,
    )

    assert result.comparison == expected


def test_blocked_baseline_blocks_comparison():
    baseline = _blocked_policy(
        CrossBorderScoringPolicyKind.BASELINE
    )
    candidate = _aligned_policy(
        CrossBorderScoringPolicyKind.CANDIDATE
    )

    assert (
        baseline.state
        is AlignedCrossBorderScoringPolicyEvaluationState.BLOCKED
    )

    result = compare_aligned_cross_border_scoring_policies(
        baseline=baseline,
        candidate=candidate,
    )

    assert (
        result.state
        is AlignedCrossBorderScoringPolicyComparisonState.BLOCKED
    )
    assert result.comparison is None
    assert result.reasons == (
        "baseline_policy_evaluation_not_available",
    )


def test_blocked_candidate_blocks_comparison():
    baseline = _aligned_policy(
        CrossBorderScoringPolicyKind.BASELINE
    )
    candidate = _blocked_policy(
        CrossBorderScoringPolicyKind.CANDIDATE
    )

    result = compare_aligned_cross_border_scoring_policies(
        baseline=baseline,
        candidate=candidate,
    )

    assert (
        result.state
        is AlignedCrossBorderScoringPolicyComparisonState.BLOCKED
    )
    assert result.comparison is None
    assert result.reasons == (
        "candidate_policy_evaluation_not_available",
    )


def test_both_blocked_preserve_both_reasons():
    baseline = _blocked_policy(
        CrossBorderScoringPolicyKind.BASELINE
    )
    candidate = _blocked_policy(
        CrossBorderScoringPolicyKind.CANDIDATE
    )

    result = compare_aligned_cross_border_scoring_policies(
        baseline=baseline,
        candidate=candidate,
    )

    assert result.reasons == (
        "baseline_policy_evaluation_not_available",
        "candidate_policy_evaluation_not_available",
    )


def test_blocked_input_does_not_invoke_comparison_authority():
    baseline = _blocked_policy(
        CrossBorderScoringPolicyKind.BASELINE
    )
    candidate = _aligned_policy(
        CrossBorderScoringPolicyKind.CANDIDATE
    )

    target = (
        "app.services.recommendation."
        "cross_border_aligned_scoring_policy_comparison."
        "compare_cross_border_scoring_policies"
    )

    with patch(target) as comparison:
        result = compare_aligned_cross_border_scoring_policies(
            baseline=baseline,
            candidate=candidate,
        )

    comparison.assert_not_called()
    assert result.comparison is None


def test_exact_nested_evaluations_are_delegated():
    baseline, candidate = _available_pair()

    canonical_comparison = compare_cross_border_scoring_policies(
        baseline=baseline.evaluation,
        candidate=candidate.evaluation,
    )

    target = (
        "app.services.recommendation."
        "cross_border_aligned_scoring_policy_comparison."
        "compare_cross_border_scoring_policies"
    )

    with patch(
        target,
        return_value=canonical_comparison,
    ) as comparison:
        result = compare_aligned_cross_border_scoring_policies(
            baseline=baseline,
            candidate=candidate,
        )

    comparison.assert_called_once_with(
        baseline=baseline.evaluation,
        candidate=candidate.evaluation,
    )
    assert result.comparison is canonical_comparison


def test_canonical_comparable_semantics_are_preserved():
    baseline, candidate = _available_pair()

    result = compare_aligned_cross_border_scoring_policies(
        baseline=baseline,
        candidate=candidate,
    )

    assert result.comparison is not None
    assert (
        result.comparison.state
        is CrossBorderPolicyComparisonState.COMPARABLE
    )


def test_result_is_immutable():
    baseline, candidate = _available_pair()

    result = compare_aligned_cross_border_scoring_policies(
        baseline=baseline,
        candidate=candidate,
    )

    with pytest.raises(FrozenInstanceError):
        result.reasons = ("changed",)


def test_adapter_exposes_no_adoption_activation_or_scoring_authority():
    baseline, candidate = _available_pair()

    result = compare_aligned_cross_border_scoring_policies(
        baseline=baseline,
        candidate=candidate,
    )

    forbidden = {
        "adoption",
        "adoption_readiness",
        "adoption_decision",
        "activation",
        "activation_readiness",
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


def test_adapter_does_not_mutate_aligned_evaluations():
    baseline, candidate = _available_pair()

    baseline_evaluation = baseline.evaluation
    candidate_evaluation = candidate.evaluation

    compare_aligned_cross_border_scoring_policies(
        baseline=baseline,
        candidate=candidate,
    )

    assert baseline.evaluation is baseline_evaluation
    assert candidate.evaluation is candidate_evaluation
