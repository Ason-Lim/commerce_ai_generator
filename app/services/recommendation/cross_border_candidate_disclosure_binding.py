from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from app.services.cross_border.landed_cost_estimate_disclosure import (
    LandedCostEstimateDisclosureEvidence,
)

from .cross_border_candidate_reference_binding_set import (
    CrossBorderCandidateReferenceBindingSet,
)


@dataclass(frozen=True)
class CrossBorderCandidateDisclosureBinding:
    """
    Immutable Recommendation-side association between one opaque
    Cross-Border candidate reference and already-established
    landed-cost disclosure evidence.

    candidate_position is the only join authority.

    This binding does not:

    - infer product identity from candidate_ref;
    - derive or alter landed-cost evidence;
    - convert currencies;
    - calculate payment or card fees;
    - calculate Recommendation score components;
    - rank, rerank, select, or recommend candidates;
    - render customer-facing disclosure text;
    - execute checkout or payment behavior.
    """

    candidate_ref: str
    candidate_position: int
    disclosure: LandedCostEstimateDisclosureEvidence


def bind_cross_border_candidate_disclosures(
    *,
    reference_bindings: CrossBorderCandidateReferenceBindingSet,
    disclosures: Sequence[LandedCostEstimateDisclosureEvidence],
) -> tuple[
    CrossBorderCandidateDisclosureBinding,
    CrossBorderCandidateDisclosureBinding,
]:
    """
    Bind exactly two already-established disclosure evidence objects
    to explicit Cross-Border candidate references.

    Disclosure sequence position corresponds only to canonical
    Recommendation candidate position:

        disclosures[0] -> candidate_position 1
        disclosures[1] -> candidate_position 2

    The order of reference_bindings.bindings is not used to infer
    position and is preserved in the returned tuple.

    No disclosure value is recalculated or interpreted.
    """

    if len(disclosures) != 2:
        raise ValueError(
            "exactly two disclosure evidence objects are required"
        )

    by_position = {
        1: disclosures[0],
        2: disclosures[1],
    }

    bindings = tuple(
        CrossBorderCandidateDisclosureBinding(
            candidate_ref=binding.candidate_ref,
            candidate_position=binding.candidate_position,
            disclosure=by_position[
                binding.candidate_position
            ],
        )
        for binding in reference_bindings.bindings
    )

    return (
        bindings[0],
        bindings[1],
    )
