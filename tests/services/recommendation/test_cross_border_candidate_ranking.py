from dataclasses import FrozenInstanceError
from decimal import Decimal

import pytest

from app.services.recommendation.cross_border_bound_price_signal_composition import (
    compose_bound_cross_border_price_signals,
)
from app.services.recommendation.cross_border_candidate_component_alignment import (
    CrossBorderCandidateComponentBinding,
    align_cross_border_candidate_components,
)
from app.services.recommendation.cross_border_candidate_ranking import (
    CrossBorderRankableCandidate,
    rank_cross_border_candidate_pair,
)
from app.services.recommendation.cross_border_candidate_score_composition import (
    compose_cross_border_candidate_scores,
)
from app.services.recommendation.cross_border_scoring_binding import (
    BoundCrossBorderScoringInput,
    CrossBorderScoringDirection,
)
from app.services.recommendation.models import (
    RecommendationPriority,
    RecommendationScoreComponents,
)


def _base(*, quality, trust):
    return RecommendationScoreComponents(
        quality=quality,
        price=0.0,
        trust=trust,
        popularity=60.0,
        market=50.0,
        identity=80.0,
        available=frozenset(
            {
                "quality",
                "price",
                "trust",
                "popularity",
                "market",
                "identity",
            }
        ),
    )


def _surfaces(
    *,
    first_cost=Decimal("80"),
    second_cost=Decimal("100"),
    first_quality=90.0,
    second_quality=85.0,
    first_trust=80.0,
    second_trust=75.0,
    score_priority=RecommendationPriority.MIX,
):
    scoring_input = BoundCrossBorderScoringInput(
        first_candidate_ref="candidate:first",
        second_candidate_ref="candidate:second",
        first_landed_cost=first_cost,
        second_landed_cost=second_cost,
        currency="USD",
        direction=CrossBorderScoringDirection.FIRST,
        first_evidence_quality="verified",
        second_evidence_quality="verified",
        source_schema_id="test",
        source_schema_version="1",
    )

    price_signals = compose_bound_cross_border_price_signals(
        scoring_input
    )

    aligned = align_cross_border_candidate_components(
        price_signals=price_signals,
        first_binding=CrossBorderCandidateComponentBinding(
            candidate_ref="candidate:first",
            base_components=_base(
                quality=first_quality,
                trust=first_trust,
            ),
        ),
        second_binding=CrossBorderCandidateComponentBinding(
            candidate_ref="candidate:second",
            base_components=_base(
                quality=second_quality,
                trust=second_trust,
            ),
        ),
    )

    scores = compose_cross_border_candidate_scores(
        aligned_components=aligned,
        priority=score_priority,
    )

    return price_signals, aligned, scores


def test_price_priority_uses_preserved_landed_cost():
    price_signals, aligned, scores = _surfaces(
        first_cost=Decimal("120"),
        second_cost=Decimal("80"),
    )

    ranked = rank_cross_border_candidate_pair(
        scores=scores,
        price_signals=price_signals,
        aligned_components=aligned,
        priority=RecommendationPriority.PRICE,
    )

    assert ranked[0].candidate_ref == "candidate:second"
    assert ranked[0].landed_cost == 80.0
    assert ranked[1].candidate_ref == "candidate:first"
    assert ranked[1].landed_cost == 120.0


def test_quality_priority_uses_aligned_quality():
    price_signals, aligned, scores = _surfaces(
        first_quality=70.0,
        second_quality=95.0,
    )

    ranked = rank_cross_border_candidate_pair(
        scores=scores,
        price_signals=price_signals,
        aligned_components=aligned,
        priority=RecommendationPriority.QUALITY,
    )

    assert ranked[0].candidate_ref == "candidate:second"


def test_trust_priority_uses_aligned_trust():
    price_signals, aligned, scores = _surfaces(
        first_trust=60.0,
        second_trust=98.0,
    )

    ranked = rank_cross_border_candidate_pair(
        scores=scores,
        price_signals=price_signals,
        aligned_components=aligned,
        priority=RecommendationPriority.TRUST,
    )

    assert ranked[0].candidate_ref == "candidate:second"


def test_mix_priority_uses_canonical_final_score():
    price_signals, aligned, scores = _surfaces()

    ranked = rank_cross_border_candidate_pair(
        scores=scores,
        price_signals=price_signals,
        aligned_components=aligned,
        priority=RecommendationPriority.MIX,
    )

    expected = sorted(
        [
            ("candidate:first", scores.first_score.final_score),
            ("candidate:second", scores.second_score.final_score),
        ],
        key=lambda item: item[1],
        reverse=True,
    )

    assert [item.candidate_ref for item in ranked] == [
        item[0] for item in expected
    ]


def test_complete_tie_preserves_pair_order():
    price_signals, aligned, scores = _surfaces(
        first_cost=Decimal("100"),
        second_cost=Decimal("100"),
        first_quality=90.0,
        second_quality=90.0,
        first_trust=80.0,
        second_trust=80.0,
    )

    ranked = rank_cross_border_candidate_pair(
        scores=scores,
        price_signals=price_signals,
        aligned_components=aligned,
        priority=RecommendationPriority.MIX,
    )

    assert [item.candidate_ref for item in ranked] == [
        "candidate:first",
        "candidate:second",
    ]


def test_misaligned_candidate_ref_fails_closed():
    price_signals, aligned, scores = _surfaces()

    altered = type(scores)(
        first_candidate_ref="candidate:wrong",
        second_candidate_ref=scores.second_candidate_ref,
        first_score=scores.first_score,
        second_score=scores.second_score,
    )

    with pytest.raises(
        ValueError,
        match="first candidate_ref",
    ):
        rank_cross_border_candidate_pair(
            scores=altered,
            price_signals=price_signals,
            aligned_components=aligned,
            priority=RecommendationPriority.MIX,
        )


def test_rankable_candidate_is_immutable():
    price_signals, aligned, scores = _surfaces()

    ranked = rank_cross_border_candidate_pair(
        scores=scores,
        price_signals=price_signals,
        aligned_components=aligned,
        priority=RecommendationPriority.MIX,
    )

    assert isinstance(
        ranked[0],
        CrossBorderRankableCandidate,
    )

    with pytest.raises(FrozenInstanceError):
        ranked[0].candidate_ref = "changed"


def test_rankable_candidate_has_no_selection_or_transaction_surface():
    price_signals, aligned, scores = _surfaces()

    ranked = rank_cross_border_candidate_pair(
        scores=scores,
        price_signals=price_signals,
        aligned_components=aligned,
        priority=RecommendationPriority.MIX,
    )

    forbidden = {
        "winner",
        "selected_candidate",
        "best_candidate",
        "recommendation",
        "checkout",
        "payment",
        "purchase",
        "dispatch",
        "production_enabled",
        "rollout_started",
        "route_traffic",
    }

    public_names = {
        name.lower()
        for name in dir(ranked[0])
        if not name.startswith("_")
    }

    assert forbidden.isdisjoint(public_names)
