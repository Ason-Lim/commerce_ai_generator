from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.services.recommendation.cross_border_bound_evidence_alignment import (
    CrossBorderBoundEvidenceAlignment,
)
from app.services.recommendation.cross_border_evidence import (
    CanonicalCrossBorderRecommendationEvidence,
)


class AlignedCrossBorderConsumptionState(
    str,
    Enum,
):
    ALIGNED = "aligned"
    REJECTED = "rejected"


@dataclass(frozen=True)
class AlignedCrossBorderConsumptionGate:
    """
    Recommendation-side fail-closed gate for canonical Cross-Border
    evidence consumption.

    ALIGNED means only that the canonical evidence candidate
    references correspond exactly to the already-validated
    Recommendation position 1/2 bindings and Cross-Border
    first/second candidate references.

    This gate does not:

    - infer candidate or product identity;
    - reorder candidates;
    - recalculate landed cost;
    - validate or reinterpret relation, totals, currency, context,
      quality, or schema semantics;
    - calculate a score;
    - modify ranking;
    - select or recommend a candidate;
    - select a shipping route;
    - execute a transaction.
    """

    state: AlignedCrossBorderConsumptionState
    evidence: CanonicalCrossBorderRecommendationEvidence
    alignment: CrossBorderBoundEvidenceAlignment
    reasons: tuple[str, ...]

    @property
    def is_aligned(self) -> bool:
        return (
            self.state
            is AlignedCrossBorderConsumptionState.ALIGNED
        )


def gate_aligned_cross_border_consumption(
    *,
    evidence: CanonicalCrossBorderRecommendationEvidence,
    alignment: CrossBorderBoundEvidenceAlignment,
) -> AlignedCrossBorderConsumptionGate:
    """
    Verify that canonical Recommendation evidence refers to the same
    explicitly aligned first/second candidates established by C4E.

    C4E remains authoritative for Recommendation-position to
    Cross-Border-bound-candidate alignment.

    This gate adds only the missing canonical-evidence-to-C4E
    correspondence check.
    """

    reasons: list[str] = []

    if (
        evidence.first_candidate_ref
        != alignment.position_one_binding.candidate_ref
    ):
        reasons.append("first_candidate_ref")

    if (
        evidence.second_candidate_ref
        != alignment.position_two_binding.candidate_ref
    ):
        reasons.append("second_candidate_ref")

    # Defensive confirmation of the already-established C4E
    # positional references. No identity inference is performed.
    if (
        evidence.first_candidate_ref
        != alignment.bound_comparison.first_candidate.candidate_ref
    ):
        if "first_candidate_ref" not in reasons:
            reasons.append("first_candidate_ref")

    if (
        evidence.second_candidate_ref
        != alignment.bound_comparison.second_candidate.candidate_ref
    ):
        if "second_candidate_ref" not in reasons:
            reasons.append("second_candidate_ref")

    state = (
        AlignedCrossBorderConsumptionState.ALIGNED
        if not reasons
        else AlignedCrossBorderConsumptionState.REJECTED
    )

    return AlignedCrossBorderConsumptionGate(
        state=state,
        evidence=evidence,
        alignment=alignment,
        reasons=tuple(reasons),
    )
