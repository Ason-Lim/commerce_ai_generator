from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence, Tuple

from app.services.recommendation.cross_border_candidate_reference_binding_set import (
    CrossBorderCandidateReferenceBindingSet,
)
from app.services.recommendation.cross_border_original_candidate_binding import (
    CrossBorderOriginalCandidateBinding,
    bind_cross_border_original_candidate,
)
from app.services.recommendation.models import (
    RecommendationCandidate,
)


@dataclass(frozen=True)
class CrossBorderOriginalCandidateBindingSet:
    """
    Recommendation-owned pairwise preservation of the original
    canonical Recommendation candidate items under the already
    explicit Cross-Border positional reference bindings.

    The join authority is candidate_position only.

    candidate_ref remains opaque and is never compared with or
    inferred from product identity.

    This contract is deliberately pairwise and fail-closed.
    """

    bindings: Tuple[
        CrossBorderOriginalCandidateBinding,
        CrossBorderOriginalCandidateBinding,
    ]

    def __post_init__(self) -> None:
        if len(self.bindings) != 2:
            raise ValueError(
                "exactly two original candidate bindings are required"
            )

        positions = {
            binding.candidate_position
            for binding in self.bindings
        }

        if positions != {1, 2}:
            raise ValueError(
                "original candidate binding positions must be exactly {1, 2}"
            )

        ordered = tuple(
            sorted(
                self.bindings,
                key=lambda binding: binding.candidate_position,
            )
        )

        object.__setattr__(
            self,
            "bindings",
            ordered,
        )


def bind_cross_border_original_candidate_set(
    *,
    reference_binding_set: CrossBorderCandidateReferenceBindingSet,
    candidates: Sequence[RecommendationCandidate],
) -> CrossBorderOriginalCandidateBindingSet:
    """
    Join exactly two canonical Recommendation candidates to the
    explicit Cross-Border reference positions 1 and 2.

    Sequence order is interpreted positionally:

        candidates[0] -> candidate_position 1
        candidates[1] -> candidate_position 2

    No product identity matching is performed.
    """

    if len(candidates) != 2:
        raise ValueError(
            "exactly two recommendation candidates are required"
        )

    references_by_position = {
        binding.candidate_position: binding
        for binding in reference_binding_set.bindings
    }

    if set(references_by_position) != {1, 2}:
        raise ValueError(
            "reference binding positions must be exactly {1, 2}"
        )

    bindings = tuple(
        bind_cross_border_original_candidate(
            reference_binding=references_by_position[position],
            candidate=candidates[position - 1],
        )
        for position in (1, 2)
    )

    return CrossBorderOriginalCandidateBindingSet(
        bindings=bindings,
    )
