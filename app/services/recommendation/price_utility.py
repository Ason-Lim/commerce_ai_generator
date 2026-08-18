from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Iterable, Mapping


@dataclass(frozen=True)
class PriceUtilityObservation:
    """
    Canonical candidate-relative price utility evidence.

    raw_price:
        Parsed positive raw price evidence.

    utility:
        Recommendation-relative desirability in [0, 100].

    available:
        Whether usable raw-price evidence exists for this candidate.
    """

    raw_price: float = 0.0
    utility: float = 0.0
    available: bool = False


def parse_usable_price(
    value: Any,
) -> float | None:
    """
    Convert raw price-like input into usable positive finite price evidence.

    Missing, invalid, zero, negative, NaN, and infinity are unavailable.
    """

    if value is None:
        return None

    if isinstance(
        value,
        str,
    ):
        value = (
            value.strip()
            .replace(",", "")
            .replace("원", "")
        )

        if not value:
            return None

    try:
        price = float(
            value
        )

    except (
        TypeError,
        ValueError,
    ):
        return None

    if (
        not math.isfinite(
            price
        )
        or price <= 0
    ):
        return None

    return price


def _price_from_candidate(
    candidate: Mapping[str, Any],
) -> float | None:
    """
    Read canonical raw-price evidence.

    This function intentionally does not apply discount/member/coupon
    semantics. Those belong to a separate approved price-evidence adapter.
    """

    return parse_usable_price(
        candidate.get(
            "price"
        )
    )


def _percentile_utility(
    price: float,
    sorted_unique_prices: tuple[float, ...],
) -> float:
    """
    Convert price rank to monotonic utility.

    Lowest unique price  -> 100
    Highest unique price -> 0
    Equal-price groups   -> same utility

    A single unique price represents a neutral comparison set -> 50.
    """

    count = len(
        sorted_unique_prices
    )

    if count == 1:
        return 50.0

    rank = sorted_unique_prices.index(
        price
    )

    percentile = (
        rank
        / (
            count - 1
        )
    )

    return round(
        (
            1.0
            - percentile
        )
        * 100.0,
        1,
    )


def calculate_price_utilities(
    candidates: Iterable[Mapping[str, Any]],
) -> tuple[PriceUtilityObservation, ...]:
    """
    Calculate deterministic candidate-set-relative price utility.

    Contract:
    - no input mutation;
    - missing prices remain unavailable;
    - observed raw-price evidence remains distinguishable from utility;
    - lower price never receives lower utility than higher price;
    - equal prices receive equal utility;
    - a single unique usable price receives neutral utility 50;
    - utilities remain within [0, 100];
    - missing candidates do not distort ranks of available prices.
    """

    items = tuple(
        candidates
    )

    parsed_prices = tuple(
        _price_from_candidate(
            item
        )
        for item in items
    )

    unique_prices = tuple(
        sorted(
            {
                price
                for price in parsed_prices
                if price is not None
            }
        )
    )

    observations: list[
        PriceUtilityObservation
    ] = []

    for price in parsed_prices:
        if price is None:
            observations.append(
                PriceUtilityObservation()
            )
            continue

        observations.append(
            PriceUtilityObservation(
                raw_price=price,
                utility=_percentile_utility(
                    price,
                    unique_prices,
                ),
                available=True,
            )
        )

    return tuple(
        observations
    )
