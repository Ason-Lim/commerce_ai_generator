from __future__ import annotations

from collections.abc import Sequence

from .cross_border_candidate_component_alignment import (
    CrossBorderCandidateComponentBinding,
)
from .cross_border_original_candidate_binding_set import (
    CrossBorderCandidateReferenceBindingSet,
)
from .models import RecommendationCandidate


def bind_cross_border_candidate_components(
    *,
    reference_bindings: CrossBorderCandidateReferenceBindingSet,
    candidates: Sequence[RecommendationCandidate],
) -> tuple[
    CrossBorderCandidateComponentBinding,
    CrossBorderCandidateComponentBinding,
]:
    """
    Bind Cross-Border candidate references to the canonical base score
    components already preserved by RecommendationCandidate.

    Authority rules:

    - candidate_ref is not interpreted as product identity;
    - candidate_position is the only join authority;
    - base score components are consumed from candidate.score.components;
    - score components are not recalculated or reconstructed here.
    """
    if len(candidates) != 2:
        raise ValueError(
            "exactly two recommendation candidates are required"
        )

    by_position = {
        1: candidates[0],
        2: candidates[1],
    }

    bindings = tuple(
        CrossBorderCandidateComponentBinding(
            candidate_ref=binding.candidate_ref,
            base_components=by_position[
                binding.candidate_position
            ].score.components,
        )
        for binding in reference_bindings.bindings
    )

    return (
        bindings[0],
        bindings[1],
    )
