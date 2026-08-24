from __future__ import annotations

from dataclasses import dataclass

from app.services.recommendation.cross_border_price_signal_adapter import (
    CrossBorderPriceSignal,
    adapt_pairwise_landed_cost_to_price_signals,
)
from app.services.recommendation.cross_border_scoring_binding import (
    BoundCrossBorderScoringInput,
)


@dataclass(frozen=True)
class BoundCrossBorderPriceSignals:
    """
    Price-semantic composition derived from an already-bound
    Cross-Border scoring input.

    Candidate identity and source provenance remain owned by the
    supplied BoundCrossBorderScoringInput.

    first_price and second_price preserve positional alignment with
    first_candidate_ref and second_candidate_ref respectively.

    This contract does not:

    - recalculate landed cost;
    - reinterpret scoring readiness;
    - redefine candidate identity;
    - calculate RecommendationScoreComponents;
    - execute candidate scoring;
    - calculate final recommendation scores;
    - rank or select candidates;
    - authorize production activation;
    - route traffic;
    - execute transactions.
    """

    scoring_input: BoundCrossBorderScoringInput
    first_price: CrossBorderPriceSignal
    second_price: CrossBorderPriceSignal


def compose_bound_cross_border_price_signals(
    scoring_input: BoundCrossBorderScoringInput,
) -> BoundCrossBorderPriceSignals:
    """
    Adapt the exact pairwise landed-cost evidence preserved by the
    bound Cross-Border scoring input into canonical price-utility
    signals.

    Positional candidate alignment is preserved unchanged:

    first_candidate_ref
        <-> first_landed_cost
        <-> first_price

    second_candidate_ref
        <-> second_landed_cost
        <-> second_price
    """

    first_price, second_price = (
        adapt_pairwise_landed_cost_to_price_signals(
            scoring_input.first_landed_cost,
            scoring_input.second_landed_cost,
        )
    )

    return BoundCrossBorderPriceSignals(
        scoring_input=scoring_input,
        first_price=first_price,
        second_price=second_price,
    )
