from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.services.recommendation.cross_border_aligned_scoring_readiness import (
    AlignedCrossBorderScoringReadiness,
    AlignedCrossBorderScoringReadinessState,
)
from app.services.recommendation.cross_border_scoring_binding import (
    BoundCrossBorderScoringInput,
    bind_cross_border_scoring_input,
)
from app.services.recommendation.cross_border_scoring_readiness import (
    CrossBorderScoringReadinessState,
)


class AlignedCrossBorderScoringBindingState(
    str,
    Enum,
):
    AVAILABLE = "available"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class AlignedCrossBorderScoringBinding:
    """
    Recommendation-side enforcement result for the scoring-binding
    boundary after aligned scoring readiness.

    AVAILABLE means C4N authorized downstream consumption and the
    nested scoring readiness was READY, allowing delegation to the
    existing scoring-binding authority.

    BLOCKED means either:

    - C4N prohibited downstream consumption; or
    - C4N was available but its nested scoring readiness was
      NOT_READY.

    In either blocked case no BoundCrossBorderScoringInput is built.

    This contract does not:

    - reevaluate candidate alignment;
    - reevaluate structural evidence readiness;
    - rebuild or reinterpret the landed-cost signal;
    - duplicate scoring-readiness rules;
    - duplicate scoring-binding rules;
    - calculate or modify scores;
    - define scoring weights;
    - execute scoring policy;
    - rank or recommend candidates;
    - select routes or execute transactions.
    """

    state: AlignedCrossBorderScoringBindingState
    aligned_readiness: AlignedCrossBorderScoringReadiness
    scoring_input: BoundCrossBorderScoringInput | None
    reasons: tuple[str, ...]

    @property
    def is_available(self) -> bool:
        return (
            self.state
            is AlignedCrossBorderScoringBindingState.AVAILABLE
        )


def bind_aligned_cross_border_scoring_input(
    aligned_readiness: AlignedCrossBorderScoringReadiness,
) -> AlignedCrossBorderScoringBinding:
    """
    Enforce C4N authorization before entering the existing
    scoring-binding boundary.

    BLOCKED C4N results never invoke
    bind_cross_border_scoring_input().

    AVAILABLE C4N results with nested NOT_READY readiness also never
    invoke the binding authority.

    Only AVAILABLE + nested READY delegates the exact nested signal
    and exact nested readiness preserved by the aligned chain.
    """

    if (
        aligned_readiness.state
        is not AlignedCrossBorderScoringReadinessState.AVAILABLE
    ):
        return AlignedCrossBorderScoringBinding(
            state=AlignedCrossBorderScoringBindingState.BLOCKED,
            aligned_readiness=aligned_readiness,
            scoring_input=None,
            reasons=(
                "cross_border_scoring_readiness_not_available",
            ),
        )

    if aligned_readiness.readiness is None:
        raise ValueError(
            "available aligned scoring readiness must contain readiness"
        )

    aligned_signal = aligned_readiness.aligned_signal

    if aligned_signal.signal is None:
        raise ValueError(
            "available aligned scoring readiness must contain signal"
        )

    if (
        aligned_readiness.readiness.state
        is not CrossBorderScoringReadinessState.READY
    ):
        return AlignedCrossBorderScoringBinding(
            state=AlignedCrossBorderScoringBindingState.BLOCKED,
            aligned_readiness=aligned_readiness,
            scoring_input=None,
            reasons=(
                "cross_border_scoring_not_ready",
            ),
        )

    scoring_input = bind_cross_border_scoring_input(
        signal=aligned_signal.signal,
        readiness=aligned_readiness.readiness,
    )

    return AlignedCrossBorderScoringBinding(
        state=AlignedCrossBorderScoringBindingState.AVAILABLE,
        aligned_readiness=aligned_readiness,
        scoring_input=scoring_input,
        reasons=(),
    )
