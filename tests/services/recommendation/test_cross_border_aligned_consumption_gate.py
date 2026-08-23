from dataclasses import FrozenInstanceError, replace
from decimal import Decimal

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


def test_exact_alignment_is_accepted():
    evidence = _evidence()
    alignment = _alignment()

    result = gate_aligned_cross_border_consumption(
        evidence=evidence,
        alignment=alignment,
    )

    assert (
        result.state
        is AlignedCrossBorderConsumptionState.ALIGNED
    )
    assert result.is_aligned is True
    assert result.reasons == ()
    assert result.evidence is evidence
    assert result.alignment is alignment


def test_first_candidate_mismatch_is_rejected():
    evidence = replace(
        _evidence(),
        first_candidate_ref="candidate:other",
    )

    result = gate_aligned_cross_border_consumption(
        evidence=evidence,
        alignment=_alignment(),
    )

    assert (
        result.state
        is AlignedCrossBorderConsumptionState.REJECTED
    )
    assert result.is_aligned is False
    assert result.reasons == ("first_candidate_ref",)


def test_second_candidate_mismatch_is_rejected():
    evidence = replace(
        _evidence(),
        second_candidate_ref="candidate:other",
    )

    result = gate_aligned_cross_border_consumption(
        evidence=evidence,
        alignment=_alignment(),
    )

    assert (
        result.state
        is AlignedCrossBorderConsumptionState.REJECTED
    )
    assert result.reasons == ("second_candidate_ref",)


def test_swapped_canonical_candidate_refs_are_rejected():
    evidence = replace(
        _evidence(),
        first_candidate_ref="candidate:second",
        second_candidate_ref="candidate:first",
    )

    result = gate_aligned_cross_border_consumption(
        evidence=evidence,
        alignment=_alignment(),
    )

    assert (
        result.state
        is AlignedCrossBorderConsumptionState.REJECTED
    )
    assert result.reasons == (
        "first_candidate_ref",
        "second_candidate_ref",
    )


def test_non_identity_evidence_values_are_not_gate_responsibility():
    evidence = replace(
        _evidence(),
        landed_cost_relation="second_less",
        first_landed_cost=Decimal("999"),
        second_landed_cost=Decimal("1"),
        currency="KRW",
    )

    result = gate_aligned_cross_border_consumption(
        evidence=evidence,
        alignment=_alignment(),
    )

    assert (
        result.state
        is AlignedCrossBorderConsumptionState.ALIGNED
    )
    assert result.reasons == ()


def test_gate_result_is_immutable():
    result = gate_aligned_cross_border_consumption(
        evidence=_evidence(),
        alignment=_alignment(),
    )

    with pytest.raises(FrozenInstanceError):
        result.reasons = ("changed",)


def test_gate_exposes_no_scoring_or_ranking_authority():
    result = gate_aligned_cross_border_consumption(
        evidence=_evidence(),
        alignment=_alignment(),
    )

    forbidden = {
        "score",
        "weight",
        "rank",
        "winner",
        "recommendation",
        "selected_candidate",
        "shipping_route",
    }

    assert forbidden.isdisjoint(vars(result))


def test_gate_does_not_mutate_inputs():
    evidence = _evidence()
    alignment = _alignment()

    original_first = evidence.first_candidate_ref
    original_second = evidence.second_candidate_ref
    original_bound = alignment.bound_comparison

    gate_aligned_cross_border_consumption(
        evidence=evidence,
        alignment=alignment,
    )

    assert evidence.first_candidate_ref == original_first
    assert evidence.second_candidate_ref == original_second
    assert alignment.bound_comparison is original_bound
