from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import app.services.generator_service as generator
import app.services.recommendation_pipeline as pipeline

from app.services.recommendation.models import (
    RecommendationContext,
    RecommendationPriority,
    RecommendationResult,
)


def _result() -> RecommendationResult:
    return RecommendationResult(
        context=RecommendationContext(
            query="사과",
            priority=RecommendationPriority.MIX,
            limit=10,
        ),
        candidates=(),
        summary="canonical summary",
    )


class StubProvider:
    def recommend(
        self,
        context,
    ):
        return _result()


def test_generator_entrypoint_uses_production_provider_composition():
    request = SimpleNamespace(
        context="사과 추천",
        mode="B2C",
        priority="ranking",
        quantity=None,
        session_id=None,
    )

    with patch.object(
        generator,
        "compose_production_recommendation_provider",
        return_value=StubProvider(),
    ) as compose_provider:
        with patch.object(
            generator,
            "analyze_user_query",
            return_value={
                "normalized_keyword": "사과",
            },
        ):
            with patch.object(
                generator,
                "build_legacy_response_components",
                return_value={
                    "summary": "canonical summary",
                    "top3": [],
                    "best_price": None,
                    "best_quality": None,
                    "products": [],
                },
            ):
                generator.generate_product_strategy(
                    request
                )

    compose_provider.assert_called_once_with()


def test_pipeline_entrypoint_uses_production_provider_composition():
    with patch.object(
        pipeline,
        "compose_production_recommendation_provider",
        return_value=StubProvider(),
    ) as compose_provider:
        result = pipeline.run_recommendation_pipeline(
            q="사과",
            priority="ranking",
            limit=10,
        )

    compose_provider.assert_called_once_with()

    assert result["engine_version"] == (
        "recommendation_provider_canonical"
    )


def test_generator_no_longer_directly_constructs_provider():
    source = Path(
        "app/services/generator_service.py"
    ).read_text(
        encoding="utf-8"
    )

    assert (
        "RecommendationProvider()"
        not in source
    )

    assert (
        "compose_production_recommendation_provider()"
        in source
    )


def test_pipeline_no_longer_directly_constructs_provider():
    source = Path(
        "app/services/recommendation_pipeline.py"
    ).read_text(
        encoding="utf-8"
    )

    assert (
        "RecommendationProvider()"
        not in source
    )

    assert (
        "compose_production_recommendation_provider()"
        in source
    )


def test_entrypoints_do_not_supply_runtime_authority_or_candidate_scorer():
    generator_source = Path(
        "app/services/generator_service.py"
    ).read_text(
        encoding="utf-8"
    )

    pipeline_source = Path(
        "app/services/recommendation_pipeline.py"
    ).read_text(
        encoding="utf-8"
    )

    for source in (
        generator_source,
        pipeline_source,
    ):
        assert (
            "authority_source="
            not in source
        )

        assert (
            "candidate_scorer="
            not in source
        )
