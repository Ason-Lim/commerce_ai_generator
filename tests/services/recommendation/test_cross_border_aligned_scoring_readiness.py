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
    AlignedCrossBorderLandedCostSignalState,
    build_aligned_cross_border_landed_cost_signal,
)
from app.services.recommendation.cross_border_aligned_scoring_readiness import (
    AlignedCrossBorderScoringReadiness,
    AlignedCrossBorderScoringReadinessState,
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
from app.services.recommendation.cross_border_scoring_readiness import (
    CrossBorderScoringReadinessState,
    evaluate_cross_border_scoring_readiness,
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


def _aligned_signal(
    evidence: CanonicalCrossBorderRecommendationEvidence | None = None,
):
    gate = gate_aligned_cross_border_consumption(
        evidence=evidence or _evidence(),
        alignment=_alignment(),
    )

    evaluation = evaluate_aligned_cross_border_readiness(
        gate
    )

    return build_aligned_cross_border_landed_cost_signal(
        evaluation
    )


def _blocked_signal():
    gate = gate_aligned_cross_border_consumption(
        evidence=replace(
            _evidence(),
            first_candidate_ref="candidate:other",
        ),
        alignment=_alignment(),
    )

    evaluation = evaluate_aligned_cross_border_readiness(
        gate
    )

    return build_aligned_cross_border_landed_cost_signal(
        evaluation
    )


def test_available_signal_enters_existing_scoring_readiness():
    aligned_signal = _aligned_signal()

    result = evaluate_aligned_cross_border_scoring_readiness(
        aligned_signal
    )

    assert isinstance(
        result,
        AlignedCrossBorderScoringReadiness,
    )
    assert (
        result.state
        is AlignedCrossBorderScoringReadinessState.AVAILABLE
    )
    assert result.is_available is True
    assert result.aligned_signal is aligned_signal
    assert result.readiness is not None
    assert (
        result.readiness.state
        is CrossBorderScoringReadinessState.READY
    )
    assert result.reasons == ()


def test_available_result_matches_existing_scoring_readiness_authority():
    aligned_signal = _aligned_signal()

    expected = evaluate_cross_border_scoring_readiness(
        aligned_signal.signal
    )

    result = evaluate_aligned_cross_border_scoring_readiness(
        aligned_signal
    )

    assert result.readiness == expected


def test_blocked_signal_blocks_scoring_readiness():
    aligned_signal = _blocked_signal()

    assert (
        aligned_signal.state
        is AlignedCrossBorderLandedCostSignalState.BLOCKED
    )

    result = evaluate_aligned_cross_border_scoring_readiness(
        aligned_signal
    )

    assert (
        result.state
        is AlignedCrossBorderScoringReadinessState.BLOCKED
    )
    assert result.is_available is False
    assert result.aligned_signal is aligned_signal
    assert result.readiness is None
    assert result.reasons == (
        "cross_border_landed_cost_signal_not_available",
    )


def test_blocked_signal_does_not_invoke_scoring_readiness_authority():
    aligned_signal = _blocked_signal()

    target = (
        "app.services.recommendation."
        "cross_border_aligned_scoring_readiness."
        "evaluate_cross_border_scoring_readiness"
    )

    with patch(target) as scoring_readiness:
        result = evaluate_aligned_cross_border_scoring_readiness(
            aligned_signal
        )

    scoring_readiness.assert_not_called()
    assert result.readiness is None


def test_unavailable_nested_signal_remains_not_ready_not_blocked():
    aligned_signal = _aligned_signal(
        evidence=replace(
            _evidence(),
            currency="US1",
        )
    )

    assert (
        aligned_signal.state
        is AlignedCrossBorderLandedCostSignalState.AVAILABLE
    )
    assert aligned_signal.signal is not None

    result = evaluate_aligned_cross_border_scoring_readiness(
        aligned_signal
    )

    assert (
        result.state
        is AlignedCrossBorderScoringReadinessState.AVAILABLE
    )
    assert result.readiness is not None
    assert (
        result.readiness.state
        is CrossBorderScoringReadinessState.NOT_READY
    )


def test_exact_nested_signal_is_delegated():
    aligned_signal = _aligned_signal()

    canonical_readiness = (
        evaluate_cross_border_scoring_readiness(
            aligned_signal.signal
        )
    )

    target = (
        "app.services.recommendation."
        "cross_border_aligned_scoring_readiness."
        "evaluate_cross_border_scoring_readiness"
    )

    with patch(
        target,
        return_value=canonical_readiness,
    ) as scoring_readiness:
        result = evaluate_aligned_cross_border_scoring_readiness(
            aligned_signal
        )

    scoring_readiness.assert_called_once_with(
        aligned_signal.signal
    )
    assert result.readiness is canonical_readiness


def test_result_is_immutable():
    result = evaluate_aligned_cross_border_scoring_readiness(
        _aligned_signal()
    )

    with pytest.raises(FrozenInstanceError):
        result.reasons = ("changed",)


def test_adapter_exposes_no_scoring_binding_or_ranking_authority():
    result = evaluate_aligned_cross_border_scoring_readiness(
        _aligned_signal()
    )

    forbidden = {
        "scoring_input",
        "bound_input",
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


def test_adapter_does_not_mutate_aligned_signal():
    aligned_signal = _aligned_signal()

    original_nested_signal = aligned_signal.signal
    original_evaluation = aligned_signal.evaluation

    evaluate_aligned_cross_border_scoring_readiness(
        aligned_signal
    )

    assert aligned_signal.signal is original_nested_signal
    assert aligned_signal.evaluation is original_evaluation
