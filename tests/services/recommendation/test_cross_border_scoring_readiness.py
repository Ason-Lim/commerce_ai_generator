from __future__ import annotations

from dataclasses import FrozenInstanceError
from decimal import Decimal

import pytest

from app.services.recommendation.cross_border_landed_cost_signal import (
    CrossBorderLandedCostAdvantage,
    CrossBorderLandedCostSignal,
    CrossBorderLandedCostSignalState,
)
from app.services.recommendation.cross_border_scoring_readiness import (
    CrossBorderScoringReadiness,
    CrossBorderScoringReadinessState,
    evaluate_cross_border_scoring_readiness,
)


def _signal(
    **overrides,
) -> CrossBorderLandedCostSignal:
    values = {
        "state": CrossBorderLandedCostSignalState.AVAILABLE,
        "first_candidate_ref": "candidate:first",
        "second_candidate_ref": "candidate:second",
        "first_landed_cost": Decimal("100"),
        "second_landed_cost": Decimal("120"),
        "currency": "USD",
        "advantage": CrossBorderLandedCostAdvantage.FIRST,
        "first_evidence_quality": "known",
        "second_evidence_quality": "estimated",
        "source_schema_id": (
            "commerce_ai.cross_border."
            "recommendation_handoff"
        ),
        "source_schema_version": "1.0",
        "reason": "landed-cost signal available",
    }

    values.update(overrides)

    return CrossBorderLandedCostSignal(
        **values
    )


def test_complete_available_signal_is_scoring_ready():
    result = evaluate_cross_border_scoring_readiness(
        _signal()
    )

    assert (
        result.state
        is CrossBorderScoringReadinessState.READY
    )

    assert result.reasons == ()


def test_result_is_canonical_type():
    result = evaluate_cross_border_scoring_readiness(
        _signal()
    )

    assert isinstance(
        result,
        CrossBorderScoringReadiness,
    )


def test_all_dimensions_are_ready_for_valid_signal():
    result = evaluate_cross_border_scoring_readiness(
        _signal()
    )

    assert result.signal_available is True
    assert result.comparison_direction_ready is True
    assert result.candidate_identity_ready is True
    assert result.landed_cost_values_ready is True
    assert result.currency_ready is True
    assert result.evidence_quality_ready is True
    assert result.source_contract_ready is True


@pytest.mark.parametrize(
    "advantage",
    [
        CrossBorderLandedCostAdvantage.FIRST,
        CrossBorderLandedCostAdvantage.SECOND,
        CrossBorderLandedCostAdvantage.EQUAL,
    ],
)
def test_directional_or_equal_advantage_can_be_ready(
    advantage,
):
    result = evaluate_cross_border_scoring_readiness(
        _signal(
            advantage=advantage,
        )
    )

    assert (
        result.state
        is CrossBorderScoringReadinessState.READY
    )


def test_not_comparable_is_not_scoring_ready():
    result = evaluate_cross_border_scoring_readiness(
        _signal(
            advantage=(
                CrossBorderLandedCostAdvantage.NOT_COMPARABLE
            ),
        )
    )

    assert (
        result.state
        is CrossBorderScoringReadinessState.NOT_READY
    )

    assert "comparison_direction" in result.reasons


def test_unavailable_signal_is_not_scoring_ready():
    result = evaluate_cross_border_scoring_readiness(
        _signal(
            state=(
                CrossBorderLandedCostSignalState.UNAVAILABLE
            ),
            advantage=(
                CrossBorderLandedCostAdvantage.NOT_COMPARABLE
            ),
        )
    )

    assert (
        result.state
        is CrossBorderScoringReadinessState.NOT_READY
    )

    assert "signal_available" in result.reasons


def test_unavailable_signal_does_not_gain_directional_readiness():
    result = evaluate_cross_border_scoring_readiness(
        _signal(
            state=(
                CrossBorderLandedCostSignalState.UNAVAILABLE
            ),
            advantage=CrossBorderLandedCostAdvantage.FIRST,
        )
    )

    assert result.signal_available is False
    assert result.comparison_direction_ready is False


def test_same_candidate_identity_is_not_ready():
    result = evaluate_cross_border_scoring_readiness(
        _signal(
            second_candidate_ref="candidate:first",
        )
    )

    assert (
        result.state
        is CrossBorderScoringReadinessState.NOT_READY
    )

    assert "candidate_identity" in result.reasons


@pytest.mark.parametrize(
    "currency",
    [
        "",
        "US",
        "USDD",
        "12D",
        "usd",
    ],
)
def test_invalid_currency_is_not_ready(
    currency: str,
):
    result = evaluate_cross_border_scoring_readiness(
        _signal(
            currency=currency,
        )
    )

    assert (
        result.state
        is CrossBorderScoringReadinessState.NOT_READY
    )

    assert "currency" in result.reasons


