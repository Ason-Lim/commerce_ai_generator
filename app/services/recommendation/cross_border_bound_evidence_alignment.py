from __future__ import annotations

from dataclasses import dataclass

from app.services.cross_border.landed_cost_comparison_binding import (
    BoundLandedCostComparison,
)
from app.services.recommendation.cross_border_candidate_reference_binding import (
    CrossBorderCandidateReferenceBinding,
)
from app.services.recommendation.cross_border_candidate_reference_binding_set import (
    CrossBorderCandidateReferenceBindingSet,
)


@dataclass(frozen=True)
class CrossBorderBoundEvidenceAlignment:
    """
    Read-only semantic alignment between Recommendation candidate
    positions and an existing Cross-Border bound landed-cost
    comparison.

    Recommendation candidate position 1 must correspond exactly to
    the Cross-Border first candidate.

    Recommendation candidate position 2 must correspond exactly to
    the Cross-Border second candidate.

    This contract validates already-explicit candidate references
    only. It does not:

    - infer candidate or product identity;
    - reorder candidates by tuple order or landed cost;
    - calculate or recalculate landed cost;
    - reinterpret comparison relation;
    - score or rank candidates;
    - recommend or select a candidate;
    - select a shipping route;
    - execute a transaction.
    """

    position_one_binding: CrossBorderCandidateReferenceBinding
    position_two_binding: CrossBorderCandidateReferenceBinding
    bound_comparison: BoundLandedCostComparison

    @property
    def first_candidate_ref(self) -> str:
        return self.position_one_binding.candidate_ref

    @property
    def second_candidate_ref(self) -> str:
        return self.position_two_binding.candidate_ref


def align_cross_border_bound_evidence(
    *,
    binding_set: CrossBorderCandidateReferenceBindingSet,
    bound_comparison: BoundLandedCostComparison,
) -> CrossBorderBoundEvidenceAlignment:
    """
    Validate exact positional reference alignment between the
    Recommendation binding set and Cross-Border bound comparison.

    Binding tuple order is intentionally ignored. Explicit
    candidate_position is authoritative on the Recommendation side.

    No candidate reference is synthesized, inferred, reordered,
    canonicalized, or matched through product identity.
    """

    bindings_by_position = {
        binding.candidate_position: binding
        for binding in binding_set.bindings
    }

    position_one = bindings_by_position[1]
    position_two = bindings_by_position[2]

    first_candidate_ref = (
        bound_comparison.first_candidate.candidate_ref
    )
    second_candidate_ref = (
        bound_comparison.second_candidate.candidate_ref
    )

    if position_one.candidate_ref != first_candidate_ref:
        raise ValueError(
            "candidate position 1 must match "
            "bound comparison first candidate"
        )

    if position_two.candidate_ref != second_candidate_ref:
        raise ValueError(
            "candidate position 2 must match "
            "bound comparison second candidate"
        )

    return CrossBorderBoundEvidenceAlignment(
        position_one_binding=position_one,
        position_two_binding=position_two,
        bound_comparison=bound_comparison,
    )
