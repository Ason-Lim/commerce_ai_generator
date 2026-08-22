from __future__ import annotations

from decimal import Decimal

import pytest

from app.services.cross_border.context import (
    CrossBorderEvaluationContext,
)
from app.services.cross_border.landed_cost_aggregation import (
    LandedCostAggregationQuality,
)
from app.services.cross_border.landed_cost_bound_readiness import (
    BoundLandedCostReadiness,
    BoundLandedCostReadinessState,
)
from app.services.cross_border.landed_cost_candidate_comparison import (
    LandedCostCandidateComparison,
    LandedCostCandidateComparisonState,
    LandedCostCandidateRelation,
)
from app.services.cross_border.landed_cost_comparison_binding import (
    BoundLandedCostComparison,
    LandedCostCandidateRef,
)
from app.services.cross_border.recommendation_handoff import (
    RecommendationHandoffEvidence,
    build_recommendation_handoff_evidence,
)


def _context() -> CrossBorderEvaluationContext:
    return CrossBorderEvaluationContext(
        origin_country="KR",
        destination_country="US",
    )


def _bound() -> BoundLandedCostComparison:
    return BoundLandedCostComparison(
        first_candidate=LandedCostCandidateRef(
            candidate_ref="amazon-us:offer:123",
        ),
        second_candidate=LandedCostCandidateRef(
            candidate_ref="korea-direct:offer:456",
        ),
        comparison=LandedCostCandidateComparison(
            state=(
                LandedCostCandidateComparisonState.COMPARED
            ),
            relation=(
                LandedCostCandidateRelation.FIRST_LESS
            ),
            first_total=Decimal("100"),
            second_total=Decimal("120"),
            currency="USD",
            context=_context(),
            first_quality=(
                LandedCostAggregationQuality.KNOWN
            ),
            second_quality=(
                LandedCostAggregationQuality.ESTIMATED
            ),
            reason="bounded comparison",
        ),
    )


def _readiness() -> BoundLandedCostReadiness:
    return BoundLandedCostReadiness(
        state=BoundLandedCostReadinessState.READY,
        first_candidate_ref="amazon-us:offer:123",
        second_candidate_ref="korea-direct:offer:456",
        relation=LandedCostCandidateRelation.FIRST_LESS,
        currency="USD",
        context=_context(),
        first_quality=LandedCostAggregationQuality.KNOWN,
        second_quality=(
            LandedCostAggregationQuality.ESTIMATED
        ),
        reason="bound evidence complete",
    )


def test_ready_bound_evidence_can_build_handoff():
    handoff = build_recommendation_handoff_evidence(
        bound=_bound(),
        readiness=_readiness(),
    )

    assert isinstance(
        handoff,
        RecommendationHandoffEvidence,
    )


def test_candidate_references_are_preserved():
    handoff = build_recommendation_handoff_evidence(
        bound=_bound(),
        readiness=_readiness(),
    )

    assert (
        handoff.first_candidate_ref
        == "amazon-us:offer:123"
    )

    assert (
        handoff.second_candidate_ref
        == "korea-direct:offer:456"
    )


def test_relation_is_preserved():
    handoff = build_recommendation_handoff_evidence(
        bound=_bound(),
        readiness=_readiness(),
    )

    assert (
        handoff.relation
        is LandedCostCandidateRelation.FIRST_LESS
    )


def test_totals_are_preserved():
    handoff = build_recommendation_handoff_evidence(
        bound=_bound(),
        readiness=_readiness(),
    )

    assert handoff.first_total == Decimal("100")
    assert handoff.second_total == Decimal("120")


def test_currency_is_preserved():
    handoff = build_recommendation_handoff_evidence(
        bound=_bound(),
        readiness=_readiness(),
    )

    assert handoff.currency == "USD"


def test_context_is_preserved():
    handoff = build_recommendation_handoff_evidence(
        bound=_bound(),
        readiness=_readiness(),
    )

    assert handoff.context == _context()


def test_quality_metadata_is_preserved():
    handoff = build_recommendation_handoff_evidence(
        bound=_bound(),
        readiness=_readiness(),
    )

    assert (
        handoff.first_quality
        is LandedCostAggregationQuality.KNOWN
    )

    assert (
        handoff.second_quality
        is LandedCostAggregationQuality.ESTIMATED
    )


def test_not_ready_evidence_is_rejected():
    readiness = BoundLandedCostReadiness(
        state=BoundLandedCostReadinessState.NOT_READY,
        first_candidate_ref="amazon-us:offer:123",
        second_candidate_ref="korea-direct:offer:456",
        relation=None,
        currency=None,
        context=None,
        first_quality=None,
        second_quality=None,
        reason="incomplete",
    )

    with pytest.raises(
        ValueError,
        match="not ready for handoff",
    ):
        build_recommendation_handoff_evidence(
            bound=_bound(),
            readiness=readiness,
        )


