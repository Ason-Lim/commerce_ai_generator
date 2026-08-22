from __future__ import annotations

from dataclasses import FrozenInstanceError
from decimal import Decimal

import pytest

from app.services.recommendation.cross_border_evaluation_readiness import (
    CrossBorderEvaluationReadinessState,
    evaluate_cross_border_readiness,
)
from app.services.recommendation.cross_border_evidence import (
    CanonicalCrossBorderRecommendationEvidence,
)
from app.services.recommendation.cross_border_landed_cost_signal import (
    CrossBorderLandedCostAdvantage,
    CrossBorderLandedCostSignal,
    CrossBorderLandedCostSignalState,
    build_cross_border_landed_cost_signal,
)


def _evidence(
    **overrides,
) -> CanonicalCrossBorderRecommendationEvidence:
    values = {
        "first_candidate_ref": "candidate:first",
        "second_candidate_ref": "candidate:second",
        "landed_cost_relation": "first_less",
        "first_landed_cost": Decimal("100"),
        "second_landed_cost": Decimal("120"),
        "currency": "USD",
        "origin_country": "KR",
        "destination_country": "US",
        "first_evidence_quality": "known",
        "second_evidence_quality": "estimated",
        "source_schema_id": (
            "commerce_ai.cross_border."
            "recommendation_handoff"
        ),
        "source_schema_version": "1.0",
    }

    values.update(overrides)

    return CanonicalCrossBorderRecommendationEvidence(
        **values
    )


def _signal(
    evidence=None,
):
    if evidence is None:
        evidence = _evidence()

    readiness = evaluate_cross_border_readiness(
        evidence
    )

    return build_cross_border_landed_cost_signal(
        evidence=evidence,
        readiness=readiness,
    )


def test_ready_evidence_builds_available_signal():
    result = _signal()

    assert (
        result.state
        is CrossBorderLandedCostSignalState.AVAILABLE
    )


def test_signal_is_canonical_type():
    result = _signal()

    assert isinstance(
        result,
        CrossBorderLandedCostSignal,
    )


def test_first_less_maps_to_first_advantage():
    result = _signal(
        _evidence(
            landed_cost_relation="first_less",
        )
    )

    assert (
        result.advantage
        is CrossBorderLandedCostAdvantage.FIRST
    )


def test_second_less_maps_to_second_advantage():
    result = _signal(
        _evidence(
            landed_cost_relation="second_less",
            first_landed_cost=Decimal("120"),
            second_landed_cost=Decimal("100"),
        )
    )

    assert (
        result.advantage
        is CrossBorderLandedCostAdvantage.SECOND
    )


def test_equal_maps_to_equal_advantage():
    result = _signal(
        _evidence(
            landed_cost_relation="equal",
            first_landed_cost=Decimal("100"),
            second_landed_cost=Decimal("100"),
        )
    )

    assert (
        result.advantage
        is CrossBorderLandedCostAdvantage.EQUAL
    )


def test_not_comparable_maps_to_not_comparable():
    result = _signal(
        _evidence(
            landed_cost_relation="not_comparable",
        )
    )

    assert (
        result.advantage
        is CrossBorderLandedCostAdvantage.NOT_COMPARABLE
    )


def test_signal_preserves_candidate_references():
    result = _signal()

    assert (
        result.first_candidate_ref
        == "candidate:first"
    )

    assert (
        result.second_candidate_ref
        == "candidate:second"
    )


def test_signal_preserves_landed_costs():
    result = _signal()

    assert (
        result.first_landed_cost
        == Decimal("100")
    )

    assert (
        result.second_landed_cost
        == Decimal("120")
    )


def test_signal_preserves_currency():
    result = _signal()

    assert result.currency == "USD"


def test_signal_preserves_evidence_quality():
    result = _signal()

    assert result.first_evidence_quality == "known"
    assert (
        result.second_evidence_quality
        == "estimated"
    )


def test_signal_preserves_source_contract():
    result = _signal()

    assert (
        result.source_schema_id
        == (
            "commerce_ai.cross_border."
            "recommendation_handoff"
        )
    )

    assert result.source_schema_version == "1.0"


def test_not_ready_evidence_builds_unavailable_signal():
    evidence = _evidence(
        second_candidate_ref="candidate:first",
    )

    readiness = evaluate_cross_border_readiness(
        evidence
    )

    assert (
        readiness.state
        is CrossBorderEvaluationReadinessState.NOT_READY
    )

    result = build_cross_border_landed_cost_signal(
        evidence=evidence,
        readiness=readiness,
    )

    assert (
        result.state
        is CrossBorderLandedCostSignalState.UNAVAILABLE
    )


def test_unavailable_signal_has_no_candidate_advantage():
    evidence = _evidence(
        second_candidate_ref="candidate:first",
    )

    readiness = evaluate_cross_border_readiness(
        evidence
    )

    result = build_cross_border_landed_cost_signal(
        evidence=evidence,
        readiness=readiness,
    )

    assert (
        result.advantage
        is CrossBorderLandedCostAdvantage.NOT_COMPARABLE
    )


def test_signal_is_immutable():
    result = _signal()

    with pytest.raises(
        FrozenInstanceError,
    ):
        result.currency = "KRW"


def test_signal_state_vocabulary_is_bounded():
    assert {
        state.value
        for state in CrossBorderLandedCostSignalState
    } == {
        "available",
        "unavailable",
    }


def test_advantage_vocabulary_is_bounded():
    assert {
        state.value
        for state in CrossBorderLandedCostAdvantage
    } == {
        "first",
        "second",
        "equal",
        "not_comparable",
    }


def test_first_advantage_is_not_winner_surface():
    result = _signal()

    forbidden = {
        "winner",
        "winning_candidate",
        "best_candidate",
        "selected_candidate",
    }

    public_names = {
        name.lower()
        for name in dir(result)
        if not name.startswith("_")
    }

    assert forbidden.isdisjoint(
        public_names
    )


def test_signal_has_no_score_surface():
    result = _signal()

    forbidden = {
        "score",
        "final_score",
        "price_score",
        "ranking_score",
        "weight",
    }

    public_names = {
        name.lower()
        for name in dir(result)
        if not name.startswith("_")
    }

    assert forbidden.isdisjoint(
        public_names
    )


def test_signal_has_no_recommendation_surface():
    result = _signal()

    forbidden = {
        "recommend",
        "recommended_candidate",
        "preferred_candidate",
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


def test_signal_has_no_user_preference_surface():
    result = _signal()

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


def test_signal_has_no_transaction_surface():
    result = _signal()

    forbidden = {
        "checkout",
        "payment",
        "purchase",
        "dispatch",
        "book_shipment",
    }

    public_names = {
        name.lower()
        for name in dir(result)
        if not name.startswith("_")
    }

    assert forbidden.isdisjoint(
        public_names
    )


def test_signal_build_does_not_mutate_evidence():
    evidence = _evidence()

    original_first = evidence.first_landed_cost
    original_second = evidence.second_landed_cost

    _signal(evidence)

    assert (
        evidence.first_landed_cost
        == original_first
    )

    assert (
        evidence.second_landed_cost
        == original_second
    )
