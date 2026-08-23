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
    AlignedCrossBorderConsumptionState,
    gate_aligned_cross_border_consumption,
)
from app.services.recommendation.cross_border_aligned_evaluation_readiness import (
    AlignedCrossBorderEvaluationReadiness,
    AlignedCrossBorderEvaluationState,
    evaluate_aligned_cross_border_readiness,
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
from app.services.recommendation.cross_border_evaluation_readiness import (
    CrossBorderEvaluationReadinessState,
    evaluate_cross_border_readiness,
)
from app.services.recommendation.cross_border_evidence import (
    CanonicalCrossBorderRecommendationEvidence,
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


def _aligned_gate(
    evidence: CanonicalCrossBorderRecommendationEvidence | None = None,
):
    return gate_aligned_cross_border_consumption(
        evidence=evidence or _evidence(),
        alignment=_alignment(),
    )


def _rejected_gate():
    evidence = replace(
        _evidence(),
        first_candidate_ref="candidate:other",
    )

    return gate_aligned_cross_border_consumption(
        evidence=evidence,
        alignment=_alignment(),
    )


def test_aligned_gate_enters_existing_readiness_boundary():
    gate = _aligned_gate()

    result = evaluate_aligned_cross_border_readiness(
        gate
    )

    assert isinstance(
        result,
        AlignedCrossBorderEvaluationReadiness,
    )
    assert (
        result.state
        is AlignedCrossBorderEvaluationState.AVAILABLE
    )
    assert result.is_available is True
    assert result.gate is gate
    assert result.readiness is not None
    assert (
        result.readiness.state
        is CrossBorderEvaluationReadinessState.READY
    )
    assert result.reasons == ()


def test_aligned_result_matches_existing_readiness_authority():
    gate = _aligned_gate()

    expected = evaluate_cross_border_readiness(
        gate.evidence
    )

    result = evaluate_aligned_cross_border_readiness(
        gate
    )

    assert result.readiness == expected


def test_rejected_gate_is_blocked():
    gate = _rejected_gate()

    assert (
        gate.state
        is AlignedCrossBorderConsumptionState.REJECTED
    )

    result = evaluate_aligned_cross_border_readiness(
        gate
    )

    assert (
        result.state
        is AlignedCrossBorderEvaluationState.BLOCKED
    )
    assert result.is_available is False
    assert result.gate is gate
    assert result.readiness is None
    assert result.reasons == (
        "cross_border_consumption_not_aligned",
    )


def test_rejected_gate_does_not_invoke_readiness_authority():
    gate = _rejected_gate()

    target = (
        "app.services.recommendation."
        "cross_border_aligned_evaluation_readiness."
        "evaluate_cross_border_readiness"
    )

    with patch(target) as readiness:
        result = evaluate_aligned_cross_border_readiness(
            gate
        )

    readiness.assert_not_called()
    assert result.readiness is None


def test_structural_not_ready_remains_distinct_from_blocked():
    evidence = replace(
        _evidence(),
        currency="US1",
    )
    gate = _aligned_gate(
        evidence=evidence
    )

    assert gate.is_aligned is True

    result = evaluate_aligned_cross_border_readiness(
        gate
    )

    assert (
        result.state
        is AlignedCrossBorderEvaluationState.AVAILABLE
    )
    assert result.readiness is not None
    assert (
        result.readiness.state
        is CrossBorderEvaluationReadinessState.NOT_READY
    )
    assert "currency" in result.readiness.reasons
    assert result.reasons == ()


def test_exact_gate_evidence_is_delegated():
    gate = _aligned_gate()

    target = (
        "app.services.recommendation."
        "cross_border_aligned_evaluation_readiness."
        "evaluate_cross_border_readiness"
    )

    canonical_readiness = evaluate_cross_border_readiness(
        gate.evidence
    )

    with patch(
        target,
        return_value=canonical_readiness,
    ) as readiness:
        result = evaluate_aligned_cross_border_readiness(
            gate
        )

    readiness.assert_called_once_with(
        gate.evidence
    )
    assert result.readiness is canonical_readiness


def test_result_is_immutable():
    result = evaluate_aligned_cross_border_readiness(
        _aligned_gate()
    )

    with pytest.raises(FrozenInstanceError):
        result.reasons = ("changed",)


def test_enforcement_exposes_no_later_stage_authority():
    result = evaluate_aligned_cross_border_readiness(
        _aligned_gate()
    )

    forbidden = {
        "signal",
        "advantage",
        "scoring_readiness",
        "scoring_input",
        "score",
        "weight",
        "rank",
        "winner",
        "recommendation",
        "selected_candidate",
        "shipping_route",
    }

    assert forbidden.isdisjoint(
        vars(result)
    )


def test_enforcement_does_not_mutate_gate_or_evidence():
    gate = _aligned_gate()

    original_evidence = gate.evidence
    original_first = (
        gate.evidence.first_candidate_ref
    )
    original_second = (
        gate.evidence.second_candidate_ref
    )

    evaluate_aligned_cross_border_readiness(
        gate
    )

    assert gate.evidence is original_evidence
    assert (
        gate.evidence.first_candidate_ref
        == original_first
    )
    assert (
        gate.evidence.second_candidate_ref
        == original_second
    )
