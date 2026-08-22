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
from app.services.cross_border.recommendation_handoff_contract import (
    RECOMMENDATION_HANDOFF_SCHEMA_ID,
    RECOMMENDATION_HANDOFF_SCHEMA_VERSION,
    RecommendationHandoffContractIdentity,
    VersionedRecommendationHandoff,
    version_recommendation_handoff,
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


def test_canonical_schema_identity_constants():
    assert (
        RECOMMENDATION_HANDOFF_SCHEMA_ID
        == (
            "commerce_ai.cross_border."
            "recommendation_handoff"
        )
    )

    assert (
        RECOMMENDATION_HANDOFF_SCHEMA_VERSION
        == "1.0"
    )


def test_default_contract_identity_is_canonical():
    identity = (
        RecommendationHandoffContractIdentity()
    )

    assert (
        identity.schema_id
        == RECOMMENDATION_HANDOFF_SCHEMA_ID
    )

    assert (
        identity.schema_version
        == RECOMMENDATION_HANDOFF_SCHEMA_VERSION
    )


def test_contract_identity_is_immutable():
    identity = (
        RecommendationHandoffContractIdentity()
    )

    with pytest.raises(FrozenInstanceError):
        identity.schema_version = "2.0"


def test_schema_id_is_normalized():
    identity = RecommendationHandoffContractIdentity(
        schema_id=(
            "  commerce_ai.cross_border."
            "recommendation_handoff  "
        ),
    )

    assert (
        identity.schema_id
        == RECOMMENDATION_HANDOFF_SCHEMA_ID
    )


def test_schema_version_is_normalized():
    identity = RecommendationHandoffContractIdentity(
        schema_version="  1.0  ",
    )

    assert identity.schema_version == "1.0"


def test_blank_schema_id_is_rejected():
    with pytest.raises(
        ValueError,
        match="schema_id must be non-empty",
    ):
        RecommendationHandoffContractIdentity(
            schema_id="   ",
        )


@pytest.mark.parametrize(
    "version",
    [
        "",
        "1",
        "1.",
        ".1",
        "1.0.0",
        "v1.0",
        "01.0",
        "1.00",
        "1.x",
    ],
)
def test_invalid_schema_version_is_rejected(
    version: str,
):
    with pytest.raises(
        ValueError,
        match="schema_version",
    ):
        RecommendationHandoffContractIdentity(
            schema_version=version,
        )


def test_major_and_minor_version_are_exposed():
    identity = RecommendationHandoffContractIdentity(
        schema_version="12.34",
    )

    assert identity.major_version == 12
    assert identity.minor_version == 34


def test_same_schema_same_major_is_compatible():
    first = RecommendationHandoffContractIdentity(
        schema_version="1.0",
    )

    second = RecommendationHandoffContractIdentity(
        schema_version="1.7",
    )

    assert (
        first.is_compatible_with(second)
        is True
    )

    assert (
        second.is_compatible_with(first)
        is True
    )


def test_different_major_is_not_compatible():
    first = RecommendationHandoffContractIdentity(
        schema_version="1.9",
    )

    second = RecommendationHandoffContractIdentity(
        schema_version="2.0",
    )

    assert (
        first.is_compatible_with(second)
        is False
    )


def test_different_schema_id_is_not_compatible():
    first = RecommendationHandoffContractIdentity()

    second = RecommendationHandoffContractIdentity(
        schema_id="external.other_contract",
        schema_version="1.0",
    )

    assert (
        first.is_compatible_with(second)
        is False
    )


def test_handoff_can_be_wrapped_with_default_contract():
    evidence = _evidence()

    versioned = version_recommendation_handoff(
        evidence
    )

    assert isinstance(
        versioned,
        VersionedRecommendationHandoff,
    )

    assert (
        versioned.contract.schema_id
        == RECOMMENDATION_HANDOFF_SCHEMA_ID
    )

    assert (
        versioned.contract.schema_version
        == RECOMMENDATION_HANDOFF_SCHEMA_VERSION
    )

    assert versioned.evidence is evidence


def test_explicit_contract_identity_is_preserved():
    evidence = _evidence()

    contract = RecommendationHandoffContractIdentity(
        schema_version="1.4",
    )

    versioned = version_recommendation_handoff(
        evidence,
        contract=contract,
    )

    assert versioned.contract is contract
    assert versioned.evidence is evidence


def test_versioning_does_not_mutate_evidence():
    evidence = _evidence()

    version_recommendation_handoff(
        evidence
    )

    assert (
        evidence.first_candidate_ref
        == "amazon-us:offer:123"
    )

    assert (
        evidence.second_candidate_ref
        == "korea-direct:offer:456"
    )

    assert (
        evidence.relation
        is LandedCostCandidateRelation.FIRST_LESS
    )


def test_versioned_handoff_has_no_decision_surface():
    versioned = version_recommendation_handoff(
        _evidence()
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
        for name in dir(versioned)
        if not name.startswith("_")
    }

    assert forbidden.isdisjoint(
        public_names
    )


def test_contract_identity_has_no_consumer_execution_surface():
    identity = (
        RecommendationHandoffContractIdentity()
    )

    forbidden = {
        "send",
        "publish",
        "dispatch",
        "consume",
        "invoke",
        "recommend",
        "rank",
        "select",
    }

    public_names = {
        name.lower()
        for name in dir(identity)
        if not name.startswith("_")
    }

    assert forbidden.isdisjoint(
        public_names
    )
