from decimal import Decimal

import pytest

from app.services.cross_border.landed_cost_aggregation import (
    LandedCostAggregationQuality,
    LandedCostAggregationState,
)
from app.services.cross_border.landed_cost_estimate_disclosure import (
    LandedCostEstimateDisclosureEvidence,
)
from app.services.cross_border.landed_cost_temporal_evaluation import (
    LandedCostTemporalEvaluationState,
)
from app.services.recommendation.cross_border_candidate_disclosure_binding import (
    CrossBorderCandidateDisclosureBinding,
)
from app.services.recommendation.cross_border_candidate_disclosure_projection import (
    project_cross_border_candidate_disclosure,
)
from app.services.recommendation.models import (
    RecommendationCandidate,
    RecommendationPriority,
    RecommendationScoreComponents,
    RecommendationScoreResult,
)


def _score():
    return RecommendationScoreResult(
        final_score=80.0,
        priority=RecommendationPriority.MIX,
        components=RecommendationScoreComponents(
            price=80.0,
        ),
    )


def _candidate():
    return RecommendationCandidate(
        item={"product_id": "p-1"},
        score=_score(),
        rank=1,
        metadata={
            "source": "canonical",
            "cross_border": {
                "candidate_ref": "candidate:first",
                "candidate_position": 1,
                "landed_cost": 78.0,
            },
        },
    )


def _disclosure():
    return LandedCostEstimateDisclosureEvidence(
        total=Decimal("78.00"),
        currency="USD",
        aggregation_state=(
            LandedCostAggregationState.AGGREGATED
        ),
        aggregation_quality=(
            LandedCostAggregationQuality.ESTIMATED
        ),
        aggregation_reason="estimated landed cost",
        temporal_state=(
            LandedCostTemporalEvaluationState.EVALUABLE
        ),
        temporal_reason="currency evidence is fresh",
        fx_base_currency="USD",
        fx_quote_currency="KRW",
        fx_rate=Decimal("1390"),
        fx_retrieved_at="2026-08-24T07:00:00Z",
        fx_effective_at="2026-08-24T06:55:00Z",
    )


def _binding(
    *,
    candidate_ref="candidate:first",
    candidate_position=1,
):
    return CrossBorderCandidateDisclosureBinding(
        candidate_ref=candidate_ref,
        candidate_position=candidate_position,
        disclosure=_disclosure(),
    )


def test_projects_disclosure_into_cross_border_metadata():
    result = project_cross_border_candidate_disclosure(
        candidate=_candidate(),
        binding=_binding(),
    )

    disclosure = (
        result.metadata["cross_border"][
            "estimate_disclosure"
        ]
    )

    assert disclosure["total"] == Decimal("78.00")
    assert disclosure["currency"] == "USD"
    assert disclosure["fx_base_currency"] == "USD"
    assert disclosure["fx_quote_currency"] == "KRW"
    assert disclosure["fx_rate"] == Decimal("1390")


def test_preserves_item_score_and_rank():
    candidate = _candidate()

    result = project_cross_border_candidate_disclosure(
        candidate=candidate,
        binding=_binding(),
    )

    assert result.item == candidate.item
    assert result.score is candidate.score
    assert result.rank == candidate.rank


def test_preserves_existing_metadata():
    result = project_cross_border_candidate_disclosure(
        candidate=_candidate(),
        binding=_binding(),
    )

    assert result.metadata["source"] == "canonical"
    assert (
        result.metadata["cross_border"]["candidate_ref"]
        == "candidate:first"
    )
    assert (
        result.metadata["cross_border"]["candidate_position"]
        == 1
    )
    assert (
        result.metadata["cross_border"]["landed_cost"]
        == 78.0
    )


def test_rejects_candidate_ref_mismatch():
    with pytest.raises(
        ValueError,
        match="candidate_ref",
    ):
        project_cross_border_candidate_disclosure(
            candidate=_candidate(),
            binding=_binding(
                candidate_ref="candidate:other"
            ),
        )


def test_rejects_candidate_position_mismatch():
    with pytest.raises(
        ValueError,
        match="candidate_position",
    ):
        project_cross_border_candidate_disclosure(
            candidate=_candidate(),
            binding=_binding(
                candidate_position=2
            ),
        )


def test_does_not_create_customer_facing_disclosure_text():
    result = project_cross_border_candidate_disclosure(
        candidate=_candidate(),
        binding=_binding(),
    )

    forbidden = {
        "display_text",
        "customer_notice",
        "warning_text",
        "disclaimer",
        "checkout_total",
        "final_payment_amount",
        "card_fee",
        "payment_fee",
        "recommended_route",
    }

    cross_border = set(
        result.metadata["cross_border"]
    )

    disclosure = set(
        result.metadata["cross_border"][
            "estimate_disclosure"
        ]
    )

    assert forbidden.isdisjoint(cross_border)
    assert forbidden.isdisjoint(disclosure)
