from __future__ import annotations

from app.services.recommendation.context import (
    build_recommendation_context,
)
from app.services.recommendation.cross_border_canonical_result_composition import (
    compose_cross_border_canonical_result,
)
from app.services.recommendation.cross_border_ranked_original_candidate import (
    CrossBorderRankedOriginalCandidate,
    CrossBorderRankedOriginalCandidatePair,
)
from app.services.recommendation.models import (
    RecommendationPriority,
    RecommendationResult,
    RecommendationScoreComponents,
    RecommendationScoreResult,
)
from app.services.recommendation.parser import (
    parse_recommendation_query,
)
from app.services.recommendation.policy import (
    resolve_recommendation_policy,
)


def _context():
    return build_recommendation_context(
        parse_recommendation_query(
            "한국 사과"
        ),
        resolve_recommendation_policy(
            "ranking"
        ),
    )


def _components(
    *,
    price: float,
) -> RecommendationScoreComponents:
    return RecommendationScoreComponents(
        quality=80.0,
        price=price,
        trust=90.0,
        popularity=70.0,
        market=75.0,
        identity=85.0,
    )


def _candidate(
    *,
    candidate_ref: str,
    candidate_position: int,
    rank_position: int,
    product_id: str,
    final_score: float,
    landed_cost: float,
) -> CrossBorderRankedOriginalCandidate:
    components = _components(
        price=(
            90.0
            if rank_position == 1
            else 70.0
        ),
    )

    score = RecommendationScoreResult(
        priority=RecommendationPriority.MIX,
        components=components,
        final_score=final_score,
    )

    return CrossBorderRankedOriginalCandidate(
        candidate_ref=candidate_ref,
        candidate_position=candidate_position,
        rank_position=rank_position,
        item={
            "product_id": product_id,
            "product_name": f"상품 {product_id}",
        },
        score=score,
        components=components,
        landed_cost=landed_cost,
    )


def _ranked_pair():
    return CrossBorderRankedOriginalCandidatePair(
        ranked=(
            _candidate(
                candidate_ref="candidate:second",
                candidate_position=2,
                rank_position=1,
                product_id="PRODUCT-B",
                final_score=95.0,
                landed_cost=80.0,
            ),
            _candidate(
                candidate_ref="candidate:first",
                candidate_position=1,
                rank_position=2,
                product_id="PRODUCT-A",
                final_score=85.0,
                landed_cost=100.0,
            ),
        )
    )


def test_composition_returns_canonical_recommendation_result():
    result = compose_cross_border_canonical_result(
        context=_context(),
        ranked_pair=_ranked_pair(),
    )

    assert isinstance(
        result,
        RecommendationResult,
    )


def test_composition_preserves_canonical_rank_order():
    result = compose_cross_border_canonical_result(
        context=_context(),
        ranked_pair=_ranked_pair(),
    )

    assert [
        candidate.rank
        for candidate in result.candidates
    ] == [1, 2]

    assert [
        candidate.item["product_id"]
        for candidate in result.candidates
    ] == [
        "PRODUCT-B",
        "PRODUCT-A",
    ]


def test_original_candidate_position_remains_provenance_not_rank():
    result = compose_cross_border_canonical_result(
        context=_context(),
        ranked_pair=_ranked_pair(),
    )

    first, second = result.candidates

    assert first.rank == 1
    assert (
        first.metadata["cross_border"][
            "candidate_position"
        ]
        == 2
    )

    assert second.rank == 2
    assert (
        second.metadata["cross_border"][
            "candidate_position"
        ]
        == 1
    )


def test_candidate_ref_remains_bounded_correlation_provenance():
    result = compose_cross_border_canonical_result(
        context=_context(),
        ranked_pair=_ranked_pair(),
    )

    assert (
        result.candidates[0]
        .metadata["cross_border"]["candidate_ref"]
        == "candidate:second"
    )

    assert (
        result.candidates[1]
        .metadata["cross_border"]["candidate_ref"]
        == "candidate:first"
    )


def test_existing_score_objects_are_reused():
    pair = _ranked_pair()

    original_scores = tuple(
        candidate.score
        for candidate in pair.ranked
    )

    result = compose_cross_border_canonical_result(
        context=_context(),
        ranked_pair=pair,
    )

    assert result.candidates[0].score is original_scores[0]
    assert result.candidates[1].score is original_scores[1]


def test_landed_cost_provenance_is_preserved():
    result = compose_cross_border_canonical_result(
        context=_context(),
        ranked_pair=_ranked_pair(),
    )

    assert (
        result.candidates[0]
        .metadata["cross_border"]["landed_cost"]
        == 80.0
    )

    assert (
        result.candidates[1]
        .metadata["cross_border"]["landed_cost"]
        == 100.0
    )


def test_result_metadata_remains_bounded_projection_metadata():
    result = compose_cross_border_canonical_result(
        context=_context(),
        ranked_pair=_ranked_pair(),
    )

    assert dict(result.metadata) == {
        "provider": "CrossBorderCanonicalResultProjection",
        "candidate_count": 2,
    }


def test_composition_creates_no_winner_or_selection_authority():
    result = compose_cross_border_canonical_result(
        context=_context(),
        ranked_pair=_ranked_pair(),
    )

    forbidden = {
        "winner",
        "winner_id",
        "selected",
        "selected_candidate",
        "selected_candidate_id",
        "best_candidate",
        "recommended_candidate",
        "selection_reason",
    }

    assert forbidden.isdisjoint(
        set(result.metadata)
    )

    assert not any(
        hasattr(result, name)
        for name in forbidden
    )


def test_composition_does_not_mutate_ranked_pair():
    pair = _ranked_pair()

    before = tuple(
        (
            candidate.candidate_ref,
            candidate.candidate_position,
            candidate.rank_position,
            dict(candidate.item),
            candidate.score,
            candidate.landed_cost,
        )
        for candidate in pair.ranked
    )

    compose_cross_border_canonical_result(
        context=_context(),
        ranked_pair=pair,
    )

    after = tuple(
        (
            candidate.candidate_ref,
            candidate.candidate_position,
            candidate.rank_position,
            dict(candidate.item),
            candidate.score,
            candidate.landed_cost,
        )
        for candidate in pair.ranked
    )

    assert after == before
