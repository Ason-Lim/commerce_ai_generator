from __future__ import annotations

from dataclasses import asdict
from typing import Any

from app.services.recommendation.cross_border_candidate_disclosure_binding import (
    CrossBorderCandidateDisclosureBinding,
)
from app.services.recommendation.models import (
    RecommendationCandidate,
)


def project_cross_border_candidate_disclosure(
    *,
    candidate: RecommendationCandidate,
    binding: CrossBorderCandidateDisclosureBinding,
) -> RecommendationCandidate:
    """
    Attach already-established Cross-Border disclosure evidence to one
    canonical RecommendationCandidate.

    candidate_position and candidate_ref must match the existing
    candidate Cross-Border metadata.

    This projection:

    - preserves item, score, and rank unchanged;
    - preserves existing candidate metadata;
    - serializes already-established disclosure evidence only;
    - does not calculate FX conversion;
    - does not calculate card/payment fees;
    - does not score, rerank, or select candidates;
    - does not render customer-facing text.
    """

    existing_metadata = dict(candidate.metadata)

    cross_border = dict(
        existing_metadata.get("cross_border", {})
    )

    existing_ref = cross_border.get("candidate_ref")
    existing_position = cross_border.get("candidate_position")

    if existing_ref != binding.candidate_ref:
        raise ValueError(
            "candidate_ref does not match disclosure binding"
        )

    if existing_position != binding.candidate_position:
        raise ValueError(
            "candidate_position does not match disclosure binding"
        )

    disclosure: dict[str, Any] = asdict(
        binding.disclosure
    )

    cross_border["estimate_disclosure"] = disclosure
    existing_metadata["cross_border"] = cross_border

    return RecommendationCandidate(
        item=candidate.item,
        score=candidate.score,
        rank=candidate.rank,
        metadata=existing_metadata,
    )
