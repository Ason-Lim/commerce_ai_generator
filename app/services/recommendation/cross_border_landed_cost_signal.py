from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

from app.services.recommendation.cross_border_evaluation_readiness import (
    CrossBorderEvaluationReadiness,
    CrossBorderEvaluationReadinessState,
)
from app.services.recommendation.cross_border_evidence import (
    CanonicalCrossBorderRecommendationEvidence,
)


class CrossBorderLandedCostSignalState(
    str,
    Enum,
):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"


class CrossBorderLandedCostAdvantage(
    str,
    Enum,
):
    FIRST = "first"
    SECOND = "second"
    EQUAL = "equal"
    NOT_COMPARABLE = "not_comparable"


@dataclass(frozen=True)
class CrossBorderLandedCostSignal:
    """
    Recommendation-owned bounded signal derived from canonical
    Cross-Border landed-cost evidence.

    The signal reports observable landed-cost comparison semantics
    only.

    It does not calculate a score, modify ranking, choose a winner,
    or produce a recommendation.
    """

    state: CrossBorderLandedCostSignalState

    first_candidate_ref: str
    second_candidate_ref: str

    first_landed_cost: Decimal
    second_landed_cost: Decimal

    currency: str

    advantage: CrossBorderLandedCostAdvantage

    first_evidence_quality: str
    second_evidence_quality: str

    source_schema_id: str
    source_schema_version: str

    reason: str


def build_cross_border_landed_cost_signal(
    *,
    evidence: CanonicalCrossBorderRecommendationEvidence,
    readiness: CrossBorderEvaluationReadiness,
) -> CrossBorderLandedCostSignal:
    """
    Build a bounded Recommendation-side landed-cost signal.

    A signal is AVAILABLE only when R1C declared the canonical
    evidence READY.

    No score, rank, preference weight, recommendation, selection,
    or transaction semantics are introduced.
    """

    if (
        readiness.state
        is not CrossBorderEvaluationReadinessState.READY
    ):
        return CrossBorderLandedCostSignal(
            state=CrossBorderLandedCostSignalState.UNAVAILABLE,
            first_candidate_ref=evidence.first_candidate_ref,
            second_candidate_ref=evidence.second_candidate_ref,
            first_landed_cost=evidence.first_landed_cost,
            second_landed_cost=evidence.second_landed_cost,
            currency=evidence.currency,
            advantage=(
                CrossBorderLandedCostAdvantage.NOT_COMPARABLE
            ),
            first_evidence_quality=(
                evidence.first_evidence_quality
            ),
            second_evidence_quality=(
                evidence.second_evidence_quality
            ),
            source_schema_id=evidence.source_schema_id,
            source_schema_version=(
                evidence.source_schema_version
            ),
            reason="cross-border evidence is not evaluation-ready",
        )

    relation = evidence.landed_cost_relation

    relation_to_advantage = {
        "first_less": CrossBorderLandedCostAdvantage.FIRST,
        "second_less": CrossBorderLandedCostAdvantage.SECOND,
        "equal": CrossBorderLandedCostAdvantage.EQUAL,
        "not_comparable": (
            CrossBorderLandedCostAdvantage.NOT_COMPARABLE
        ),
    }

    advantage = relation_to_advantage.get(
        relation,
        CrossBorderLandedCostAdvantage.NOT_COMPARABLE,
    )

    return CrossBorderLandedCostSignal(
        state=CrossBorderLandedCostSignalState.AVAILABLE,
        first_candidate_ref=evidence.first_candidate_ref,
        second_candidate_ref=evidence.second_candidate_ref,
        first_landed_cost=evidence.first_landed_cost,
        second_landed_cost=evidence.second_landed_cost,
        currency=evidence.currency,
        advantage=advantage,
        first_evidence_quality=(
            evidence.first_evidence_quality
        ),
        second_evidence_quality=(
            evidence.second_evidence_quality
        ),
        source_schema_id=evidence.source_schema_id,
        source_schema_version=evidence.source_schema_version,
        reason="landed-cost signal available",
    )
