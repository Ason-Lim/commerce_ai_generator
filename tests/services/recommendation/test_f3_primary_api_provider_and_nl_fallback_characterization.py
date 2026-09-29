from __future__ import annotations

import builtins
from types import SimpleNamespace

import pytest

import app.main as main
import app.services.generator_service as generator
import app.services.recommendation.provider as provider_module
import app.services.recommendation_pipeline as pipeline
from app.services.recommendation.models import (
    RecommendationScoreComponents,
    RecommendationScoreResult,
)
from app.services.recommendation.provider import RecommendationProvider
from app.services.recommendation.ranking import (
    rank_candidates as canonical_rank_candidates,
)


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
            version="f3-characterization",
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


def _install_rank_counter(monkeypatch):
    calls = {"count": 0}

    def counted_rank(*args, **kwargs):
        calls["count"] += 1
        return canonical_rank_candidates(
            *args,
            **kwargs,
        )

    monkeypatch.setattr(
        provider_module,
        "rank_candidates",
        counted_rank,
    )

    return calls


def _install_fallback_sort_counter(monkeypatch):
    calls = {"count": 0}

    def counted_sorted(*args, **kwargs):
        calls["count"] += 1
        return builtins.sorted(
            *args,
            **kwargs,
        )

    monkeypatch.setattr(
        main,
        "sorted",
        counted_sorted,
        raising=False,
    )

    return calls


def test_generate_executes_canonical_provider_ranking_once(
    monkeypatch,
):
    rank_calls = _install_rank_counter(
        monkeypatch
    )

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
        },
    )
    monkeypatch.setattr(
        generator,
        "build_legacy_response_components",
        lambda result, **kwargs: {
            "summary": result.summary,
            "top3": [],
            "best_price": None,
            "best_quality": None,
            "products": [],
        },
    )

    generator.generate_product_strategy(
        SimpleNamespace(
            context="사과 추천",
            mode="B2C",
            priority="ranking",
            quantity=None,
            session_id=None,
        )
    )

    assert rank_calls["count"] == 1


def test_recommendations_v2_executes_canonical_provider_ranking_once(
    monkeypatch,
):
    rank_calls = _install_rank_counter(
        monkeypatch
    )

    monkeypatch.setattr(
        pipeline,
        "compose_production_recommendation_provider",
        _provider,
    )

    result = main.recommendations_v2(
        q="사과 추천",
        priority="ranking",
        session_id=None,
    )

    assert rank_calls["count"] == 1
    assert result["engine_version"] == (
        "recommendation_provider_canonical"
    )
    assert "recommendation_path" not in result


def test_recommendations_nl_success_executes_rank_once_and_no_fallback_sort(
    monkeypatch,
):
    rank_calls = _install_rank_counter(
        monkeypatch
    )
    fallback_sort_calls = (
        _install_fallback_sort_counter(
            monkeypatch
        )
    )

    monkeypatch.setattr(
        pipeline,
        "compose_production_recommendation_provider",
        _provider,
    )

    result = main.natural_language_recommendations(
        q="사과 추천",
        priority="ranking",
        session_id=None,
    )

    assert rank_calls["count"] == 1
    assert fallback_sort_calls["count"] == 0
    assert result["engine_version"] == (
        "recommendation_provider_canonical"
    )
    assert result["recommendation_path"] == main.NL_PATH_CANONICAL
    assert [item["score"] for item in result["items"]] == [0, 0]
    assert [item["rank"] for item in result["items"]] == [1, 2]


class _FallbackRows:
    def mappings(self):
        return self

    def all(self):
        return [
            {
                "product_name": "사과 A",
                "price": 12000,
                "db_price_per_100g": 12000,
                "final_recommendation_score": 80.0,
                "final_recommendation_label": "사용자 반응 우수 추천",
                "recommendation_reason": "리뷰 999건으로 구매자 반응이 확인됩니다.",
            },
            {
                "product_name": "사과 B",
                "price": 9000,
                "db_price_per_100g": 9000,
                "final_recommendation_score": 70.0,
            },
        ]