def test_candidate_reference_mismatch_is_rejected():
    readiness = BoundLandedCostReadiness(
        state=BoundLandedCostReadinessState.READY,
        first_candidate_ref="wrong:first",
        second_candidate_ref="korea-direct:offer:456",
        relation=LandedCostCandidateRelation.FIRST_LESS,
        currency="USD",
        context=_context(),
        first_quality=LandedCostAggregationQuality.KNOWN,
        second_quality=(
            LandedCostAggregationQuality.ESTIMATED
        ),
        reason="synthetic mismatch",
    )

    with pytest.raises(
        ValueError,
        match="candidate references do not match",
    ):
        build_recommendation_handoff_evidence(
            bound=_bound(),
            readiness=readiness,
        )


def test_relation_mismatch_is_rejected():
    readiness = BoundLandedCostReadiness(
        state=BoundLandedCostReadinessState.READY,
        first_candidate_ref="amazon-us:offer:123",
        second_candidate_ref="korea-direct:offer:456",
        relation=LandedCostCandidateRelation.SECOND_LESS,
        currency="USD",
        context=_context(),
        first_quality=LandedCostAggregationQuality.KNOWN,
        second_quality=(
            LandedCostAggregationQuality.ESTIMATED
        ),
        reason="synthetic mismatch",
    )

    with pytest.raises(
        ValueError,
        match="relation does not match",
    ):
        build_recommendation_handoff_evidence(
            bound=_bound(),
            readiness=readiness,
        )


def test_currency_mismatch_is_rejected():
    readiness = BoundLandedCostReadiness(
        state=BoundLandedCostReadinessState.READY,
        first_candidate_ref="amazon-us:offer:123",
        second_candidate_ref="korea-direct:offer:456",
        relation=LandedCostCandidateRelation.FIRST_LESS,
        currency="KRW",
        context=_context(),
        first_quality=LandedCostAggregationQuality.KNOWN,
        second_quality=(
            LandedCostAggregationQuality.ESTIMATED
        ),
        reason="synthetic mismatch",
    )

    with pytest.raises(
        ValueError,
        match="currency does not match",
    ):
        build_recommendation_handoff_evidence(
            bound=_bound(),
            readiness=readiness,
        )


def test_context_mismatch_is_rejected():
    readiness = BoundLandedCostReadiness(
        state=BoundLandedCostReadinessState.READY,
        first_candidate_ref="amazon-us:offer:123",
        second_candidate_ref="korea-direct:offer:456",
        relation=LandedCostCandidateRelation.FIRST_LESS,
        currency="USD",
        context=CrossBorderEvaluationContext(
            origin_country="KR",
            destination_country="JP",
        ),
        first_quality=LandedCostAggregationQuality.KNOWN,
        second_quality=(
            LandedCostAggregationQuality.ESTIMATED
        ),
        reason="synthetic mismatch",
    )

    with pytest.raises(
        ValueError,
        match="context does not match",
    ):
        build_recommendation_handoff_evidence(
            bound=_bound(),
            readiness=readiness,
        )


def test_quality_mismatch_is_rejected():
    readiness = BoundLandedCostReadiness(
        state=BoundLandedCostReadinessState.READY,
        first_candidate_ref="amazon-us:offer:123",
        second_candidate_ref="korea-direct:offer:456",
        relation=LandedCostCandidateRelation.FIRST_LESS,
        currency="USD",
        context=_context(),
        first_quality=(
            LandedCostAggregationQuality.ESTIMATED
        ),
        second_quality=(
            LandedCostAggregationQuality.ESTIMATED
        ),
        reason="synthetic mismatch",
    )

    with pytest.raises(
        ValueError,
        match="quality metadata does not match",
    ):
        build_recommendation_handoff_evidence(
            bound=_bound(),
            readiness=readiness,
        )


def test_handoff_has_no_winner_surface():
    handoff = build_recommendation_handoff_evidence(
        bound=_bound(),
        readiness=_readiness(),
    )

    assert not hasattr(
        handoff,
        "winner",
    )

    assert not hasattr(
        handoff,
        "recommended_candidate",
    )

    assert not hasattr(
        handoff,
        "selected_candidate",
    )


def test_handoff_has_no_ranking_surface():
    handoff = build_recommendation_handoff_evidence(
        bound=_bound(),
        readiness=_readiness(),
    )

    assert not hasattr(
        handoff,
        "rank",
    )

    assert not hasattr(
        handoff,
        "score",
    )


def test_handoff_has_no_user_preference_surface():
    handoff = build_recommendation_handoff_evidence(
        bound=_bound(),
        readiness=_readiness(),
    )

    assert not hasattr(
        handoff,
        "user_preference",
    )

    assert not hasattr(
        handoff,
        "priority",
    )


def test_handoff_does_not_mutate_inputs():
    bound = _bound()
    readiness = _readiness()

    build_recommendation_handoff_evidence(
        bound=bound,
        readiness=readiness,
    )

    assert (
        bound.comparison.relation
        is LandedCostCandidateRelation.FIRST_LESS
    )

    assert (
        readiness.state
        is BoundLandedCostReadinessState.READY
    )
