from __future__ import annotations

from dataclasses import FrozenInstanceError
from decimal import Decimal

import pytest

from app.services.cross_border import (
    CrossBorderEvaluationContext,
    LandedCostAggregationQuality,
    LandedCostCandidateRelation,
    RecommendationHandoffContractIdentity,
    RecommendationHandoffEvidence,
    version_recommendation_handoff,
)
from app.services.recommendation.cross_border_handoff import (
    CROSS_BORDER_HANDOFF_SUPPORTED_MAJOR_VERSION,
    CrossBorderHandoffInbound,
    CrossBorderHandoffInboundState,
    accept_cross_border_handoff,
)


def _evidence() -> RecommendationHandoffEvidence:
    return RecommendationHandoffEvidence(
        first_candidate_ref="amazon-us:offer:123",
        second_candidate_ref="korea-direct:offer:456",
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
    schema_id: str = (
        "commerce_ai.cross_border."
        "recommendation_handoff"
    ),
    schema_version: str = "1.0",
):
    return version_recommendation_handoff(
        _evidence(),
        contract=RecommendationHandoffContractIdentity(
            schema_id=schema_id,
            schema_version=schema_version,
        ),
    )


def test_supported_major_version_is_explicit():
    assert (
        CROSS_BORDER_HANDOFF_SUPPORTED_MAJOR_VERSION
        == 1
    )


def test_canonical_cross_border_handoff_is_accepted():
    result = accept_cross_border_handoff(
        _handoff()
    )

    assert (
        result.state
        is CrossBorderHandoffInboundState.ACCEPTED
    )


def test_accepted_handoff_exposes_evidence():
    handoff = _handoff()

    result = accept_cross_border_handoff(
        handoff
    )

    assert result.evidence is handoff.evidence


def test_accepted_handoff_preserves_schema_identity():
    result = accept_cross_border_handoff(
        _handoff()
    )

    assert (
        result.schema_id
        == (
            "commerce_ai.cross_border."
            "recommendation_handoff"
        )
    )

    assert result.schema_version == "1.0"


def test_compatible_minor_version_is_accepted():
    result = accept_cross_border_handoff(
        _handoff(
            schema_version="1.9",
        )
    )

    assert (
        result.state
        is CrossBorderHandoffInboundState.ACCEPTED
    )


def test_incompatible_major_version_is_rejected():
    result = accept_cross_border_handoff(
        _handoff(
            schema_version="2.0",
        )
    )

    assert (
        result.state
        is CrossBorderHandoffInboundState.REJECTED
    )

    assert result.evidence is None

    assert result.reason == "major version mismatch"


def test_wrong_schema_family_is_rejected():
    result = accept_cross_border_handoff(
        _handoff(
            schema_id="external.other_contract",
        )
    )

    assert (
        result.state
        is CrossBorderHandoffInboundState.REJECTED
    )

    assert result.evidence is None

    assert result.reason == "schema_id mismatch"


def test_rejected_result_preserves_received_contract_identity():
    result = accept_cross_border_handoff(
        _handoff(
            schema_version="2.0",
        )
    )

    assert result.schema_version == "2.0"


def test_inbound_result_is_immutable():
    result = accept_cross_border_handoff(
        _handoff()
    )

    with pytest.raises(
        FrozenInstanceError,
    ):
        result.reason = "mutated"


def test_adapter_does_not_mutate_handoff():
    handoff = _handoff()

    accept_cross_border_handoff(
        handoff
    )

    assert handoff.contract.schema_version == "1.0"

    assert (
        handoff.evidence.first_candidate_ref
        == "amazon-us:offer:123"
    )


def test_inbound_result_has_no_ranking_surface():
    result = accept_cross_border_handoff(
        _handoff()
    )

    forbidden = {
        "rank",
        "ranking",
        "score",
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


def test_inbound_result_has_no_recommendation_surface():
    result = accept_cross_border_handoff(
        _handoff()
    )

    forbidden = {
        "winner",
        "recommend",
        "recommended_candidate",
        "selected_candidate",
        "preferred_candidate",
    }

    public_names = {
        name.lower()
        for name in dir(result)
        if not name.startswith("_")
    }

    assert forbidden.isdisjoint(
        public_names
    )


def test_inbound_result_has_no_user_preference_surface():
    result = accept_cross_border_handoff(
        _handoff()
    )

    forbidden = {
        "user_preference",
        "price_weight",
        "quality_weight",
        "trust_weight",
    }

    public_names = {
        name.lower()
        for name in dir(result)
        if not name.startswith("_")
    }

    assert forbidden.isdisjoint(
        public_names
    )


def test_inbound_result_has_no_transaction_surface():
    result = accept_cross_border_handoff(
        _handoff()
    )

    forbidden = {
        "checkout",
        "payment",
        "book_shipment",
        "dispatch",
        "purchase",
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
        for state in CrossBorderHandoffInboundState
    } == {
        "accepted",
        "rejected",
    }


def test_accepted_result_is_canonical_type():
    result = accept_cross_border_handoff(
        _handoff()
    )

    assert isinstance(
        result,
        CrossBorderHandoffInbound,
    )
