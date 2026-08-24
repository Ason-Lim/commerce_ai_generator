from __future__ import annotations

from app.services.recommendation.context import (
    build_recommendation_context,
)
from app.services.recommendation.models import (
    RecommendationCandidate,
    RecommendationPriority,
    RecommendationScoreComponents,
    RecommendationScoreResult,
    RecommendationResult,
)
from app.services.recommendation.parser import (
    parse_recommendation_query,
)
from app.services.recommendation.policy import (
    resolve_recommendation_policy,
)
from app.services.recommendation.cross_border_canonical_result_projection import (
    project_cross_border_canonical_result,
)


def _context():
    return build_recommendation_context(
        parse_recommendation_query("한국 사과"),
        resolve_recommendation_policy("ranking"),
    )


def _score(value: float) -> RecommendationScoreResult:
    return RecommendationScoreResult(
        priority=RecommendationPriority.MIX,
        components=RecommendationScoreComponents(),
        final_score=value,
    )


def _candidates():
    return (
        RecommendationCandidate(
            item={
                "product_id": "A",
                "product_name": "한국 사과 A",
            },
            score=_score(90.0),
            rank=1,
            metadata={
                "source": "cross_border",
            },
        ),
        RecommendationCandidate(
            item={
                "product_id": "B",
                "product_name": "한국 사과 B",
            },
            score=_score(80.0),
            rank=2,
            metadata={
                "source": "cross_border",
            },
        ),
    )


def test_projection_returns_canonical_recommendation_result():
    context = _context()
    candidates = _candidates()

    result = project_cross_border_canonical_result(
        context=context,
        candidates=candidates,
    )

    assert isinstance(result, RecommendationResult)
    assert result.context is context


def test_projection_preserves_candidate_order_and_identity():
    candidates = _candidates()

    result = project_cross_border_canonical_result(
        context=_context(),
        candidates=candidates,
    )

    assert result.candidates == candidates
    assert result.candidates[0] is candidates[0]
    assert result.candidates[1] is candidates[1]

    assert [
        candidate.rank
        for candidate in result.candidates
    ] == [1, 2]


def test_projection_reuses_existing_score_objects():
    candidates = _candidates()

    result = project_cross_border_canonical_result(
        context=_context(),
        candidates=candidates,
    )

    assert result.candidates[0].score is candidates[0].score
    assert result.candidates[1].score is candidates[1].score


def test_projection_adds_only_bounded_result_metadata():
    candidates = _candidates()

    result = project_cross_border_canonical_result(
        context=_context(),
        candidates=candidates,
    )

    assert dict(result.metadata) == {
        "provider": "CrossBorderCanonicalResultProjection",
        "candidate_count": 2,
    }


def test_projection_does_not_create_selection_authority():
    result = project_cross_border_canonical_result(
        context=_context(),
        candidates=_candidates(),
    )

    forbidden = {
        "winner",
        "winner_id",
        "selected_candidate",
        "selected_candidate_id",
        "selection_reason",
        "recommended_candidate",
    }

    assert not (
        forbidden
        & set(result.metadata)
    )

    assert not any(
        hasattr(result, name)
        for name in forbidden
    )


def test_projection_does_not_mutate_candidates():
    candidates = _candidates()

    before = tuple(
        (
            dict(candidate.item),
            candidate.score,
            candidate.rank,
            dict(candidate.metadata),
        )
        for candidate in candidates
    )

    project_cross_border_canonical_result(
        context=_context(),
        candidates=candidates,
    )

    after = tuple(
        (
            dict(candidate.item),
            candidate.score,
            candidate.rank,
            dict(candidate.metadata),
        )
        for candidate in candidates
    )

    assert after == before


def test_empty_candidate_sequence_is_valid():
    context = _context()

    result = project_cross_border_canonical_result(
        context=context,
        candidates=(),
    )

    assert result.context is context
    assert result.candidates == ()
    assert result.metadata["candidate_count"] == 0


def test_projection_preserves_candidate_disclosure_metadata_unchanged():
    candidate = RecommendationCandidate(
        item={
            "product_id": "DISCLOSURE-A",
            "product_name": "Disclosure Product A",
        },
        score=_score(91.0),
        rank=1,
        metadata={
            "source": "cross_border",
            "cross_border": {
                "candidate_ref": "candidate:first",
                "candidate_position": 1,
                "landed_cost": 78.0,
                "estimate_disclosure": {
                    "total": "78.00",
                    "currency": "USD",
                    "fx_base_currency": "USD",
                    "fx_quote_currency": "KRW",
                    "fx_rate": "1390",
                    "temporal_state": "evaluable",
                },
            },
        },
    )

    disclosure_before = (
        candidate.metadata["cross_border"]["estimate_disclosure"]
    )

    result = project_cross_border_canonical_result(
        context=_context(),
        candidates=(candidate,),
    )

    projected = result.candidates[0]

    assert projected is candidate
    assert (
        projected.metadata["cross_border"]["estimate_disclosure"]
        is disclosure_before
    )
    assert (
        projected.metadata["cross_border"]["estimate_disclosure"]
        == disclosure_before
    )


def test_projection_preserves_independent_candidate_disclosures():
    first = RecommendationCandidate(
        item={"product_id": "A"},
        score=_score(90.0),
        rank=1,
        metadata={
            "cross_border": {
                "candidate_ref": "candidate:first",
                "candidate_position": 1,
                "landed_cost": 78.0,
                "estimate_disclosure": {
                    "total": "78.00",
                    "currency": "USD",
                    "fx_rate": "1390",
                },
            },
        },
    )

    second = RecommendationCandidate(
        item={"product_id": "B"},
        score=_score(80.0),
        rank=2,
        metadata={
            "cross_border": {
                "candidate_ref": "candidate:second",
                "candidate_position": 2,
                "landed_cost": 95.0,
                "estimate_disclosure": {
                    "total": "95.00",
                    "currency": "USD",
                    "fx_rate": "1401",
                },
            },
        },
    )

    first_disclosure = (
        first.metadata["cross_border"]["estimate_disclosure"]
    )
    second_disclosure = (
        second.metadata["cross_border"]["estimate_disclosure"]
    )

    result = project_cross_border_canonical_result(
        context=_context(),
        candidates=(first, second),
    )

    assert result.candidates[0] is first
    assert result.candidates[1] is second

    assert (
        result.candidates[0]
        .metadata["cross_border"]["estimate_disclosure"]
        is first_disclosure
    )
    assert (
        result.candidates[1]
        .metadata["cross_border"]["estimate_disclosure"]
        is second_disclosure
    )

    assert first_disclosure is not second_disclosure
    assert first_disclosure["total"] == "78.00"
    assert second_disclosure["total"] == "95.00"
