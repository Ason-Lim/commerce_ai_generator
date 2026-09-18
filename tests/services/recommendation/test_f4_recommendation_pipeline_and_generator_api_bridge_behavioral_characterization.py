from __future__ import annotations

from types import SimpleNamespace

import app.main as main
import app.services.generator_compatibility as compatibility
import app.services.generator_service as generator
import app.services.recommendation_pipeline as pipeline
from app.services.recommendation.models import (
    RecommendationCandidate,
    RecommendationContext,
    RecommendationResult,
    RecommendationScoreComponents,
    RecommendationScoreResult,
)
from app.services.recommendation.provider import RecommendationProvider


def _provider() -> RecommendationProvider:
    items = [
        {
            "product_name": "사과 A",
            "price": 12000,
            "quality": 90.0,
        },
        {
            "product_name": "사과 B",
            "price": 9000,
            "quality": 80.0,
        },
    ]

    def passthrough(rows):
        return list(rows)

    def build_components(item):
        value = float(item["quality"])
        return RecommendationScoreComponents(
            quality=value,
            price=value,
            trust=value,
            popularity=value,
            market=value,
            identity=value,
        )

    def score(components, priority):
        return RecommendationScoreResult(
            final_score=components.quality,
            priority=priority,
            components=components,
            version="f4-bridge-characterization",
        )

    return RecommendationProvider(
        collector=lambda query, limit: list(items),
        deduplicator=passthrough,
        normalizer=passthrough,
        food_enricher=passthrough,
        price_preparer=passthrough,
        trust_preparer=passthrough,
        popularity_preparer=passthrough,
        market_preparer=passthrough,
        identity_preparer=passthrough,
        component_builder=build_components,
        scorer=score,
    )


def test_canonical_recommendation_model_and_result_compatibility():
    context = pipeline.build_canonical_context(
        q="사과 추천",
        priority="ranking",
        session_id="f4-model-session",
        limit=2,
    )
    result = _provider().recommend(context)

    assert isinstance(context, RecommendationContext)
    assert isinstance(result, RecommendationResult)
    assert isinstance(result.candidates[0], RecommendationCandidate)
    assert compatibility.RecommendationResult is RecommendationResult
    assert compatibility.RecommendationCandidate is RecommendationCandidate


def test_production_provider_composition_and_context_construction_behavior(
    monkeypatch,
):
    captured = {}
    provider = _provider()

    class CapturingProvider:
        def recommend(self, context):
            captured["context"] = context
            return provider.recommend(context)

    monkeypatch.setattr(
        pipeline,
        "compose_production_recommendation_provider",
        lambda: CapturingProvider(),
    )

    response = pipeline.run_recommendation_pipeline(
        q="사과 추천",
        priority="quality_adaptive",
        session_id="f4-pipeline-session",
        limit=2,
    )

    context = captured["context"]
    assert context.query == "사과"
    assert context.priority is pipeline.RecommendationPriority.QUALITY
    assert context.adaptive is True
    assert context.session_id == "f4-pipeline-session"
    assert context.limit == 2
    assert response["engine_version"] == "recommendation_provider_canonical"
    assert [item["rank"] for item in response["items"]] == [1, 2]


def test_generator_service_request_and_result_bridge_behavior(monkeypatch):
    monkeypatch.setattr(
        generator,
        "compose_production_recommendation_provider",
        _provider,
    )
    monkeypatch.setattr(
        generator,
        "analyze_user_query",
        lambda query: {
            "normalized_keyword": "사과",
            "observed_query": query,
        },
    )

    response = generator.generate_product_strategy(
        SimpleNamespace(
            context="사과 추천",
            mode="B2C",
            priority="ranking",
            quantity=None,
            session_id="f4-generator-session",
        )
    )

    assert response["query"] == "사과 추천"
    assert response["search_keyword"] == "사과"
    assert response["intent"]["observed_query"] == "사과 추천"
    assert response["mode"] == "B2C"
    assert response["priority"] == "ranking"
    assert len(response["products"]) == 2
    assert [item["rank"] for item in response["products"]] == [1, 2]


def test_generate_endpoint_bridge_behavior(monkeypatch):
    calls = {"collector": [], "generator": []}
    expected = {"bridge": "generate"}

    monkeypatch.setattr(
        main,
        "collect_naver_products",
        lambda query: calls["collector"].append(query),
    )

    def fake_generate(request):
        calls["generator"].append(request)
        return expected

    monkeypatch.setattr(main, "generate_product_strategy", fake_generate)

    request = main.RequestModel(
        context="사과 추천",
        mode="B2C",
        priority="ranking",
        quantity=None,
    )
    result = main.generate(request)

    assert result is expected
    assert calls["collector"] == ["사과 추천"]
    assert calls["generator"] == [request]


def test_recommendations_v2_and_nl_pipeline_bridge_behavior(monkeypatch):
    calls = []

    def fake_pipeline(**kwargs):
        calls.append(kwargs)
        return {"call_number": len(calls)}

    monkeypatch.setattr(main, "run_recommendation_pipeline", fake_pipeline)

    v2_result = main.recommendations_v2(
        q="사과 추천",
        priority="quality",
        session_id="f4-api-session",
    )
    nl_result = main.natural_language_recommendations(
        q="사과 추천",
        priority="quality",
        session_id="f4-api-session",
    )

    expected_call = {
        "q": "사과 추천",
        "priority": "quality",
        "session_id": "f4-api-session",
        "limit": 10,
    }
    assert calls == [expected_call, expected_call]
    assert v2_result == {"call_number": 1}
    assert nl_result == {"call_number": 2}
