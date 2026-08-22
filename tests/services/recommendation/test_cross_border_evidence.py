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
from app.services.recommendation.cross_border_evidence import (
    CanonicalCrossBorderRecommendationEvidence,
    build_canonical_cross_border_evidence,
)
from app.services.recommendation.cross_border_handoff import (
    CrossBorderHandoffInbound,
    CrossBorderHandoffInboundState,
    accept_cross_border_handoff,
)


def _handoff(
    *,
    schema_version: str = "1.0",
):
    evidence = RecommendationHandoffEvidence(
        first_candidate_ref="amazon-us:offer:123",
        second_candidate_ref="korea-direct:offer:456",
        relation=LandedCostCandidateRelation.FIRST_LESS,
        first_total=Decimal("100.50"),
        second_total=Decimal("120.75"),
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

    return version_recommendation_handoff(
        evidence,
        contract=RecommendationHandoffContractIdentity(
            schema_version=schema_version,
        ),
    )


def _accepted_inbound(
) -> CrossBorderHandoffInbound:
    return accept_cross_border_handoff(
        _handoff()
    )


def test_accepted_inbound_builds_canonical_evidence():
    canonical = (
        build_canonical_cross_border_evidence(
            _accepted_inbound()
        )
    )

    assert isinstance(
        canonical,
        CanonicalCrossBorderRecommendationEvidence,
    )


def test_candidate_references_are_preserved():
    canonical = (
        build_canonical_cross_border_evidence(
            _accepted_inbound()
        )
    )

    assert (
        canonical.first_candidate_ref
        == "amazon-us:offer:123"
    )

    assert (
        canonical.second_candidate_ref
        == "korea-direct:offer:456"
    )


def test_landed_cost_relation_becomes_primitive_value():
    canonical = (
        build_canonical_cross_border_evidence(
            _accepted_inbound()
        )
    )

    assert canonical.landed_cost_relation == "first_less"

    assert isinstance(
        canonical.landed_cost_relation,
        str,
    )


def test_landed_cost_totals_are_preserved():
    canonical = (
        build_canonical_cross_border_evidence(
            _accepted_inbound()
        )
    )

    assert (
        canonical.first_landed_cost
        == Decimal("100.50")
    )

    assert (
        canonical.second_landed_cost
        == Decimal("120.75")
    )


def test_currency_is_preserved():
    canonical = (
        build_canonical_cross_border_evidence(
            _accepted_inbound()
        )
    )

    assert canonical.currency == "USD"


def test_route_context_is_flattened():
    canonical = (
        build_canonical_cross_border_evidence(
            _accepted_inbound()
        )
    )

    assert canonical.origin_country == "KR"
    assert canonical.destination_country == "US"


def test_quality_values_become_primitives():
    canonical = (
        build_canonical_cross_border_evidence(
            _accepted_inbound()
        )
    )

    assert canonical.first_evidence_quality == "known"

    assert (
        canonical.second_evidence_quality
        == "estimated"
    )

    assert isinstance(
        canonical.first_evidence_quality,
        str,
    )


def test_source_contract_identity_is_preserved():
    canonical = (
        build_canonical_cross_border_evidence(
            _accepted_inbound()
        )
    )

    assert (
        canonical.source_schema_id
        == (
            "commerce_ai.cross_border."
            "recommendation_handoff"
        )
    )

    assert canonical.source_schema_version == "1.0"


def test_compatible_minor_source_version_is_preserved():
    inbound = accept_cross_border_handoff(
        _handoff(
            schema_version="1.7",
        )
    )

    canonical = (
        build_canonical_cross_border_evidence(
            inbound
        )
    )

    assert canonical.source_schema_version == "1.7"


def test_rejected_inbound_cannot_build_canonical_evidence():
    inbound = CrossBorderHandoffInbound(
        state=CrossBorderHandoffInboundState.REJECTED,
        evidence=None,
        schema_id=(
            "commerce_ai.cross_border."
            "recommendation_handoff"
        ),
        schema_version="2.0",
        reason="major version mismatch",
    )

    with pytest.raises(
        ValueError,
        match="not accepted",
    ):
        build_canonical_cross_border_evidence(
            inbound
        )


def test_accepted_but_missing_evidence_is_rejected():
    inbound = CrossBorderHandoffInbound(
        state=CrossBorderHandoffInboundState.ACCEPTED,
        evidence=None,
        schema_id=(
            "commerce_ai.cross_border."
            "recommendation_handoff"
        ),
        schema_version="1.0",
        reason="synthetic invalid state",
    )

    with pytest.raises(
        ValueError,
        match="evidence is missing",
    ):
        build_canonical_cross_border_evidence(
            inbound
        )


def test_canonical_evidence_is_immutable():
    canonical = (
        build_canonical_cross_border_evidence(
            _accepted_inbound()
        )
    )

    with pytest.raises(
        FrozenInstanceError,
    ):
        canonical.currency = "KRW"


def test_canonical_constructor_normalizes_strings():
    canonical = CanonicalCrossBorderRecommendationEvidence(
        first_candidate_ref="  first  ",
        second_candidate_ref="  second  ",
        landed_cost_relation="  first_less  ",
        first_landed_cost=Decimal("10"),
        second_landed_cost=Decimal("20"),
        currency=" usd ",
        origin_country=" kr ",
        destination_country=" us ",
        first_evidence_quality=" known ",
        second_evidence_quality=" estimated ",
        source_schema_id=" schema ",
        source_schema_version=" 1.0 ",
    )

    assert canonical.first_candidate_ref == "first"
    assert canonical.second_candidate_ref == "second"
    assert canonical.landed_cost_relation == "first_less"
    assert canonical.currency == "USD"
    assert canonical.origin_country == "KR"
    assert canonical.destination_country == "US"
    assert canonical.first_evidence_quality == "known"
    assert canonical.second_evidence_quality == "estimated"
    assert canonical.source_schema_id == "schema"
    assert canonical.source_schema_version == "1.0"


def test_blank_required_value_is_rejected():
    with pytest.raises(
        ValueError,
        match="blank required values",
    ):
        CanonicalCrossBorderRecommendationEvidence(
            first_candidate_ref=" ",
            second_candidate_ref="second",
            landed_cost_relation="first_less",
            first_landed_cost=Decimal("10"),
            second_landed_cost=Decimal("20"),
            currency="USD",
            origin_country="KR",
            destination_country="US",
            first_evidence_quality="known",
            second_evidence_quality="estimated",
            source_schema_id="schema",
            source_schema_version="1.0",
        )


def test_negative_first_cost_is_rejected():
    with pytest.raises(
        ValueError,
        match="first_landed_cost",
    ):
        CanonicalCrossBorderRecommendationEvidence(
            first_candidate_ref="first",
            second_candidate_ref="second",
            landed_cost_relation="first_less",
            first_landed_cost=Decimal("-1"),
            second_landed_cost=Decimal("20"),
            currency="USD",
            origin_country="KR",
            destination_country="US",
            first_evidence_quality="known",
            second_evidence_quality="estimated",
            source_schema_id="schema",
            source_schema_version="1.0",
        )


def test_negative_second_cost_is_rejected():
    with pytest.raises(
        ValueError,
        match="second_landed_cost",
    ):
        CanonicalCrossBorderRecommendationEvidence(
            first_candidate_ref="first",
            second_candidate_ref="second",
            landed_cost_relation="first_less",
            first_landed_cost=Decimal("10"),
            second_landed_cost=Decimal("-1"),
            currency="USD",
            origin_country="KR",
            destination_country="US",
            first_evidence_quality="known",
            second_evidence_quality="estimated",
            source_schema_id="schema",
            source_schema_version="1.0",
        )


def test_build_does_not_mutate_inbound_or_source():
    inbound = _accepted_inbound()

    source = inbound.evidence

    canonical = (
        build_canonical_cross_border_evidence(
            inbound
        )
    )

    assert (
        inbound.state
        is CrossBorderHandoffInboundState.ACCEPTED
    )

    assert inbound.evidence is source

    assert (
        canonical.first_candidate_ref
        == source.first_candidate_ref
    )


def test_canonical_evidence_has_no_ranking_surface():
    canonical = (
        build_canonical_cross_border_evidence(
            _accepted_inbound()
        )
    )

    forbidden = {
        "rank",
        "ranking",
        "score",
        "priority",
    }

    public_names = {
        name.lower()
        for name in dir(canonical)
        if not name.startswith("_")
    }

    assert forbidden.isdisjoint(public_names)


def test_canonical_evidence_has_no_recommendation_surface():
    canonical = (
        build_canonical_cross_border_evidence(
            _accepted_inbound()
        )
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
        for name in dir(canonical)
        if not name.startswith("_")
    }

    assert forbidden.isdisjoint(public_names)


def test_canonical_evidence_has_no_preference_surface():
    canonical = (
        build_canonical_cross_border_evidence(
            _accepted_inbound()
        )
    )

    forbidden = {
        "user_preference",
        "price_weight",
        "quality_weight",
        "trust_weight",
    }

    public_names = {
        name.lower()
        for name in dir(canonical)
        if not name.startswith("_")
    }

    assert forbidden.isdisjoint(public_names)


def test_canonical_evidence_has_no_transaction_surface():
    canonical = (
        build_canonical_cross_border_evidence(
            _accepted_inbound()
        )
    )

    forbidden = {
        "checkout",
        "payment",
        "purchase",
        "dispatch",
        "book_shipment",
    }

    public_names = {
        name.lower()
        for name in dir(canonical)
        if not name.startswith("_")
    }

    assert forbidden.isdisjoint(public_names)
