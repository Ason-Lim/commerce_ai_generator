from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from app.services.recommendation.cross_border_candidate_ranking import (
    CrossBorderRankableCandidate,
)
from app.services.recommendation.cross_border_original_candidate_binding import (
    CrossBorderOriginalCandidateBinding,
)
from app.services.recommendation.cross_border_original_candidate_binding_set import (
    CrossBorderOriginalCandidateBindingSet,
)
from app.services.recommendation.cross_border_ranked_original_candidate import (
    CrossBorderRankedOriginalCandidate,
    CrossBorderRankedOriginalCandidatePair,
    reconcile_cross_border_ranked_original_candidates,
)
from app.services.recommendation.models import (
    RecommendationPriority,
    RecommendationScoreComponents,
    RecommendationScoreResult,
)


def _components():
    return RecommendationScoreComponents(
        quality=80.0,
        price=70.0,
        trust=90.0,
        popularity=60.0,
        market=50.0,
        identity=85.0,
    )


def _rankable(
    candidate_ref: str,
    *,
    final_score: float,
    landed_cost: float,
):
    components = _components()

    return CrossBorderRankableCandidate(
        candidate_ref=candidate_ref,
        score=RecommendationScoreResult(
            final_score=final_score,
            priority=RecommendationPriority.MIX,
            components=components,
        ),
        components=components,
        landed_cost=landed_cost,
    )


def _originals():
    return CrossBorderOriginalCandidateBindingSet(
        bindings=(
            CrossBorderOriginalCandidateBinding(
                candidate_ref="candidate:first",
                candidate_position=1,
                item={
                    "product_id": "PRODUCT-A",
                    "product_name": "상품 A",
                },
            ),
            CrossBorderOriginalCandidateBinding(
                candidate_ref="candidate:second",
                candidate_position=2,
                item={
                    "product_id": "PRODUCT-B",
                    "product_name": "상품 B",
                },
            ),
        )
    )


def test_ranked_order_is_preserved_while_original_item_is_reconciled():
    result = reconcile_cross_border_ranked_original_candidates(
        original_bindings=_originals(),
        ranked_candidates=(
            _rankable(
                "candidate:second",
                final_score=95.0,
                landed_cost=80.0,
            ),
            _rankable(
                "candidate:first",
                final_score=85.0,
                landed_cost=100.0,
            ),
        ),
    )

    first, second = result.ranked

    assert first.rank_position == 1
    assert first.candidate_ref == "candidate:second"
    assert first.candidate_position == 2
    assert first.item["product_id"] == "PRODUCT-B"

    assert second.rank_position == 2
    assert second.candidate_ref == "candidate:first"
    assert second.candidate_position == 1
    assert second.item["product_id"] == "PRODUCT-A"


def test_reconciliation_does_not_treat_rank_position_as_candidate_position():
    result = reconcile_cross_border_ranked_original_candidates(
        original_bindings=_originals(),
        ranked_candidates=(
            _rankable(
                "candidate:second",
                final_score=95.0,
                landed_cost=80.0,
            ),
            _rankable(
                "candidate:first",
                final_score=85.0,
                landed_cost=100.0,
            ),
        ),
    )

    assert result.ranked[0].rank_position == 1
    assert result.ranked[0].candidate_position == 2

    assert result.ranked[1].rank_position == 2
    assert result.ranked[1].candidate_position == 1


def test_candidate_ref_is_correlation_only_not_product_identity():
    result = reconcile_cross_border_ranked_original_candidates(
        original_bindings=_originals(),
        ranked_candidates=(
            _rankable(
                "candidate:first",
                final_score=90.0,
                landed_cost=90.0,
            ),
            _rankable(
                "candidate:second",
                final_score=80.0,
                landed_cost=110.0,
            ),
        ),
    )

    assert result.ranked[0].candidate_ref == "candidate:first"
    assert result.ranked[0].item["product_id"] == "PRODUCT-A"

    assert result.ranked[1].candidate_ref == "candidate:second"
    assert result.ranked[1].item["product_id"] == "PRODUCT-B"


def test_mismatched_reference_set_fails_closed():
    with pytest.raises(
        ValueError,
        match=(
            "ranked candidate_ref set does not match "
            "original bindings"
        ),
    ):
        reconcile_cross_border_ranked_original_candidates(
            original_bindings=_originals(),
            ranked_candidates=(
                _rankable(
                    "candidate:first",
                    final_score=90.0,
                    landed_cost=90.0,
                ),
                _rankable(
                    "candidate:unknown",
                    final_score=80.0,
                    landed_cost=110.0,
                ),
            ),
        )


def test_duplicate_ranked_reference_fails_closed():
    with pytest.raises(
        ValueError,
        match="ranked candidate_ref values must be unique",
    ):
        reconcile_cross_border_ranked_original_candidates(
            original_bindings=_originals(),
            ranked_candidates=(
                _rankable(
                    "candidate:first",
                    final_score=90.0,
                    landed_cost=90.0,
                ),
                _rankable(
                    "candidate:first",
                    final_score=80.0,
                    landed_cost=110.0,
                ),
            ),
        )


def test_reconciled_candidate_is_immutable():
    result = reconcile_cross_border_ranked_original_candidates(
        original_bindings=_originals(),
        ranked_candidates=(
            _rankable(
                "candidate:first",
                final_score=90.0,
                landed_cost=90.0,
            ),
            _rankable(
                "candidate:second",
                final_score=80.0,
                landed_cost=110.0,
            ),
        ),
    )

    with pytest.raises(FrozenInstanceError):
        result.ranked[0].candidate_ref = "changed"

    with pytest.raises(TypeError):
        result.ranked[0].item["product_id"] = "changed"


def test_pair_orders_by_explicit_rank_position():
    first = CrossBorderRankedOriginalCandidate(
        candidate_ref="candidate:first",
        candidate_position=1,
        rank_position=1,
        item={"product_id": "A"},
        score=_rankable(
            "candidate:first",
            final_score=90.0,
            landed_cost=90.0,
        ).score,
        components=_components(),
        landed_cost=90.0,
    )

    second = CrossBorderRankedOriginalCandidate(
        candidate_ref="candidate:second",
        candidate_position=2,
        rank_position=2,
        item={"product_id": "B"},
        score=_rankable(
            "candidate:second",
            final_score=80.0,
            landed_cost=110.0,
        ).score,
        components=_components(),
        landed_cost=110.0,
    )

    result = CrossBorderRankedOriginalCandidatePair(
        ranked=(
            second,
            first,
        )
    )

    assert tuple(
        item.rank_position
        for item in result.ranked
    ) == (1, 2)


def test_no_winner_selection_or_activation_surface():
    result = reconcile_cross_border_ranked_original_candidates(
        original_bindings=_originals(),
        ranked_candidates=(
            _rankable(
                "candidate:first",
                final_score=90.0,
                landed_cost=90.0,
            ),
            _rankable(
                "candidate:second",
                final_score=80.0,
                landed_cost=110.0,
            ),
        ),
    )

    forbidden = {
        "winner",
        "selected",
        "selected_candidate",
        "best_candidate",
        "recommendation",
        "production_enabled",
        "rollout_started",
        "route_traffic",
        "checkout",
        "payment",
        "purchase",
        "dispatch",
    }

    public_names = {
        name.lower()
        for name in dir(result)
        if not name.startswith("_")
    }

    assert forbidden.isdisjoint(public_names)
