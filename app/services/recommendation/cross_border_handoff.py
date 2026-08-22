from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.services.cross_border import (
    RECOMMENDATION_HANDOFF_SCHEMA_ID,
    RecommendationHandoffAcceptanceState,
    RecommendationHandoffConsumerExpectation,
    RecommendationHandoffEvidence,
    VersionedRecommendationHandoff,
    evaluate_recommendation_handoff_acceptance,
)


CROSS_BORDER_HANDOFF_SUPPORTED_MAJOR_VERSION = 1


class CrossBorderHandoffInboundState(
    str,
    Enum,
):
    ACCEPTED = "accepted"
    REJECTED = "rejected"


@dataclass(frozen=True)
class CrossBorderHandoffInbound:
    """
    Recommendation-side inbound boundary for Cross-Border evidence.

    ACCEPTED means that the versioned Cross-Border handoff satisfies
    the Recommendation-side contract expectation.

    This object does not rank, score, recommend, select, or execute
    transactions.
    """

    state: CrossBorderHandoffInboundState

    evidence: RecommendationHandoffEvidence | None

    schema_id: str
    schema_version: str

    reason: str


def _consumer_expectation(
) -> RecommendationHandoffConsumerExpectation:
    return RecommendationHandoffConsumerExpectation(
        schema_id=RECOMMENDATION_HANDOFF_SCHEMA_ID,
        major_version=(
            CROSS_BORDER_HANDOFF_SUPPORTED_MAJOR_VERSION
        ),
    )


def accept_cross_border_handoff(
    handoff: VersionedRecommendationHandoff,
) -> CrossBorderHandoffInbound:
    """
    Validate and accept a versioned Cross-Border handoff at the
    Recommendation Engine boundary.

    Contract acceptance only is performed here.

    No ranking, scoring, user preference application,
    recommendation, candidate selection, or transaction execution
    occurs in this adapter.
    """

    acceptance = (
        evaluate_recommendation_handoff_acceptance(
            handoff=handoff,
            expectation=_consumer_expectation(),
        )
    )

    contract = handoff.contract

    if (
        acceptance.state
        is RecommendationHandoffAcceptanceState.REJECTED
    ):
        return CrossBorderHandoffInbound(
            state=CrossBorderHandoffInboundState.REJECTED,
            evidence=None,
            schema_id=contract.schema_id,
            schema_version=contract.schema_version,
            reason=acceptance.reason,
        )

    return CrossBorderHandoffInbound(
        state=CrossBorderHandoffInboundState.ACCEPTED,
        evidence=handoff.evidence,
        schema_id=contract.schema_id,
        schema_version=contract.schema_version,
        reason="cross-border handoff accepted",
    )
