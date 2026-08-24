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
from app.services.recommendation.cross_border_candidate_score_composition import (
    PairwiseCrossBorderCandidateScores,
    compose_cross_border_candidate_scores,
)
from app.services.recommendation.cross_border_scoring_binding import (
    BoundCrossBorderScoringInput,
    CrossBorderScoringDirection,
)
from app.services.recommendation.models import (
    RecommendationPriority,
    RecommendationScoreComponents,
    RecommendationScoreResult,
)
from app.services.recommendation.scoring import (
    calculate_recommendation_score,
)


def _base(
    *,
    quality: float,
    price: float,
    trust: float,
) -> RecommendationScoreComponents:
    return RecommendationScoreComponents(
        quality=quality,
        price=price,
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


def _aligned():
    scoring_input = BoundCrossBorderScoringInput(
        first_candidate_ref="candidate:first",
        second_candidate_ref="candidate:second",
        first_landed_cost=Decimal("80"),
        second_landed_cost=Decimal("100"),
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

    return align_cross_border_candidate_components(
        price_signals=price_signals,
        first_binding=CrossBorderCandidateComponentBinding(
            candidate_ref="candidate:first",
            base_components=_base(
                quality=90.0,
                price=10.0,
                trust=80.0,
            ),
        ),
        second_binding=CrossBorderCandidateComponentBinding(
            candidate_ref="candidate:second",
            base_components=_base(
                quality=85.0,
                price=20.0,
                trust=75.0,
            ),
        ),
    )


def test_scores_both_candidates_independently():
    aligned = _aligned()

    result = compose_cross_border_candidate_scores(
        aligned_components=aligned,
        priority=RecommendationPriority.MIX,
    )

    assert result.first_score == calculate_recommendation_score(
        aligned.first_components,
        RecommendationPriority.MIX,
    )

    assert result.second_score == calculate_recommendation_score(
        aligned.second_components,
        RecommendationPriority.MIX,
    )


def test_candidate_refs_are_preserved():
    result = compose_cross_border_candidate_scores(
        aligned_components=_aligned(),
        priority=RecommendationPriority.PRICE,
    )

    assert result.first_candidate_ref == "candidate:first"
    assert result.second_candidate_ref == "candidate:second"


def test_same_priority_is_delegated_to_both_candidates():
    aligned = _aligned()
    calls = []

    def scorer(components, priority):
        calls.append(
            (
                components,
                priority,
            )
        )
        return calculate_recommendation_score(
            components,
            priority,
            version="candidate-test",
        )

    result = compose_cross_border_candidate_scores(
        aligned_components=aligned,
        priority=RecommendationPriority.QUALITY,
        scorer=scorer,
    )

    assert calls == [
        (
            aligned.first_components,
            RecommendationPriority.QUALITY,
        ),
        (
            aligned.second_components,
            RecommendationPriority.QUALITY,
        ),
    ]

    assert result.first_score.version == "candidate-test"
    assert result.second_score.version == "candidate-test"


def test_first_invalid_score_result_fails_closed():
    aligned = _aligned()
    calls = 0

    def invalid_first(components, priority):
        nonlocal calls
        calls += 1

        if calls == 1:
            return object()

        return calculate_recommendation_score(
            components,
            priority,
        )

    with pytest.raises(
        TypeError,
        match="first candidate scorer result",
    ):
        compose_cross_border_candidate_scores(
            aligned_components=aligned,
            priority=RecommendationPriority.MIX,
            scorer=invalid_first,
        )


def test_second_invalid_score_result_fails_closed():
    aligned = _aligned()
    calls = 0

    def invalid_second(components, priority):
        nonlocal calls
        calls += 1

        if calls == 2:
            return object()

        return calculate_recommendation_score(
            components,
            priority,
        )

    with pytest.raises(
        TypeError,
        match="second candidate scorer result",
    ):
        compose_cross_border_candidate_scores(
            aligned_components=aligned,
            priority=RecommendationPriority.MIX,
            scorer=invalid_second,
        )


def test_result_is_immutable():
    result = compose_cross_border_candidate_scores(
        aligned_components=_aligned(),
        priority=RecommendationPriority.MIX,
    )

    with pytest.raises(
        FrozenInstanceError,
    ):
        result.first_candidate_ref = "changed"


def test_result_is_bounded_contract_type():
    result = compose_cross_border_candidate_scores(
        aligned_components=_aligned(),
        priority=RecommendationPriority.MIX,
    )

    assert isinstance(
        result,
        PairwiseCrossBorderCandidateScores,
    )

    assert isinstance(
        result.first_score,
        RecommendationScoreResult,
    )

    assert isinstance(
        result.second_score,
        RecommendationScoreResult,
    )


def test_result_has_no_winner_ranking_or_transaction_surface():
    result = compose_cross_border_candidate_scores(
        aligned_components=_aligned(),
        priority=RecommendationPriority.MIX,
    )

    forbidden = {
        "winner",
        "better_candidate",
        "selected_candidate",
        "best_candidate",
        "rank",
        "ranking",
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
        for name in dir(result)
        if not name.startswith("_")
    }

    assert forbidden.isdisjoint(
        public_names
    )
