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
    AlignedCrossBorderEvaluationState,
    evaluate_aligned_cross_border_readiness,
)
from app.services.recommendation.cross_border_aligned_landed_cost_signal import (
    AlignedCrossBorderLandedCostSignal,
    AlignedCrossBorderLandedCostSignalState,
    build_aligned_cross_border_landed_cost_signal,
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
from app.services.recommendation.cross_border_landed_cost_signal import (
    CrossBorderLandedCostSignalState,
    build_cross_border_landed_cost_signal,
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


def _aligned_evaluation(
    evidence: CanonicalCrossBorderRecommendationEvidence | None = None,
):
    gate = gate_aligned_cross_border_consumption(
        evidence=evidence or _evidence(),
        alignment=_alignment(),
    )

    return evaluate_aligned_cross_border_readiness(
        gate
    )


def _blocked_evaluation():
    gate = gate_aligned_cross_border_consumption(
        evidence=replace(
            _evidence(),
            first_candidate_ref="candidate:other",
        ),
        alignment=_alignment(),
    )

    return evaluate_aligned_cross_border_readiness(
        gate
    )


def test_available_ready_evaluation_builds_existing_signal():
    evaluation = _aligned_evaluation()

    result = build_aligned_cross_border_landed_cost_signal(
        evaluation
    )

    assert isinstance(
        result,
        AlignedCrossBorderLandedCostSignal,
    )
    assert (
        result.state
        is AlignedCrossBorderLandedCostSignalState.AVAILABLE
    )
    assert result.is_available is True
    assert result.evaluation is evaluation
    assert result.signal is not None
    assert (
        result.signal.state
        is CrossBorderLandedCostSignalState.AVAILABLE
    )
    assert result.reasons == ()


def test_available_result_matches_existing_signal_authority():
    evaluation = _aligned_evaluation()

    expected = build_cross_border_landed_cost_signal(
        evidence=evaluation.gate.evidence,
        readiness=evaluation.readiness,
    )

    result = build_aligned_cross_border_landed_cost_signal(
        evaluation
    )

    assert result.signal == expected


def test_blocked_evaluation_blocks_signal_build():
    evaluation = _blocked_evaluation()

    assert (
        evaluation.state
        is AlignedCrossBorderEvaluationState.BLOCKED
    )

    result = build_aligned_cross_border_landed_cost_signal(
        evaluation
    )

    assert (
        result.state
        is AlignedCrossBorderLandedCostSignalState.BLOCKED
    )
    assert result.is_available is False
    assert result.evaluation is evaluation
    assert result.signal is None
    assert result.reasons == (
        "cross_border_evaluation_not_available",
    )


def test_blocked_evaluation_does_not_invoke_signal_authority():
    evaluation = _blocked_evaluation()

    target = (
        "app.services.recommendation."
        "cross_border_aligned_landed_cost_signal."
        "build_cross_border_landed_cost_signal"
    )

    with patch(target) as signal_builder:
        result = build_aligned_cross_border_landed_cost_signal(
            evaluation
        )

    signal_builder.assert_not_called()
    assert result.signal is None


def test_structural_not_ready_remains_signal_unavailable_not_blocked():
    evaluation = _aligned_evaluation(
        evidence=replace(
            _evidence(),
            currency="US1",
        )
    )

    assert (
        evaluation.state
        is AlignedCrossBorderEvaluationState.AVAILABLE
    )
    assert evaluation.readiness is not None

    result = build_aligned_cross_border_landed_cost_signal(
        evaluation
    )

    assert (
        result.state
        is AlignedCrossBorderLandedCostSignalState.AVAILABLE
    )
    assert result.signal is not None
    assert (
        result.signal.state
        is CrossBorderLandedCostSignalState.UNAVAILABLE
    )


def test_exact_evidence_and_readiness_are_delegated():
    evaluation = _aligned_evaluation()

    canonical_signal = build_cross_border_landed_cost_signal(
        evidence=evaluation.gate.evidence,
        readiness=evaluation.readiness,
    )

    target = (
        "app.services.recommendation."
        "cross_border_aligned_landed_cost_signal."
        "build_cross_border_landed_cost_signal"
    )

    with patch(
        target,
        return_value=canonical_signal,
    ) as signal_builder:
        result = build_aligned_cross_border_landed_cost_signal(
            evaluation
        )

    signal_builder.assert_called_once_with(
        evidence=evaluation.gate.evidence,
        readiness=evaluation.readiness,
    )
    assert result.signal is canonical_signal


def test_result_is_immutable():
    result = build_aligned_cross_border_landed_cost_signal(
        _aligned_evaluation()
    )

    with pytest.raises(FrozenInstanceError):
        result.reasons = ("changed",)


def test_adapter_exposes_no_scoring_or_ranking_authority():
    result = build_aligned_cross_border_landed_cost_signal(
        _aligned_evaluation()
    )

    forbidden = {
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


def test_adapter_does_not_mutate_evaluation_or_evidence():
    evaluation = _aligned_evaluation()

    original_gate = evaluation.gate
    original_evidence = evaluation.gate.evidence
    original_readiness = evaluation.readiness

    build_aligned_cross_border_landed_cost_signal(
        evaluation
    )

    assert evaluation.gate is original_gate
    assert evaluation.gate.evidence is original_evidence
    assert evaluation.readiness is original_readiness
