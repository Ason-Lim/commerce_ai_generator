from __future__ import annotations

from app.services.generator_compatibility import (
    apply_legacy_b2b_strategy,
    build_legacy_response_components,
    candidate_to_legacy_product,
    legacy_best_price_from_result,
    legacy_best_quality_from_result,
    legacy_products_from_result,
    legacy_top3_from_result,
)
from app.services.recommendation.models import (
    RecommendationCandidate,
    RecommendationContext,
    RecommendationPriority,
    RecommendationResult,
    RecommendationScoreComponents,
    RecommendationScoreResult,
)


def candidate(
    *,
    product_id: str,
    price: int,
    quality: float,
    final_score: float,
    rank: int,
) -> RecommendationCandidate:
    return RecommendationCandidate(
        item={
            "product_id": product_id,
            "product_name": f"상품 {product_id}",
            "price": price,
        },
        score=RecommendationScoreResult(
            final_score=final_score,
            priority=RecommendationPriority.MIX,
            components=RecommendationScoreComponents(
                quality=quality,
                price=50.0,
                trust=60.0,
                popularity=0.0,
                market=0.0,
                identity=0.0,
            ),
        ),
        rank=rank,
    )


def result() -> RecommendationResult:
    return RecommendationResult(
        context=RecommendationContext(
            query="사과",
            priority=RecommendationPriority.MIX,
        ),
        candidates=(
            candidate(
                product_id="A",
                price=12000,
                quality=90.0,
                final_score=95.0,
                rank=1,
            ),
            candidate(
                product_id="B",
                price=8000,
                quality=80.0,
                final_score=90.0,
                rank=2,
            ),
            candidate(
                product_id="C",
                price=15000,
                quality=98.0,
                final_score=85.0,
                rank=3,
            ),
            candidate(
                product_id="D",
                price=7000,
                quality=70.0,
                final_score=80.0,
                rank=4,
            ),
        ),
        summary="canonical summary",
    )


def test_candidate_to_legacy_product() -> None:
    item = candidate_to_legacy_product(
        result().candidates[0]
    )

    assert item["product_id"] == "A"
    assert item["rank"] == 1
    assert item["score"] == 95.0
    assert item["final_score"] == 95.0
    assert item["quality_score"] == 90.0
    assert item["price_score"] == 50.0
    assert item["trust_score"] == 60.0


def test_products_follow_canonical_rank() -> None:
    products = legacy_products_from_result(
        result()
    )

    assert [
        item["product_id"]
        for item in products
    ] == ["A", "B", "C", "D"]


def test_top3_follow_canonical_rank() -> None:
    top3 = legacy_top3_from_result(
        result()
    )

    assert [
        item["product_id"]
        for item in top3
    ] == ["A", "B", "C"]


def test_best_price_is_compatibility_derived() -> None:
    item = legacy_best_price_from_result(
        result()
    )

    assert item is not None
    assert item["product_id"] == "D"


def test_best_quality_is_compatibility_derived() -> None:
    item = legacy_best_quality_from_result(
        result()
    )

    assert item is not None
    assert item["product_id"] == "C"


def test_empty_result_has_no_best_candidates() -> None:
    empty = RecommendationResult(
        context=RecommendationContext(
            query="사과",
            priority=RecommendationPriority.MIX,
        )
    )

    assert (
        legacy_best_price_from_result(empty)
        is None
    )
    assert (
        legacy_best_quality_from_result(empty)
        is None
    )
    assert legacy_products_from_result(empty) == []
    assert legacy_top3_from_result(empty) == []


def test_b2b_strategy_is_injected() -> None:
    def builder(
        product,
        quantity,
    ):
        return {
            "product_id": product["product_id"],
            "quantity": quantity,
        }

    enriched = apply_legacy_b2b_strategy(
        legacy_top3_from_result(result()),
        quantity=100,
        strategy_builder=builder,
    )

    assert len(enriched) == 3

    for item in enriched:
        assert (
            item["b2b_strategy"]["quantity"]
            == 100
        )


def test_response_components_preserve_summary() -> None:
    components = (
        build_legacy_response_components(
            result(),
            mode="B2C",
        )
    )

    assert components["summary"] == (
        "canonical summary"
    )

    assert [
        item["product_id"]
        for item in components["top3"]
    ] == ["A", "B", "C"]

    assert (
        components["best_price"][
            "product_id"
        ]
        == "D"
    )

    assert (
        components["best_quality"][
            "product_id"
        ]
        == "C"
    )


def test_b2b_response_enriches_only_top3() -> None:
    def builder(
        product,
        quantity,
    ):
        return {
            "quantity": quantity,
        }

    components = (
        build_legacy_response_components(
            result(),
            mode="B2B",
            quantity=50,
            strategy_builder=builder,
        )
    )

    assert all(
        "b2b_strategy" in item
        for item in components["top3"]
    )

    assert all(
        "b2b_strategy" not in item
        for item in components["products"]
    )


def test_adapter_does_not_mutate_canonical_items() -> None:
    canonical = result()

    build_legacy_response_components(
        canonical,
        mode="B2C",
    )

    assert all(
        "score" not in candidate.item
        for candidate in canonical.candidates
    )
