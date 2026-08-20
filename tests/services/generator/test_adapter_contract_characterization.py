from __future__ import annotations

from dataclasses import fields

from app.services.recommendation.models import (
    RecommendationCandidate,
    RecommendationContext,
    RecommendationPriority,
    RecommendationResult,
    RecommendationScoreComponents,
    RecommendationScoreResult,
)


LEGACY_RESPONSE_KEYS = {
    "query",
    "search_keyword",
    "intent",
    "mode",
    "priority",
    "summary",
    "top3",
    "best_price",
    "best_quality",
    "products",
}


def _candidate(
    *,
    product_id: str,
    product_name: str,
    price: int,
    quality: float,
    final_score: float,
    rank: int,
) -> RecommendationCandidate:
    return RecommendationCandidate(
        item={
            "product_id": product_id,
            "product_name": product_name,
            "price": price,
        },
        score=RecommendationScoreResult(
            final_score=final_score,
            priority=RecommendationPriority.MIX,
            components=RecommendationScoreComponents(
                quality=quality,
                price=0.0,
                trust=0.0,
                popularity=0.0,
                market=0.0,
                identity=0.0,
            ),
        ),
        rank=rank,
    )


def _result() -> RecommendationResult:
    context = RecommendationContext(
        query="사과",
        priority=RecommendationPriority.MIX,
        limit=10,
    )

    return RecommendationResult(
        context=context,
        candidates=(
            _candidate(
                product_id="A",
                product_name="사과 A",
                price=12000,
                quality=90.0,
                final_score=91.0,
                rank=1,
            ),
            _candidate(
                product_id="B",
                product_name="사과 B",
                price=9000,
                quality=80.0,
                final_score=85.0,
                rank=2,
            ),
            _candidate(
                product_id="C",
                product_name="사과 C",
                price=15000,
                quality=95.0,
                final_score=82.0,
                rank=3,
            ),
            _candidate(
                product_id="D",
                product_name="사과 D",
                price=8000,
                quality=70.0,
                final_score=78.0,
                rank=4,
            ),
        ),
        summary="canonical summary",
    )


def test_canonical_result_does_not_own_legacy_api_fields() -> None:
    canonical_fields = {
        item.name
        for item in fields(RecommendationResult)
    }

    assert canonical_fields == {
        "context",
        "candidates",
        "summary",
        "warnings",
        "metadata",
    }

    assert (
        canonical_fields
        & LEGACY_RESPONSE_KEYS
        == {"summary"}
    )


def test_candidate_item_is_adapter_product_source() -> None:
    result = _result()

    candidate = result.candidates[0]

    assert candidate.item["product_id"] == "A"
    assert candidate.item["product_name"] == "사과 A"
    assert candidate.item["price"] == 12000


def test_candidate_rank_is_canonical_order_source() -> None:
    result = _result()

    assert [
        candidate.rank
        for candidate in result.candidates
    ] == [1, 2, 3, 4]


def test_legacy_top3_can_be_derived_from_ranked_candidates() -> None:
    result = _result()

    top3 = [
        dict(candidate.item)
        for candidate in result.candidates[:3]
    ]

    assert [
        item["product_id"]
        for item in top3
    ] == ["A", "B", "C"]


def test_best_price_is_adapter_derived_not_result_field() -> None:
    result = _result()

    best_price_candidate = min(
        result.candidates,
        key=lambda candidate: (
            candidate.item["price"]
        ),
    )

    assert (
        best_price_candidate.item["product_id"]
        == "D"
    )

    assert not hasattr(
        result,
        "best_price",
    )


def test_best_quality_is_adapter_derived_not_result_field() -> None:
    result = _result()

    best_quality_candidate = max(
        result.candidates,
        key=lambda candidate: (
            candidate.score.components.quality
        ),
    )

    assert (
        best_quality_candidate.item["product_id"]
        == "C"
    )

    assert not hasattr(
        result,
        "best_quality",
    )


def test_b2b_strategy_is_not_canonical_result_responsibility() -> None:
    result = _result()

    assert not hasattr(
        result,
        "b2b_strategy",
    )

    assert all(
        "b2b_strategy"
        not in candidate.item
        for candidate in result.candidates
    )


def test_empty_canonical_result_has_empty_candidates() -> None:
    result = RecommendationResult(
        context=RecommendationContext(
            query="사과",
            priority=RecommendationPriority.MIX,
        ),
    )

    assert result.candidates == ()


def test_adapter_must_preserve_canonical_summary_without_ownership_leak() -> None:
    result = _result()

    assert result.summary == "canonical summary"

    assert not hasattr(
        result,
        "top3",
    )

    assert not hasattr(
        result,
        "products",
    )


def test_legacy_response_fields_remain_compatibility_contract() -> None:
    assert LEGACY_RESPONSE_KEYS == {
        "query",
        "search_keyword",
        "intent",
        "mode",
        "priority",
        "summary",
        "top3",
        "best_price",
        "best_quality",
        "products",
    }
