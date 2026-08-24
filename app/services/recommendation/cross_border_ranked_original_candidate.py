from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping, Tuple

from app.services.recommendation.cross_border_candidate_ranking import (
    CrossBorderRankableCandidate,
)
from app.services.recommendation.cross_border_original_candidate_binding_set import (
    CrossBorderOriginalCandidateBindingSet,
)
from app.services.recommendation.models import (
    RecommendationScoreComponents,
    RecommendationScoreResult,
)


@dataclass(frozen=True)
class CrossBorderRankedOriginalCandidate:
    """
    One canonical Cross-Border ranking result reconciled with the
    original canonical Recommendation candidate item.

    candidate_ref is used only to correlate two already-explicit
    Recommendation-owned Cross-Border surfaces.

    It is not interpreted as product identity.

    candidate_position remains preserved provenance from the original
    positional binding.

    rank_position describes only the order already produced by the
    canonical Recommendation ranking authority.

    This contract does not score, rescore, rerank, choose a winner,
    select a recommendation, activate production behavior, route
    traffic, or execute transactions.
    """

    candidate_ref: str
    candidate_position: int
    rank_position: int
    item: Mapping[str, Any]
    score: RecommendationScoreResult
    components: RecommendationScoreComponents
    landed_cost: float | None

    def __post_init__(self) -> None:
        candidate_ref = self.candidate_ref.strip()

        if not candidate_ref:
            raise ValueError(
                "candidate_ref must be non-empty"
            )

        if self.candidate_position not in {1, 2}:
            raise ValueError(
                "candidate_position must be 1 or 2"
            )

        if self.rank_position not in {1, 2}:
            raise ValueError(
                "rank_position must be 1 or 2"
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


@dataclass(frozen=True)
class CrossBorderRankedOriginalCandidatePair:
    """
    Pairwise reconciliation of canonical ranking output with the
    original canonical Recommendation candidate items.

    Tuple order is canonical ranking order.

    No winner or recommendation-selection semantics are introduced.
    """

    ranked: Tuple[
        CrossBorderRankedOriginalCandidate,
        CrossBorderRankedOriginalCandidate,
    ]

    def __post_init__(self) -> None:
        if len(self.ranked) != 2:
            raise ValueError(
                "exactly two ranked original candidates are required"
            )

        rank_positions = {
            candidate.rank_position
            for candidate in self.ranked
        }

        if rank_positions != {1, 2}:
            raise ValueError(
                "rank positions must be exactly {1, 2}"
            )

        candidate_refs = {
            candidate.candidate_ref
            for candidate in self.ranked
        }

        if len(candidate_refs) != 2:
            raise ValueError(
                "ranked candidate_ref values must be unique"
            )

        ordered = tuple(
            sorted(
                self.ranked,
                key=lambda candidate: candidate.rank_position,
            )
        )

        object.__setattr__(
            self,
            "ranked",
            ordered,
        )


def reconcile_cross_border_ranked_original_candidates(
    *,
    original_bindings: CrossBorderOriginalCandidateBindingSet,
    ranked_candidates: tuple[
        CrossBorderRankableCandidate,
        CrossBorderRankableCandidate,
    ],
) -> CrossBorderRankedOriginalCandidatePair:
    """
    Reconcile the already-ranked Cross-Border pair with preserved
    original Recommendation candidate items.

    The ranking tuple already represents canonical rank order.

    candidate_ref is used only as an explicit correlation key between
    the ranked Cross-Border surface and the previously established
    original-candidate binding surface.

    No product field is inspected or compared.
    """

    if len(ranked_candidates) != 2:
        raise ValueError(
            "exactly two ranked candidates are required"
        )

    originals_by_ref = {
        binding.candidate_ref: binding
        for binding in original_bindings.bindings
    }

    if len(originals_by_ref) != 2:
        raise ValueError(
            "original candidate_ref values must be unique"
        )

    ranked_refs = tuple(
        candidate.candidate_ref
        for candidate in ranked_candidates
    )

    if len(set(ranked_refs)) != 2:
        raise ValueError(
            "ranked candidate_ref values must be unique"
        )

    if set(ranked_refs) != set(originals_by_ref):
        raise ValueError(
            "ranked candidate_ref set does not match original bindings"
        )

    reconciled = tuple(
        CrossBorderRankedOriginalCandidate(
            candidate_ref=ranked_candidate.candidate_ref,
            candidate_position=(
                originals_by_ref[
                    ranked_candidate.candidate_ref
                ].candidate_position
            ),
            rank_position=rank_position,
            item=(
                originals_by_ref[
                    ranked_candidate.candidate_ref
                ].item
            ),
            score=ranked_candidate.score,
            components=ranked_candidate.components,
            landed_cost=ranked_candidate.landed_cost,
        )
        for rank_position, ranked_candidate
        in enumerate(
            ranked_candidates,
            start=1,
        )
    )

    return CrossBorderRankedOriginalCandidatePair(
        ranked=reconciled,
    )
