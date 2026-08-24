from __future__ import annotations

from dataclasses import dataclass

from app.services.recommendation.price_utility import (
    calculate_price_utilities,
)


@dataclass(frozen=True)
class CrossBorderPriceSignal:
    """
    Canonical price-utility signal derived from aligned
    Cross-Border landed-cost evidence.

    landed_cost preserves the Cross-Border monetary evidence.

    utility is recommendation-relative price desirability in
    the canonical [0, 100] range.

    available distinguishes unavailable evidence from an
    observed canonical utility of 0.
    """

    landed_cost: float | None
    utility: float
    available: bool


def adapt_pairwise_landed_cost_to_price_signals(
    first_landed_cost: object,
    second_landed_cost: object,
) -> tuple[
    CrossBorderPriceSignal,
    CrossBorderPriceSignal,
]:
    """
    Adapt pairwise landed-cost evidence to canonical price utility.

    This adapter owns no independent normalization algorithm.
    It delegates relative price semantics to the existing
    canonical calculate_price_utilities() contract.

    It does not:

    - mutate product raw-price evidence;
    - calculate final recommendation scores;
    - rank or select candidates;
    - authorize candidate scoring;
    - route production traffic;
    - execute transactions.
    """

    observations = calculate_price_utilities(
        [
            {
                "price": first_landed_cost,
            },
            {
                "price": second_landed_cost,
            },
        ]
    )

    return tuple(
        CrossBorderPriceSignal(
            landed_cost=(
                observation.raw_price
                if observation.available
                else None
            ),
            utility=observation.utility,
            available=observation.available,
        )
        for observation in observations
    )
