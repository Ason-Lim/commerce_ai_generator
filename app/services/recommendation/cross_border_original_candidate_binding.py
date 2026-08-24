from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping

from app.services.recommendation.cross_border_candidate_reference_binding import (
    CrossBorderCandidateReferenceBinding,
)
from app.services.recommendation.models import (
    RecommendationCandidate,
)


@dataclass(frozen=True)
class CrossBorderOriginalCandidateBinding:
    """
    Recommendation-owned binding between one already-explicit
    Cross-Border candidate reference/position and the original
    canonical Recommendation candidate item at that position.

    candidate_ref remains an opaque Cross-Border handoff reference.
    It is not interpreted as product identity.

    candidate_position is the only join authority used by the
    composition helper below.

    This contract does not:

    - infer identity from product_id or candidate_ref;
    - compare candidate_ref with product fields;
    - score or rescore candidates;
    - rank or select candidates;
    - calculate landed cost;
    - activate policy behavior;
    - route production traffic;
    - execute transactions.
    """

    candidate_ref: str
    candidate_position: int
    item: Mapping[str, Any]

    def __post_init__(self) -> None:
        candidate_ref = self.candidate_ref.strip()

        if not candidate_ref:
            raise ValueError(
                "candidate_ref must be non-empty"
            )

        if self.candidate_position <= 0:
            raise ValueError(
                "candidate_position must be greater than zero"
            )

        object.__setattr__(
            self,
            "candidate_ref",
            candidate_ref,
        )
        object.__setattr__(
            self,
            "item",
            MappingProxyType(
                dict(self.item)
            ),
        )


def bind_cross_border_original_candidate(
    *,
    reference_binding: CrossBorderCandidateReferenceBinding,
    candidate: RecommendationCandidate,
) -> CrossBorderOriginalCandidateBinding:
    """
    Preserve the original canonical candidate item under one
    already-explicit Cross-Border positional reference binding.

    The caller supplies the Recommendation candidate corresponding
    to reference_binding.candidate_position.

    No product-identity matching or inference is performed here.
    """

    return CrossBorderOriginalCandidateBinding(
        candidate_ref=reference_binding.candidate_ref,
        candidate_position=reference_binding.candidate_position,
        item=candidate.item,
    )
