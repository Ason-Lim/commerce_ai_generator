from __future__ import annotations

from types import SimpleNamespace

import app.services.generator_service as generator
from app.services.recommendation.models import (
    RecommendationCandidate,
    RecommendationContext,
    RecommendationPriority,
    RecommendationResult,
    RecommendationScoreComponents,
    RecommendationScoreResult,
)


EXPECTED_RESPONSE_KEYS = {
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


def make_request(
    *,
    context: str = "가성비 좋은 사과 추천",
    mode: str = "B2C",
    priority: str = "price",
    quantity=None,
    session_id=None,
):
    return SimpleNamespace(
        context=context,
        mode=mode,
        priority=priority,
        quantity=quantity,
        session_id=session_id,
    )


def candidate(
    *,
    product_id: str,
    product_name: str,
    price: int,
    quality: float,
    final_score: float,
    rank: int,
):
    return RecommendationCandidate(
        item={
            "product_id": product_id,
            "product_name": product_name,
            "price": price,
        },
        score=RecommendationScoreResult(
            final_score=final_score,
            priority=RecommendationPriority.PRICE,
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


def canonical_result(
    *,
    candidates=(),
    summary="canonical summary",
):
    return RecommendationResult(
        context=RecommendationContext(
            query="사과",
            priority=RecommendationPriority.PRICE,
            limit=10,
        ),
        candidates=tuple(candidates),
        summary=summary,
    )


class StubProvider:
    result = None
    received_context = None

    def recommend(self, context):
        type(self).received_context = context
        return type(self).result


def patch_canonical_runtime(
    monkeypatch,
    result,
):
    StubProvider.result = result
    StubProvider.received_context = None

    monkeypatch.setattr(
        generator,
        "compose_production_recommendation_provider",
        lambda: StubProvider(),
    )


def test_generate_product_strategy_preserves_response_contract(
    monkeypatch,
):
    patch_canonical_runtime(
        monkeypatch,
        canonical_result(
            candidates=(
                candidate(
                    product_id="A",
                    product_name="사과 A",
                    price=12000,
                    quality=90.0,
                    final_score=91.0,
                    rank=1,
                ),
                candidate(
                    product_id="B",
                    product_name="사과 B",
                    price=9000,
                    quality=80.0,
                    final_score=85.0,
                    rank=2,
                ),
                candidate(
                    product_id="C",
                    product_name="사과 C",
                    price=15000,
                    quality=95.0,
                    final_score=82.0,
                    rank=3,
                ),
            ),
        ),
    )

    result = generator.generate_product_strategy(
        make_request()
    )

    assert result is not None
    assert set(result) == EXPECTED_RESPONSE_KEYS
    assert result["query"] == "가성비 좋은 사과 추천"
    assert result["search_keyword"] == "사과"
    assert result["mode"] == "B2C"
    assert result["priority"] == "price"
    assert len(result["top3"]) == 3
    assert len(result["products"]) == 3


def test_generate_product_strategy_uses_canonical_provider_order(
    monkeypatch,
):
    patch_canonical_runtime(
        monkeypatch,
        canonical_result(
            candidates=(
                candidate(
                    product_id="HIGH",
                    product_name="Canonical First",
                    price=20000,
                    quality=80.0,
                    final_score=99.0,
                    rank=1,
                ),
                candidate(
                    product_id="LOW",
                    product_name="Canonical Second",
                    price=5000,
                    quality=90.0,
                    final_score=70.0,
                    rank=2,
                ),
            ),
        ),
    )

    result = generator.generate_product_strategy(
        make_request()
    )

    assert [
        item["product_id"]
        for item in result["products"]
    ] == [
        "HIGH",
        "LOW",
    ]


def test_generate_product_strategy_passes_session_id_to_context(
    monkeypatch,
):
    patch_canonical_runtime(
        monkeypatch,
        canonical_result(),
    )

    generator.generate_product_strategy(
        make_request(
            session_id="session-123",
        )
    )

    context = StubProvider.received_context

    assert context is not None
    assert context.session_id == "session-123"


def test_generate_product_strategy_supports_legacy_request_without_session_id(
    monkeypatch,
):
    request = SimpleNamespace(
        context="사과 추천",
        mode="B2C",
        priority="price",
        quantity=None,
    )

    patch_canonical_runtime(
        monkeypatch,
        canonical_result(),
    )

    result = generator.generate_product_strategy(
        request
    )

    assert result is not None
    assert StubProvider.received_context.session_id is None


def test_generate_product_strategy_preserves_b2b_compatibility(
    monkeypatch,
):
    patch_canonical_runtime(
        monkeypatch,
        canonical_result(
            candidates=(
                candidate(
                    product_id="A",
                    product_name="B2B 사과 A",
                    price=10000,
                    quality=90.0,
                    final_score=95.0,
                    rank=1,
                ),
                candidate(
                    product_id="B",
                    product_name="B2B 사과 B",
                    price=11000,
                    quality=80.0,
                    final_score=85.0,
                    rank=2,
                ),
            ),
        ),
    )

    monkeypatch.setattr(
        generator,
        "build_b2b_strategy",
        lambda item, quantity: {
            "quantity": quantity,
            "product_id": item["product_id"],
        },
    )

    result = generator.generate_product_strategy(
        make_request(
            mode="B2B",
            quantity=100,
        )
    )

    assert result["top3"][0]["b2b_strategy"] == {
        "quantity": 100,
        "product_id": "A",
    }


def test_generate_product_strategy_empty_canonical_result_preserves_shape(
    monkeypatch,
):
    patch_canonical_runtime(
        monkeypatch,
        canonical_result(),
    )

    result = generator.generate_product_strategy(
        make_request()
    )

    assert result is not None
    assert set(result) == EXPECTED_RESPONSE_KEYS
    assert result["top3"] == []
    assert result["products"] == []
    assert result["best_price"] is None
    assert result["best_quality"] is None


def test_generate_product_strategy_preserves_canonical_summary(
    monkeypatch,
):
    patch_canonical_runtime(
        monkeypatch,
        canonical_result(
            summary="canonical summary",
        ),
    )

    result = generator.generate_product_strategy(
        make_request()
    )

    assert result["summary"] == "canonical summary"


def test_generate_product_strategy_no_longer_owns_legacy_execution():
    source = (
        generator.generate_product_strategy
        .__code__
        .co_names
    )

    retired_names = {
        "fetch_products_from_db",
        "normalize_product",
        "deduplicate_products",
        "calculate_trust_score",
        "calculate_final_score",
        "find_best_price_product",
        "find_best_quality_product",
    }

    assert retired_names.isdisjoint(
        set(source)
    )
