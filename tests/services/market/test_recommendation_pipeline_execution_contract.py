from unittest.mock import patch

from app.services.recommendation.models import (
    RecommendationCandidate,
    RecommendationContext,
    RecommendationPriority,
    RecommendationResult,
    RecommendationScoreComponents,
    RecommendationScoreResult,
)
from app.services.recommendation_pipeline import (
    run_recommendation_pipeline,
)


def _canonical_result() -> RecommendationResult:
    context = RecommendationContext(
        query="테스트 사과",
        priority=RecommendationPriority.MIX,
        limit=10,
    )

    score = RecommendationScoreResult(
        final_score=80.0,
        priority=RecommendationPriority.MIX,
        components=RecommendationScoreComponents(
            quality=80.0,
            price=80.0,
            trust=80.0,
            popularity=80.0,
            market=80.0,
            identity=80.0,
        ),
        version="canonical-production-test",
    )

    candidate = RecommendationCandidate(
        item={
            "product_name": "테스트 사과",
            "price": 12000,
            "platform": "naver",
            "v7_final_score": 80.0,
        },
        score=score,
        rank=1,
    )

    return RecommendationResult(
        context=context,
        candidates=(candidate,),
        summary="'테스트 사과' 기준 추천 결과",
    )


def test_canonical_provider_executes_once_per_pipeline_request():
    canonical_result = _canonical_result()

    with patch(
        "app.services.recommendation_pipeline."
        "RecommendationProvider"
    ) as provider_cls:
        provider = provider_cls.return_value
        provider.recommend.return_value = (
            canonical_result
        )

        result = run_recommendation_pipeline(
            q="테스트 사과",
            priority="ranking",
            limit=10,
        )

    assert provider_cls.call_count == 1
    assert provider.recommend.call_count == 1

    context = provider.recommend.call_args.args[0]

    assert context.query == "테스트 사과"
    assert context.priority is RecommendationPriority.MIX
    assert context.limit == 10

    assert result["engine_version"] == (
        "recommendation_provider_canonical"
    )
    assert result["summary"] == (
        "'테스트 사과' 기준 추천 결과"
    )
    assert len(result["items"]) == 1
    assert result["items"][0]["rank"] == 1
    assert result["items"][0]["v7_rank"] == 1


def test_pipeline_no_longer_executes_legacy_v8_ranking():
    canonical_result = _canonical_result()

    with (
        patch(
            "app.services.recommendation_pipeline."
            "RecommendationProvider"
        ) as provider_cls,
        patch(
            "app.services.recommendation_pipeline."
            "rank_market_items_v8"
        ) as legacy_rank,
    ):
        provider_cls.return_value.recommend.return_value = (
            canonical_result
        )

        run_recommendation_pipeline(
            q="테스트 사과",
            priority="ranking",
            limit=10,
        )

    legacy_rank.assert_not_called()