@pytest.mark.parametrize(
    "quality",
    [
        "",
        "unknown",
        "missing",
        "unverified",
    ],
)
def test_invalid_first_quality_is_not_ready(
    quality: str,
):
    result = evaluate_cross_border_scoring_readiness(
        _signal(
            first_evidence_quality=quality,
        )
    )

    assert (
        result.state
        is CrossBorderScoringReadinessState.NOT_READY
    )

    assert "evidence_quality" in result.reasons


@pytest.mark.parametrize(
    "quality",
    [
        "",
        "unknown",
        "missing",
        "unverified",
    ],
)
def test_invalid_second_quality_is_not_ready(
    quality: str,
):
    result = evaluate_cross_border_scoring_readiness(
        _signal(
            second_evidence_quality=quality,
        )
    )

    assert (
        result.state
        is CrossBorderScoringReadinessState.NOT_READY
    )

    assert "evidence_quality" in result.reasons


def test_known_known_quality_is_ready():
    result = evaluate_cross_border_scoring_readiness(
        _signal(
            first_evidence_quality="known",
            second_evidence_quality="known",
        )
    )

    assert (
        result.state
        is CrossBorderScoringReadinessState.READY
    )


def test_estimated_estimated_quality_is_ready():
    result = evaluate_cross_border_scoring_readiness(
        _signal(
            first_evidence_quality="estimated",
            second_evidence_quality="estimated",
        )
    )

    assert (
        result.state
        is CrossBorderScoringReadinessState.READY
    )


def test_blank_source_schema_id_is_not_ready():
    result = evaluate_cross_border_scoring_readiness(
        _signal(
            source_schema_id="",
        )
    )

    assert (
        result.state
        is CrossBorderScoringReadinessState.NOT_READY
    )

    assert "source_contract" in result.reasons


def test_blank_source_schema_version_is_not_ready():
    result = evaluate_cross_border_scoring_readiness(
        _signal(
            source_schema_version="",
        )
    )

    assert (
        result.state
        is CrossBorderScoringReadinessState.NOT_READY
    )

    assert "source_contract" in result.reasons


def test_multiple_failures_are_reported():
    result = evaluate_cross_border_scoring_readiness(
        _signal(
            state=(
                CrossBorderLandedCostSignalState.UNAVAILABLE
            ),
            second_candidate_ref="candidate:first",
            currency="US",
            advantage=(
                CrossBorderLandedCostAdvantage.NOT_COMPARABLE
            ),
            first_evidence_quality="unknown",
            source_schema_id="",
        )
    )

    assert set(result.reasons) == {
        "signal_available",
        "comparison_direction",
        "candidate_identity",
        "currency",
        "evidence_quality",
        "source_contract",
    }


def test_readiness_result_is_immutable():
    result = evaluate_cross_border_scoring_readiness(
        _signal()
    )

    with pytest.raises(
        FrozenInstanceError,
    ):
        result.signal_available = False


def test_readiness_vocabulary_is_bounded():
    assert {
        state.value
        for state in CrossBorderScoringReadinessState
    } == {
        "ready",
        "not_ready",
    }


def test_result_has_no_score_value_surface():
    result = evaluate_cross_border_scoring_readiness(
        _signal()
    )

    forbidden = {
        "score",
        "final_score",
        "price_score",
        "ranking_score",
        "score_delta",
        "score_adjustment",
    }

    public_names = {
        name.lower()
        for name in dir(result)
        if not name.startswith("_")
    }

    assert forbidden.isdisjoint(
        public_names
    )


def test_result_has_no_weight_surface():
    result = evaluate_cross_border_scoring_readiness(
        _signal()
    )

    forbidden = {
        "weight",
        "price_weight",
        "landed_cost_weight",
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


def test_result_has_no_ranking_or_winner_surface():
    result = evaluate_cross_border_scoring_readiness(
        _signal()
    )

    forbidden = {
        "rank",
        "winner",
        "winning_candidate",
        "best_candidate",
        "preferred_candidate",
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


def test_result_has_no_recommendation_surface():
    result = evaluate_cross_border_scoring_readiness(
        _signal()
    )

    forbidden = {
        "recommend",
        "recommended_candidate",
        "priority",
        "user_preference",
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
    result = evaluate_cross_border_scoring_readiness(
        _signal()
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


def test_readiness_does_not_mutate_signal():
    signal = _signal()

    original_state = signal.state
    original_advantage = signal.advantage

    evaluate_cross_border_scoring_readiness(
        signal
    )

    assert signal.state is original_state
    assert signal.advantage is original_advantage