class _FallbackConnection:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def execute(self, statement, parameters):
        return _FallbackRows()


class _FallbackEngine:
    def connect(self):
        return _FallbackConnection()


def test_recommendations_nl_exception_executes_only_one_fallback_sort(
    monkeypatch,
):
    rank_calls = _install_rank_counter(
        monkeypatch
    )
    fallback_sort_calls = (
        _install_fallback_sort_counter(
            monkeypatch
        )
    )

    def fail_pipeline(**kwargs):
        raise RuntimeError(
            "forced F3 fallback characterization"
        )

    monkeypatch.setattr(
        main,
        "run_recommendation_pipeline",
        fail_pipeline,
    )
    monkeypatch.setattr(
        main,
        "_get_canonical_engine",
        lambda: _FallbackEngine(),
    )

    result = main.natural_language_recommendations(
        q="사과 추천",
        priority="ranking",
        session_id=None,
    )

    assert rank_calls["count"] == 0
    assert fallback_sort_calls["count"] == 1
    assert result["recommendation_path"] == main.NL_PATH_DB_FALLBACK
    assert [item["score"] for item in result["items"]] == [80.0, 70.0]
    assert "추천 후보" in result["summary"]
    assert "반응 좋은" not in result["summary"]
    assert "구매자 반응 근거는 확인되지 않았습니다" in result["items"][0]["recommendation_reason"]
    assert result["items"][0]["final_recommendation_label"] == "계산 지표 기반 추천"
    assert [
        item["rank"]
        for item in result["items"]
    ] == [1, 2]


def test_nl_db_fallback_price_order_does_not_redefine_score(monkeypatch):
    monkeypatch.setattr(
        main, "run_recommendation_pipeline", lambda **kwargs: 1 / 0
    )
    monkeypatch.setattr(main, "_get_canonical_engine", lambda: _FallbackEngine())

    result = main.natural_language_recommendations(q="사과", priority="price")

    assert result["recommendation_path"] == main.NL_PATH_DB_FALLBACK
    assert [item["product_name"] for item in result["items"]] == ["사과 B", "사과 A"]
    assert [item["score"] for item in result["items"]] == [70.0, 80.0]
    assert [item["rank"] for item in result["items"]] == [1, 2]


@pytest.mark.parametrize("path", [main.NL_PATH_CANONICAL, main.NL_PATH_DB_FALLBACK])
def test_revisit_forwards_nl_path_without_resorting_items(monkeypatch, path):
    class RevisitRows:
        def first(self):
            return {"fruit_name": "사과"}

    class RevisitConnection:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

        def execute(self, statement, parameters):
            return SimpleNamespace(mappings=lambda: RevisitRows())

    monkeypatch.setattr(
        main, "_get_canonical_engine",
        lambda: SimpleNamespace(connect=lambda: RevisitConnection()),
    )
    nl_items = [
        {"product_name": "첫째", "rank": 1, "score": 30},
        {"product_name": "둘째", "rank": 2, "score": 90},
        {"product_name": "셋째", "rank": 3, "score": 70},
    ]
    monkeypatch.setattr(
        main,
        "natural_language_recommendations",
        lambda **kwargs: {"recommendation_path": path, "items": nl_items},
    )

    result = main.revisit_recommendations("test-session", limit=2)

    assert result["recommendation_path"] == path
    assert result["items"] == nl_items[:2]
    assert [item["rank"] for item in result["items"]] == [1, 2]


def test_revisit_without_fruit_did_not_call_nl(monkeypatch):
    class EmptyConnection:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

        def execute(self, statement, parameters):
            return SimpleNamespace(mappings=lambda: SimpleNamespace(first=lambda: None))

    monkeypatch.setattr(
        main, "_get_canonical_engine",
        lambda: SimpleNamespace(connect=lambda: EmptyConnection()),
    )
    monkeypatch.setattr(
        main, "natural_language_recommendations",
        lambda **kwargs: pytest.fail("/nl must not run without a fruit"),
    )

    result = main.revisit_recommendations("test-session")

    assert result["items"] == []
    assert result["recommendation_path"] == main.NL_PATH_NOT_CALLED
