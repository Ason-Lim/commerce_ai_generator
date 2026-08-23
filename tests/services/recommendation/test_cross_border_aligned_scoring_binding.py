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
    AlignedCrossBorderScoringBinding,
    AlignedCrossBorderScoringBindingState,
    bind_aligned_cross_border_scoring_input,
)
from app.services.recommendation.cross_border_aligned_scoring_readiness import (
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
from app.services.recommendation.cross_border_scoring_binding import (
    BoundCrossBorderScoringInput,
    bind_cross_border_scoring_input,
)
from app.services.recommendation.cross_border_scoring_readiness import (
    CrossBorderScoringReadinessState,
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


def _aligned_scoring_readiness(
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

    return evaluate_aligned_cross_border_scoring_readiness(
        signal
    )


def _blocked_scoring_readiness():
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

    signal = build_aligned_cross_border_landed_cost_signal(
        evaluation
    )

    return evaluate_aligned_cross_border_scoring_readiness(
        signal
    )


def test_available_ready_chain_binds_existing_scoring_input():
    aligned_readiness = _aligned_scoring_readiness()

    result = bind_aligned_cross_border_scoring_input(
        aligned_readiness
    )

    assert isinstance(
        result,
        AlignedCrossBorderScoringBinding,
    )
    assert (
        result.state
        is AlignedCrossBorderScoringBindingState.AVAILABLE
    )
    assert result.is_available is True
    assert result.aligned_readiness is aligned_readiness
    assert isinstance(
        result.scoring_input,
        BoundCrossBorderScoringInput,
    )
    assert result.reasons == ()


def test_available_result_matches_existing_binding_authority():
    aligned_readiness = _aligned_scoring_readiness()

    expected = bind_cross_border_scoring_input(
        signal=aligned_readiness.aligned_signal.signal,
        readiness=aligned_readiness.readiness,
    )

    result = bind_aligned_cross_border_scoring_input(
        aligned_readiness
    )

    assert result.scoring_input == expected


def test_blocked_aligned_readiness_blocks_binding():
    aligned_readiness = _blocked_scoring_readiness()

    assert (
        aligned_readiness.state
        is AlignedCrossBorderScoringReadinessState.BLOCKED
    )

    result = bind_aligned_cross_border_scoring_input(
        aligned_readiness
    )

    assert (
        result.state
        is AlignedCrossBorderScoringBindingState.BLOCKED
    )
    assert result.is_available is False
    assert result.scoring_input is None
    assert result.reasons == (
        "cross_border_scoring_readiness_not_available",
    )


def test_blocked_aligned_readiness_does_not_invoke_binding_authority():
    aligned_readiness = _blocked_scoring_readiness()

    target = (
        "app.services.recommendation."
        "cross_border_aligned_scoring_binding."
        "bind_cross_border_scoring_input"
    )

    with patch(target) as binding:
        result = bind_aligned_cross_border_scoring_input(
            aligned_readiness
        )

    binding.assert_not_called()
    assert result.scoring_input is None


def test_nested_not_ready_blocks_binding_without_reinterpreting_as_unavailable():
    aligned_readiness = _aligned_scoring_readiness(
        evidence=replace(
            _evidence(),
            currency="US1",
        )
    )

    assert (
        aligned_readiness.state
        is AlignedCrossBorderScoringReadinessState.AVAILABLE
    )
    assert aligned_readiness.readiness is not None
    assert (
        aligned_readiness.readiness.state
        is CrossBorderScoringReadinessState.NOT_READY
    )

    result = bind_aligned_cross_border_scoring_input(
        aligned_readiness
    )

    assert (
        result.state
        is AlignedCrossBorderScoringBindingState.BLOCKED
    )
    assert result.scoring_input is None
    assert result.reasons == (
        "cross_border_scoring_not_ready",
    )


def test_nested_not_ready_does_not_invoke_binding_authority():
    aligned_readiness = _aligned_scoring_readiness(
        evidence=replace(
            _evidence(),
            currency="US1",
        )
    )

    target = (
        "app.services.recommendation."
        "cross_border_aligned_scoring_binding."
        "bind_cross_border_scoring_input"
    )

    with patch(target) as binding:
        result = bind_aligned_cross_border_scoring_input(
            aligned_readiness
        )

    binding.assert_not_called()
    assert result.scoring_input is None


def test_exact_nested_signal_and_readiness_are_delegated():
    aligned_readiness = _aligned_scoring_readiness()

    canonical_input = bind_cross_border_scoring_input(
        signal=aligned_readiness.aligned_signal.signal,
        readiness=aligned_readiness.readiness,
    )

    target = (
        "app.services.recommendation."
        "cross_border_aligned_scoring_binding."
        "bind_cross_border_scoring_input"
    )

    with patch(
        target,
        return_value=canonical_input,
    ) as binding:
        result = bind_aligned_cross_border_scoring_input(
            aligned_readiness
        )

    binding.assert_called_once_with(
        signal=aligned_readiness.aligned_signal.signal,
        readiness=aligned_readiness.readiness,
    )
    assert result.scoring_input is canonical_input


def test_result_is_immutable():
    result = bind_aligned_cross_border_scoring_input(
        _aligned_scoring_readiness()
    )

    with pytest.raises(FrozenInstanceError):
        result.reasons = ("changed",)


def test_adapter_exposes_no_policy_scoring_or_ranking_authority():
    result = bind_aligned_cross_border_scoring_input(
        _aligned_scoring_readiness()
    )

    forbidden = {
        "score",
        "weight",
        "policy",
        "policy_result",
        "rank",
        "winner",
        "recommendation",
        "selected_candidate",
        "shipping_route",
    }

    assert forbidden.isdisjoint(
        vars(result)
    )


def test_adapter_does_not_mutate_aligned_readiness():
    aligned_readiness = _aligned_scoring_readiness()

    original_signal = aligned_readiness.aligned_signal
    original_readiness = aligned_readiness.readiness

    bind_aligned_cross_border_scoring_input(
        aligned_readiness
    )

    assert (
        aligned_readiness.aligned_signal
        is original_signal
    )
    assert aligned_readiness.readiness is original_readiness
