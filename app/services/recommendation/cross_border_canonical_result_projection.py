from __future__ import annotations

from typing import Sequence

from app.services.recommendation.models import (
    RecommendationCandidate,
    RecommendationContext,
    RecommendationResult,
)


def project_cross_border_canonical_result(
    *,
    context: RecommendationContext,
    candidates: Sequence[RecommendationCandidate],
) -> RecommendationResult:
    """
    Project already-ranked Cross-Border canonical candidates into the
    canonical RecommendationResult envelope.

    This projection does not select a winner, rerank candidates, rescore
    candidates, or reinterpret candidate rank.
    """

    canonical_candidates = tuple(candidates)

    return RecommendationResult(
        context=context,
        candidates=canonical_candidates,
        summary=(
            f"'{context.query}' 기준으로 "
            f"추천 상품 {len(canonical_candidates)}개를 구성했습니다."
        ),
        metadata={
            "provider": "CrossBorderCanonicalResultProjection",
            "candidate_count": len(canonical_candidates),
        },
    )
