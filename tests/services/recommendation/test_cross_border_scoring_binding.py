from __future__ import annotations

from dataclasses import FrozenInstanceError
from decimal import Decimal

import pytest

from app.services.recommendation.cross_border_landed_cost_signal import (
    CrossBorderLandedCostAdvantage,
    CrossBorderLandedCostSignal,
    CrossBorderLandedCostSignalState,
)
from app.services.recommendation.cross_border_scoring_binding import (
    BoundCrossBorderScoringInput,
    CrossBorderScoringDirection,
    bind_cross_border_scoring_input,
)
from app.services.recommendation.cross_border_scoring_readiness import (
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


def _bind(
    signal=None,
):
    if signal is None:
        signal = _signal()

    readiness = evaluate_cross_border_scoring_readiness(
        signal
    )

    return bind_cross_border_scoring_input(
        signal=signal,
        readiness=readiness,
    )


def test_ready_signal_binds_scoring_input():
    result = _bind()

    assert isinstance(
        result,
        BoundCrossBorderScoringInput,
    )


def test_first_advantage_binds_first_direction():
    result = _bind(
        _signal(
            advantage=CrossBorderLandedCostAdvantage.FIRST,
        )
    )

    assert (
        result.direction
        is CrossBorderScoringDirection.FIRST
    )


def test_second_advantage_binds_second_direction():
    result = _bind(
        _signal(
            advantage=CrossBorderLandedCostAdvantage.SECOND,
            first_landed_cost=Decimal("130"),
            second_landed_cost=Decimal("100"),
        )
    )

    assert (
        result.direction
        is CrossBorderScoringDirection.SECOND
    )


def test_equal_advantage_binds_equal_direction():
    result = _bind(
        _signal(
            advantage=CrossBorderLandedCostAdvantage.EQUAL,
            first_landed_cost=Decimal("100"),
            second_landed_cost=Decimal("100"),
        )
    )

    assert (
        result.direction
        is CrossBorderScoringDirection.EQUAL
    )


def test_not_comparable_signal_cannot_bind():
    signal = _signal(
        advantage=(
            CrossBorderLandedCostAdvantage.NOT_COMPARABLE
        )
    )

    readiness = evaluate_cross_border_scoring_readiness(
        signal
    )

    assert (
        readiness.state
        is CrossBorderScoringReadinessState.NOT_READY
    )

    with pytest.raises(
        ValueError,
        match="not scoring-ready",
    ):
        bind_cross_border_scoring_input(
            signal=signal,
            readiness=readiness,
        )


def test_unavailable_signal_cannot_bind():
    signal = _signal(
        state=CrossBorderLandedCostSignalState.UNAVAILABLE,
        advantage=(
            CrossBorderLandedCostAdvantage.NOT_COMPARABLE
        ),
    )

    readiness = evaluate_cross_border_scoring_readiness(
        signal
    )

    with pytest.raises(
        ValueError,
        match="not scoring-ready",
    ):
        bind_cross_border_scoring_input(
            signal=signal,
            readiness=readiness,
        )


def test_candidate_references_are_preserved():
    result = _bind()

    assert (
        result.first_candidate_ref
        == "candidate:first"
    )

    assert (
        result.second_candidate_ref
        == "candidate:second"
    )


def test_landed_cost_values_are_preserved():
    result = _bind()

    assert (
        result.first_landed_cost
        == Decimal("100")
    )

    assert (
        result.second_landed_cost
        == Decimal("120")
    )


def test_currency_is_preserved():
    result = _bind()

    assert result.currency == "USD"


def test_evidence_quality_is_preserved():
    result = _bind()

    assert result.first_evidence_quality == "known"
    assert (
        result.second_evidence_quality
        == "estimated"
    )


def test_source_contract_is_preserved():
    result = _bind()

    assert (
        result.source_schema_id
        == (
            "commerce_ai.cross_border."
            "recommendation_handoff"
        )
    )

    assert result.source_schema_version == "1.0"


def test_bound_input_is_immutable():
    result = _bind()

    with pytest.raises(
        FrozenInstanceError,
    ):
        result.currency = "KRW"


def test_direction_vocabulary_is_bounded():
    assert {
        direction.value
        for direction in CrossBorderScoringDirection
    } == {
        "first",
        "second",
        "equal",
    }


def test_bound_input_has_no_score_surface():
    result = _bind()

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

    assert forbidden.isdisjoint(public_names)


def test_bound_input_has_no_weight_surface():
    result = _bind()

    forbidden = {
        "weight",
        "landed_cost_weight",
        "price_weight",
        "quality_weight",
        "trust_weight",
    }

    public_names = {
        name.lower()
        for name in dir(result)
        if not name.startswith("_")
    }

    assert forbidden.isdisjoint(public_names)


def test_bound_input_has_no_ranking_surface():
    result = _bind()

    forbidden = {
        "rank",
        "ranking",
        "winner",
        "best_candidate",
        "selected_candidate",
        "preferred_candidate",
    }

    public_names = {
        name.lower()
        for name in dir(result)
        if not name.startswith("_")
    }

    assert forbidden.isdisjoint(public_names)


def test_bound_input_has_no_recommendation_surface():
    result = _bind()

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

    assert forbidden.isdisjoint(public_names)


def test_bound_input_has_no_transaction_surface():
    result = _bind()

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

    assert forbidden.isdisjoint(public_names)


def test_binding_does_not_mutate_signal():
    signal = _signal()

    original_advantage = signal.advantage
    original_first = signal.first_landed_cost

    _bind(signal)

    assert signal.advantage is original_advantage
    assert signal.first_landed_cost == original_first


def test_binding_does_not_mutate_readiness():
    signal = _signal()

    readiness = evaluate_cross_border_scoring_readiness(
        signal
    )

    original_state = readiness.state

    bind_cross_border_scoring_input(
        signal=signal,
        readiness=readiness,
    )

    assert readiness.state is original_state
