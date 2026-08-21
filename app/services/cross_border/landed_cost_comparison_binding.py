from __future__ import annotations

from dataclasses import dataclass

from app.services.cross_border.landed_cost_candidate_comparison import (
    LandedCostCandidateComparison,
    LandedCostCandidateComparisonState,
    LandedCostCandidateRelation,
)


@dataclass(frozen=True)
class LandedCostCandidateRef:
    """
    Bounded external reference to one comparison candidate.

    This reference does not own canonical product identity,
    marketplace identity, shipping-route identity, or offer identity.
    """

    candidate_ref: str

    def __post_init__(self) -> None:
        normalized = self.candidate_ref.strip()

        if not normalized:
            raise ValueError(
                "candidate_ref must be non-empty"
            )

        object.__setattr__(
            self,
            "candidate_ref",
            normalized,
        )


@dataclass(frozen=True)
class BoundLandedCostComparison:
    """
    Immutable binding of a pairwise landed-cost comparison to
    two explicit candidate references.

    The binding preserves comparison semantics only.

    It does not:
    - rank candidates;
    - recommend a candidate;
    - select a route;
    - infer product equivalence;
    - execute a transaction.
    """

    first_candidate: LandedCostCandidateRef
    second_candidate: LandedCostCandidateRef

    comparison: LandedCostCandidateComparison

    @property
    def relation(
        self,
    ) -> LandedCostCandidateRelation | None:
        return self.comparison.relation

    @property
    def is_compared(self) -> bool:
        return (
            self.comparison.state
            is LandedCostCandidateComparisonState.COMPARED
        )


def bind_landed_cost_comparison_candidates(
    *,
    first_candidate_ref: str,
    second_candidate_ref: str,
    comparison: LandedCostCandidateComparison,
) -> BoundLandedCostComparison:
    """
    Bind a Phase 9G pairwise landed-cost comparison to explicit
    candidate references.

    Candidate order is preserved exactly:

    first_candidate_ref
        corresponds to comparison.first_total

    second_candidate_ref
        corresponds to comparison.second_total

    No ranking or recommendation authority is introduced.
    """

    first_candidate = LandedCostCandidateRef(
        candidate_ref=first_candidate_ref,
    )

    second_candidate = LandedCostCandidateRef(
        candidate_ref=second_candidate_ref,
    )

    if (
        first_candidate.candidate_ref
        == second_candidate.candidate_ref
    ):
        raise ValueError(
            "first and second candidate references "
            "must be distinct"
        )

    return BoundLandedCostComparison(
        first_candidate=first_candidate,
        second_candidate=second_candidate,
        comparison=comparison,
    )
