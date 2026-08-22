from __future__ import annotations

from dataclasses import FrozenInstanceError
from decimal import Decimal

import pytest

from app.services.recommendation.cross_border_evaluation_readiness import (
    CrossBorderEvaluationReadiness,
    CrossBorderEvaluationReadinessState,
    evaluate_cross_border_readiness,
)
from app.services.recommendation.cross_border_evidence import (
    CanonicalCrossBorderRecommendationEvidence,
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


def test_complete_canonical_evidence_is_ready():
    result = evaluate_cross_border_readiness(
        _evidence()
    )

    assert (
        result.state
        is CrossBorderEvaluationReadinessState.READY
    )

    assert result.reasons == ()


def test_readiness_result_is_canonical_type():
    result = evaluate_cross_border_readiness(
        _evidence()
    )

    assert isinstance(
        result,
        CrossBorderEvaluationReadiness,
    )


def test_all_readiness_dimensions_are_true_when_ready():
    result = evaluate_cross_border_readiness(
        _evidence()
    )

    assert result.candidate_identity_ready is True
    assert result.landed_cost_ready is True
    assert result.currency_ready is True
    assert result.route_context_ready is True
    assert result.evidence_quality_ready is True
    assert result.source_contract_ready is True


def test_same_candidate_identity_is_not_ready():
    result = evaluate_cross_border_readiness(
        _evidence(
            second_candidate_ref="candidate:first",
        )
    )

    assert (
        result.state
        is CrossBorderEvaluationReadinessState.NOT_READY
    )

    assert "candidate_identity" in result.reasons


def test_unsupported_relation_is_not_ready():
    result = evaluate_cross_border_readiness(
        _evidence(
            landed_cost_relation="unknown_relation",
        )
    )

    assert (
        result.state
        is CrossBorderEvaluationReadinessState.NOT_READY
    )

    assert "landed_cost" in result.reasons


def test_equal_relation_can_be_ready():
    result = evaluate_cross_border_readiness(
        _evidence(
            landed_cost_relation="equal",
            first_landed_cost=Decimal("100"),
            second_landed_cost=Decimal("100"),
        )
    )

    assert (
        result.state
        is CrossBorderEvaluationReadinessState.READY
    )


def test_not_comparable_relation_can_be_structurally_ready():
    result = evaluate_cross_border_readiness(
        _evidence(
            landed_cost_relation="not_comparable",
        )
    )

    assert (
        result.state
        is CrossBorderEvaluationReadinessState.READY
    )


@pytest.mark.parametrize(
    "currency",
    [
        "US",
        "USDD",
        "12D",
        "usd1",
    ],
)
def test_invalid_currency_shape_is_not_ready(
    currency: str,
):
    result = evaluate_cross_border_readiness(
        _evidence(
            currency=currency,
        )
    )

    assert (
        result.state
        is CrossBorderEvaluationReadinessState.NOT_READY
    )

    assert "currency" in result.reasons


def test_same_origin_and_destination_is_not_ready():
    result = evaluate_cross_border_readiness(
        _evidence(
            destination_country="KR",
        )
    )

    assert (
        result.state
        is CrossBorderEvaluationReadinessState.NOT_READY
    )

    assert "route_context" in result.reasons


@pytest.mark.parametrize(
    "quality",
    [
        "unknown",
        "missing",
        "unverified",
    ],
)
def test_unsupported_first_quality_is_not_ready(
    quality: str,
):
    result = evaluate_cross_border_readiness(
        _evidence(
            first_evidence_quality=quality,
        )
    )

    assert (
        result.state
        is CrossBorderEvaluationReadinessState.NOT_READY
    )

    assert "evidence_quality" in result.reasons


@pytest.mark.parametrize(
    "quality",
    [
        "unknown",
        "missing",
        "unverified",
    ],
)
def test_unsupported_second_quality_is_not_ready(
    quality: str,
):
    result = evaluate_cross_border_readiness(
        _evidence(
            second_evidence_quality=quality,
        )
    )

    assert (
        result.state
        is CrossBorderEvaluationReadinessState.NOT_READY
    )

    assert "evidence_quality" in result.reasons


def test_known_known_evidence_is_ready():
    result = evaluate_cross_border_readiness(
        _evidence(
            first_evidence_quality="known",
            second_evidence_quality="known",
        )
    )

    assert (
        result.state
        is CrossBorderEvaluationReadinessState.READY
    )


def test_estimated_estimated_evidence_is_ready():
    result = evaluate_cross_border_readiness(
        _evidence(
            first_evidence_quality="estimated",
            second_evidence_quality="estimated",
        )
    )

    assert (
        result.state
        is CrossBorderEvaluationReadinessState.READY
    )


def test_multiple_failures_are_reported_without_decision():
    result = evaluate_cross_border_readiness(
        _evidence(
            second_candidate_ref="candidate:first",
            currency="US",
            destination_country="KR",
            first_evidence_quality="unknown",
        )
    )

    assert (
        result.state
        is CrossBorderEvaluationReadinessState.NOT_READY
    )

    assert set(result.reasons) == {
        "candidate_identity",
        "currency",
        "route_context",
        "evidence_quality",
    }


def test_readiness_result_is_immutable():
    result = evaluate_cross_border_readiness(
        _evidence()
    )

    with pytest.raises(
        FrozenInstanceError,
    ):
        result.state = (
            CrossBorderEvaluationReadinessState.NOT_READY
        )


def test_readiness_vocabulary_is_bounded():
    assert {
        state.value
        for state in CrossBorderEvaluationReadinessState
    } == {
        "ready",
        "not_ready",
    }


def test_result_has_no_score_surface():
    result = evaluate_cross_border_readiness(
        _evidence()
    )

    forbidden = {
        "score",
        "ranking_score",
        "final_score",
        "price_score",
    }

    public_names = {
        name.lower()
        for name in dir(result)
        if not name.startswith("_")
    }

    assert forbidden.isdisjoint(
        public_names
    )


def test_result_has_no_candidate_preference_surface():
    result = evaluate_cross_border_readiness(
        _evidence()
    )

    forbidden = {
        "winner",
        "preferred_candidate",
        "recommended_candidate",
        "selected_candidate",
        "best_candidate",
    }

    public_names = {
        name.lower()
        for name in dir(result)
        if not name.startswith("_")
    }

    assert forbidden.isdisjoint(
        public_names
    )


def test_result_has_no_user_preference_surface():
    result = evaluate_cross_border_readiness(
        _evidence()
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


def test_result_has_no_transaction_surface():
    result = evaluate_cross_border_readiness(
        _evidence()
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
        for name in dir(result)
        if not name.startswith("_")
    }

    assert forbidden.isdisjoint(
        public_names
    )


def test_readiness_does_not_mutate_evidence():
    evidence = _evidence()

    evaluate_cross_border_readiness(
        evidence
    )

    assert (
        evidence.first_candidate_ref
        == "candidate:first"
    )

    assert evidence.currency == "USD"
