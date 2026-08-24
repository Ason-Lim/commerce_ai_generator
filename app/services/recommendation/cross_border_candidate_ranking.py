from __future__ import annotations

from dataclasses import dataclass

from app.services.recommendation.cross_border_bound_price_signal_composition import (
    BoundCrossBorderPriceSignals,
)
from app.services.recommendation.cross_border_candidate_component_alignment import (
    AlignedCrossBorderCandidateComponents,
)
from app.services.recommendation.cross_border_candidate_score_composition import (
    PairwiseCrossBorderCandidateScores,
)
from app.services.recommendation.models import (
    RecommendationPriority,
    RecommendationScoreComponents,
    RecommendationScoreResult,
)
from app.services.recommendation.ranking import (
    rank_candidates,
)


@dataclass(frozen=True)
class CrossBorderRankableCandidate:
    """
    Bounded adapter surface for canonical Recommendation ranking.

    This contract aligns an existing Cross-Border candidate reference
    with its already-derived canonical score result, canonical scoring
    components, and preserved landed-cost evidence.

    It does not calculate scores, reinterpret price evidence, define a
    new ranking policy, choose a winner, select a recommendation,
    authorize production traffic, or execute transactions.
    """

    candidate_ref: str
    score: RecommendationScoreResult
    components: RecommendationScoreComponents
    landed_cost: float | None


def rank_cross_border_candidate_pair(
    *,
    scores: PairwiseCrossBorderCandidateScores,
    price_signals: BoundCrossBorderPriceSignals,
    aligned_components: AlignedCrossBorderCandidateComponents,
    priority: RecommendationPriority,
) -> tuple[
    CrossBorderRankableCandidate,
    CrossBorderRankableCandidate,
]:
    """
    Order the already-scored Cross-Border candidate pair by delegating
    exclusively to the canonical Recommendation rank_candidates()
    authority.

    Candidate-reference alignment must agree across the score,
    component, and price-evidence surfaces.

    PRICE uses preserved landed cost as the canonical raw-price
    accessor. QUALITY and TRUST use the already-aligned canonical
    component values. All other priorities follow canonical
    final-score ordering.

    Complete ties preserve the original first/second candidate order
    through Python stable sorting in rank_candidates().
    """
    scoring_input = price_signals.scoring_input

    expected_first = scores.first_candidate_ref
    expected_second = scores.second_candidate_ref

    if expected_first != aligned_components.first_candidate_ref:
        raise ValueError(
            "first candidate_ref does not match aligned components"
        )

    if expected_second != aligned_components.second_candidate_ref:
        raise ValueError(
            "second candidate_ref does not match aligned components"
        )

    if expected_first != scoring_input.first_candidate_ref:
        raise ValueError(
            "first candidate_ref does not match bound price signals"
        )

    if expected_second != scoring_input.second_candidate_ref:
        raise ValueError(
            "second candidate_ref does not match bound price signals"
        )

    if expected_first == expected_second:
        raise ValueError(
            "candidate_ref values must be unique"
        )

    first = CrossBorderRankableCandidate(
        candidate_ref=expected_first,
        score=scores.first_score,
        components=aligned_components.first_components,
        landed_cost=price_signals.first_price.landed_cost,
    )

    second = CrossBorderRankableCandidate(
        candidate_ref=expected_second,
        score=scores.second_score,
        components=aligned_components.second_components,
        landed_cost=price_signals.second_price.landed_cost,
    )

    ranked = rank_candidates(
        [first, second],
        priority,
        final_score=lambda item: item.score.final_score,
        price=lambda item: item.landed_cost,
        quality_score=lambda item: item.components.quality,
        trust_signal=lambda item: item.components.trust,
    )

    return ranked[0], ranked[1]
