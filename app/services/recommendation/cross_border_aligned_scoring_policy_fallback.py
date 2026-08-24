from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.services.recommendation.cross_border_aligned_scoring_policy_activation_boundary import (
    AlignedCrossBorderPolicyActivationBoundary,
)
from app.services.recommendation.cross_border_scoring_policy_fallback import (
    CrossBorderScoringFallbackDecision,
    evaluate_cross_border_scoring_fallback,
)


class AlignedCrossBorderScoringFallbackState(
    str,
    Enum,
):
    AVAILABLE = "available"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class AlignedCrossBorderScoringFallback:
    state: AlignedCrossBorderScoringFallbackState
    aligned_boundary: AlignedCrossBorderPolicyActivationBoundary
    fallback: CrossBorderScoringFallbackDecision | None
    reasons: tuple[str, ...]


def evaluate_aligned_cross_border_scoring_fallback(
    aligned_boundary: AlignedCrossBorderPolicyActivationBoundary,
) -> AlignedCrossBorderScoringFallback:
    """
    Preserve aligned provenance while delegating canonical fallback
    authority to the canonical fallback evaluator.

    BLOCKED means that aligned activation-boundary evaluation did not
    produce a canonical boundary eligible for fallback evaluation.
    It must not be converted into canonical BASELINE fallback.

    AVAILABLE delegates the exact nested canonical boundary without
    reimplementing fallback authority.
    """

    boundary = aligned_boundary.boundary

    if boundary is None:
        return AlignedCrossBorderScoringFallback(
            state=AlignedCrossBorderScoringFallbackState.BLOCKED,
            aligned_boundary=aligned_boundary,
            fallback=None,
            reasons=(
                "aligned_activation_boundary_blocked",
            ),
        )

    fallback = evaluate_cross_border_scoring_fallback(
        boundary,
    )

    return AlignedCrossBorderScoringFallback(
        state=AlignedCrossBorderScoringFallbackState.AVAILABLE,
        aligned_boundary=aligned_boundary,
        fallback=fallback,
        reasons=(),
    )
