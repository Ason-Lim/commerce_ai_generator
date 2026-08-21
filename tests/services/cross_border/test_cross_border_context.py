from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from app.services.cross_border.context import (
    CrossBorderEvaluationContext,
)


def test_context_preserves_origin_and_destination() -> None:
    context = CrossBorderEvaluationContext(
        origin_country="KR",
        destination_country="US",
    )

    assert context.origin_country == "KR"
    assert context.destination_country == "US"


def test_context_normalizes_outer_whitespace() -> None:
    context = CrossBorderEvaluationContext(
        origin_country=" KR ",
        destination_country=" US ",
        market=" Amazon US ",
        currency=" usd ",
        evaluated_at=" 2026-08-21T22:50:00+09:00 ",
    )

    assert context.origin_country == "KR"
    assert context.destination_country == "US"
    assert context.market == "Amazon US"
    assert context.currency == "USD"
    assert (
        context.evaluated_at
        == "2026-08-21T22:50:00+09:00"
    )


@pytest.mark.parametrize(
    "field_name",
    [
        "origin_country",
        "destination_country",
    ],
)
def test_required_context_fields_reject_empty_values(
    field_name: str,
) -> None:
    values = {
        "origin_country": "KR",
        "destination_country": "US",
    }

    values[field_name] = "   "

    with pytest.raises(ValueError):
        CrossBorderEvaluationContext(
            **values,
        )


@pytest.mark.parametrize(
    "field_name",
    [
        "market",
        "currency",
        "evaluated_at",
    ],
)
def test_optional_context_fields_reject_blank_when_present(
    field_name: str,
) -> None:
    values = {
        "origin_country": "KR",
        "destination_country": "US",
        field_name: "   ",
    }

    with pytest.raises(ValueError):
        CrossBorderEvaluationContext(
            **values,
        )


def test_context_is_immutable() -> None:
    context = CrossBorderEvaluationContext(
        origin_country="KR",
        destination_country="US",
    )

    with pytest.raises(FrozenInstanceError):
        context.destination_country = "JP"


def test_destination_contexts_remain_distinct() -> None:
    us_context = CrossBorderEvaluationContext(
        origin_country="KR",
        destination_country="US",
        currency="USD",
    )

    jp_context = CrossBorderEvaluationContext(
        origin_country="KR",
        destination_country="JP",
        currency="JPY",
    )

    assert us_context != jp_context
    assert (
        us_context.destination_country
        != jp_context.destination_country
    )


def test_context_does_not_require_market_or_currency() -> None:
    context = CrossBorderEvaluationContext(
        origin_country="KR",
        destination_country="US",
    )

    assert context.market is None
    assert context.currency is None
    assert context.evaluated_at is None
