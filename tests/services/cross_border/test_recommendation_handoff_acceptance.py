from __future__ import annotations

from dataclasses import FrozenInstanceError
from decimal import Decimal

import pytest

from app.services.cross_border.context import (
    CrossBorderEvaluationContext,
)
from app.services.cross_border.landed_cost_aggregation import (
    LandedCostAggregationQuality,
)
from app.services.cross_border.landed_cost_candidate_comparison import (
    LandedCostCandidateRelation,
)
from app.services.cross_border.recommendation_handoff import (
    RecommendationHandoffEvidence,
)
from app.services.cross_border.recommendation_handoff_acceptance import (
    RecommendationHandoffAcceptanceState,
    RecommendationHandoffConsumerExpectation,
    evaluate_recommendation_handoff_acceptance,
)
from app.services.cross_border.recommendation_handoff_contract import (
    RECOMMENDATION_HANDOFF_SCHEMA_ID,
    RecommendationHandoffContractIdentity,
    version_recommendation_handoff,
)


def _evidence() -> RecommendationHandoffEvidence:
    return RecommendationHandoffEvidence(
        first_candidate_ref="candidate:first",
        second_candidate_ref="candidate:second",
        relation=LandedCostCandidateRelation.FIRST_LESS,
        first_total=Decimal("100"),
        second_total=Decimal("120"),
        currency="USD",
        context=CrossBorderEvaluationContext(
            origin_country="KR",
            destination_country="US",
        ),
        first_quality=LandedCostAggregationQuality.KNOWN,
        second_quality=(
            LandedCostAggregationQuality.ESTIMATED
        ),
    )


def _handoff(
    *,
    schema_id: str = RECOMMENDATION_HANDOFF_SCHEMA_ID,
    schema_version: str = "1.0",
):
    contract = RecommendationHandoffContractIdentity(
        schema_id=schema_id,
        schema_version=schema_version,
    )

    return version_recommendation_handoff(
        _evidence(),
        contract=contract,
    )


def _expectation(
    *,
    schema_id: str = RECOMMENDATION_HANDOFF_SCHEMA_ID,
    major_version: int = 1,
):
    return RecommendationHandoffConsumerExpectation(
        schema_id=schema_id,
        major_version=major_version,
    )


def test_matching_schema_and_major_is_accepted():
    result = evaluate_recommendation_handoff_acceptance(
        handoff=_handoff(),
        expectation=_expectation(),
    )

    assert (
        result.state
        is RecommendationHandoffAcceptanceState.ACCEPTED
    )


def test_minor_version_difference_is_accepted():
    result = evaluate_recommendation_handoff_acceptance(
        handoff=_handoff(
            schema_version="1.9",
        ),
        expectation=_expectation(
            major_version=1,
        ),
    )

    assert (
        result.state
        is RecommendationHandoffAcceptanceState.ACCEPTED
    )


def test_major_version_mismatch_is_rejected():
    result = evaluate_recommendation_handoff_acceptance(
        handoff=_handoff(
            schema_version="2.0",
        ),
        expectation=_expectation(
            major_version=1,
        ),
    )

    assert (
        result.state
        is RecommendationHandoffAcceptanceState.REJECTED
    )

    assert result.reason == "major version mismatch"


def test_schema_id_mismatch_is_rejected():
    result = evaluate_recommendation_handoff_acceptance(
        handoff=_handoff(),
        expectation=_expectation(
            schema_id="external.other_contract",
        ),
    )

    assert (
        result.state
        is RecommendationHandoffAcceptanceState.REJECTED
    )

    assert result.reason == "schema_id mismatch"


def test_expectation_schema_id_is_normalized():
    expectation = _expectation(
        schema_id=(
            "  commerce_ai.cross_border."
            "recommendation_handoff  "
        ),
    )

    assert (
        expectation.schema_id
        == RECOMMENDATION_HANDOFF_SCHEMA_ID
    )


def test_blank_expectation_schema_id_is_rejected():
    with pytest.raises(
        ValueError,
        match="schema_id must be non-empty",
    ):
        _expectation(
            schema_id="   ",
        )


def test_negative_major_version_is_rejected():
    with pytest.raises(
        ValueError,
        match="major_version must be non-negative",
    ):
        _expectation(
            major_version=-1,
        )


def test_expectation_is_immutable():
    expectation = _expectation()

    with pytest.raises(
        FrozenInstanceError,
    ):
        expectation.major_version = 2


def test_acceptance_preserves_producer_contract():
    handoff = _handoff(
        schema_version="1.4",
    )

    result = evaluate_recommendation_handoff_acceptance(
        handoff=handoff,
        expectation=_expectation(),
    )

    assert result.producer_contract is handoff.contract


def test_acceptance_preserves_expectation_identity():
    expectation = _expectation()

    result = evaluate_recommendation_handoff_acceptance(
        handoff=_handoff(),
        expectation=expectation,
    )

    assert (
        result.expected_schema_id
        == expectation.schema_id
    )

    assert (
        result.expected_major_version
        == expectation.major_version
    )


def test_acceptance_does_not_mutate_handoff():
    handoff = _handoff()

    evaluate_recommendation_handoff_acceptance(
        handoff=handoff,
        expectation=_expectation(),
    )

    assert (
        handoff.contract.schema_version
        == "1.0"
    )

    assert (
        handoff.evidence.first_candidate_ref
        == "candidate:first"
    )


def test_acceptance_result_has_no_decision_surface():
    result = evaluate_recommendation_handoff_acceptance(
        handoff=_handoff(),
        expectation=_expectation(),
    )

    forbidden = {
        "winner",
        "rank",
        "score",
        "recommended_candidate",
        "selected_candidate",
        "preferred_candidate",
        "user_preference",
        "priority",
    }

    public_names = {
        name.lower()
        for name in dir(result)
        if not name.startswith("_")
    }

    assert forbidden.isdisjoint(
        public_names
    )


def test_acceptance_has_no_consumer_execution_surface():
    result = evaluate_recommendation_handoff_acceptance(
        handoff=_handoff(),
        expectation=_expectation(),
    )

    forbidden = {
        "send",
        "publish",
        "dispatch",
        "consume",
        "invoke",
        "execute",
    }

    public_names = {
        name.lower()
        for name in dir(result)
        if not name.startswith("_")
    }

    assert forbidden.isdisjoint(
        public_names
    )


def test_acceptance_vocabulary_is_bounded():
    assert {
        state.value
        for state in RecommendationHandoffAcceptanceState
    } == {
        "accepted",
        "rejected",
    }
