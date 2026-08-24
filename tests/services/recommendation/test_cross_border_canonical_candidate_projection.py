from __future__ import annotations

from types import MappingProxyType

from app.services.recommendation.cross_border_canonical_candidate_projection import (
    project_cross_border_ranked_candidate,
)
from app.services.recommendation.cross_border_ranked_original_candidate import (
    CrossBorderRankedOriginalCandidate,
)
from app.services.recommendation.models import (
    RecommendationCandidate,
    RecommendationScoreComponents,
    RecommendationScoreResult,
)


def _ranked_candidate() -> CrossBorderRankedOriginalCandidate:
    components = RecommendationScoreComponents(
        quality=81.0,
        price=92.0,
        trust=88.0,
        popularity=76.0,
        market=84.0,
    )

    score = RecommendationScoreResult(
        final_score=86.5,
        components=components,
        priority="value",
    )

    return CrossBorderRankedOriginalCandidate(
        candidate_ref="candidate-a",
        candidate_position=2,
        rank_position=1,
        item={
            "id": "product-a",
            "name": "Product A",
            "price": 100.0,
        },
        score=score,
        components=components,
        landed_cost=128.5,
    )


def test_projects_to_canonical_recommendation_candidate() -> None:
    ranked = _ranked_candidate()

    projected = project_cross_border_ranked_candidate(
        ranked
    )

    assert isinstance(
        projected,
        RecommendationCandidate,
    )


def test_preserves_ranked_item_value() -> None:
    ranked = _ranked_candidate()

    projected = project_cross_border_ranked_candidate(
        ranked
    )

    assert dict(projected.item) == dict(ranked.item)


def test_reuses_existing_score_object() -> None:
    ranked = _ranked_candidate()

    projected = project_cross_border_ranked_candidate(
        ranked
    )

    assert projected.score is ranked.score


def test_maps_canonical_rank_position_directly() -> None:
    ranked = _ranked_candidate()

    projected = project_cross_border_ranked_candidate(
        ranked
    )

    assert projected.rank == ranked.rank_position


def test_preserves_cross_border_provenance_in_metadata() -> None:
    ranked = _ranked_candidate()

    projected = project_cross_border_ranked_candidate(
        ranked
    )

    assert projected.metadata["cross_border"] == {
        "candidate_ref": ranked.candidate_ref,
        "candidate_position": ranked.candidate_position,
        "landed_cost": ranked.landed_cost,
    }


def test_does_not_duplicate_rank_position_in_metadata() -> None:
    ranked = _ranked_candidate()

    projected = project_cross_border_ranked_candidate(
        ranked
    )

    assert "rank_position" not in projected.metadata
    assert (
        "rank_position"
        not in projected.metadata["cross_border"]
    )


def test_canonical_candidate_outer_surfaces_are_immutable() -> None:
    ranked = _ranked_candidate()

    projected = project_cross_border_ranked_candidate(
        ranked
    )

    assert isinstance(
        projected.item,
        MappingProxyType,
    )
    assert isinstance(
        projected.metadata,
        MappingProxyType,
    )


def test_projection_does_not_mutate_source_candidate() -> None:
    ranked = _ranked_candidate()

    original_item = dict(ranked.item)
    original_score = ranked.score
    original_rank = ranked.rank_position

    project_cross_border_ranked_candidate(
        ranked
    )

    assert dict(ranked.item) == original_item
    assert ranked.score is original_score
    assert ranked.rank_position == original_rank
