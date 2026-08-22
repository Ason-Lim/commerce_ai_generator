from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.services.cross_border.recommendation_handoff_contract import (
    RecommendationHandoffContractIdentity,
    VersionedRecommendationHandoff,
)


class RecommendationHandoffAcceptanceState(
    str,
    Enum,
):
    ACCEPTED = "accepted"
    REJECTED = "rejected"


@dataclass(frozen=True)
class RecommendationHandoffConsumerExpectation:
    """
    Canonical consumer-side contract expectation.

    This object expresses only which outbound schema family and
    major version a consumer is prepared to accept.

    It does not identify or invoke a concrete Recommendation Engine.
    """

    schema_id: str
    major_version: int

    def __post_init__(self) -> None:
        schema_id = self.schema_id.strip()

        if not schema_id:
            raise ValueError(
                "schema_id must be non-empty"
            )

        if self.major_version < 0:
            raise ValueError(
                "major_version must be non-negative"
            )

        object.__setattr__(
            self,
            "schema_id",
            schema_id,
        )


@dataclass(frozen=True)
class RecommendationHandoffAcceptance:
    """
    Immutable acceptance result for a versioned outbound handoff.

    ACCEPTED means only that the handoff contract is structurally
    compatible with the stated consumer expectation.

    It does not mean the handoff has been consumed or acted upon.
    """

    state: RecommendationHandoffAcceptanceState

    producer_contract: RecommendationHandoffContractIdentity
    expected_schema_id: str
    expected_major_version: int

    reason: str


def evaluate_recommendation_handoff_acceptance(
    *,
    handoff: VersionedRecommendationHandoff,
    expectation: RecommendationHandoffConsumerExpectation,
) -> RecommendationHandoffAcceptance:
    """
    Evaluate whether a versioned Cross-Border handoff is compatible
    with a declared consumer contract expectation.

    No consumer invocation, ranking, recommendation, selection,
    scoring, or transaction execution is performed.
    """

    contract = handoff.contract

    if (
        contract.schema_id
        != expectation.schema_id
    ):
        return RecommendationHandoffAcceptance(
            state=(
                RecommendationHandoffAcceptanceState.REJECTED
            ),
            producer_contract=contract,
            expected_schema_id=expectation.schema_id,
            expected_major_version=(
                expectation.major_version
            ),
            reason="schema_id mismatch",
        )

    if (
        contract.major_version
        != expectation.major_version
    ):
        return RecommendationHandoffAcceptance(
            state=(
                RecommendationHandoffAcceptanceState.REJECTED
            ),
            producer_contract=contract,
            expected_schema_id=expectation.schema_id,
            expected_major_version=(
                expectation.major_version
            ),
            reason="major version mismatch",
        )

    return RecommendationHandoffAcceptance(
        state=(
            RecommendationHandoffAcceptanceState.ACCEPTED
        ),
        producer_contract=contract,
        expected_schema_id=expectation.schema_id,
        expected_major_version=(
            expectation.major_version
        ),
        reason="handoff contract is compatible",
    )
