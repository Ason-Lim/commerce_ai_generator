from app.services.recommendation.models import (
    RecommendationCandidate,
    RecommendationContext,
    RecommendationPriority,
    RecommendationResult,
    RecommendationScoreComponents,
    RecommendationScoreResult,
)
from app.services.recommendation_pipeline import (
    build_canonical_context,
    canonical_result_to_compatibility_response,
    resolve_canonical_priority,
)


def _score_result(
    score: float = 88.0,
) -> RecommendationScoreResult:
    return RecommendationScoreResult(
        final_score=score,
        priority=RecommendationPriority.MIX,
        components=RecommendationScoreComponents(
            quality=90.0,
            price=80.0,
            trust=85.0,
            popularity=70.0,
            market=75.0,
            identity=95.0,
        ),
        version="canonical-test",
    )


def test_resolve_ranking_to_mix():
    priority, adaptive = resolve_canonical_priority(
        "ranking"
    )

    assert priority is RecommendationPriority.MIX
    assert adaptive is False


def test_resolve_value_to_price():
    priority, adaptive = resolve_canonical_priority(
        "value"
    )

    assert priority is RecommendationPriority.PRICE
    assert adaptive is False


def test_resolve_adaptive_priority():
    priority, adaptive = resolve_canonical_priority(
        "quality_adaptive"
    )

    assert priority is RecommendationPriority.QUALITY
    assert adaptive is True


def test_unknown_priority_falls_back_to_mix():
    priority, adaptive = resolve_canonical_priority(
        "unknown-mode"
    )

    assert priority is RecommendationPriority.MIX
    assert adaptive is False


def test_build_canonical_context_preserves_request_metadata():
    context = build_canonical_context(
        q="가성비 좋은 사과 추천",
        priority="value_adaptive",
        session_id="session-001",
        limit=10,
    )

    assert context.query == "사과"
    assert context.priority is RecommendationPriority.PRICE
    assert context.adaptive is True
    assert context.session_id == "session-001"
    assert context.limit == 10
    assert (
        context.metadata["requested_query"]
        == "가성비 좋은 사과 추천"
    )
    assert (
        context.metadata["requested_priority"]
        == "value_adaptive"
    )


def test_canonical_result_to_compatibility_response_preserves_contract():
    context = RecommendationContext(
        query="사과",
        priority=RecommendationPriority.MIX,
        limit=10,
    )

    candidate = RecommendationCandidate(
        item={
            "product_name": "테스트 사과",
            "seller_name": "테스트몰",
            "price": 10000,
            "v7_final_score": 88.0,
            "v7_quality_score": 90.0,
            "v7_price_score": 80.0,
            "v7_platform_score": 85.0,
        },
        score=_score_result(),
        rank=1,
    )

    result = RecommendationResult(
        context=context,
        candidates=(candidate,),
        summary="canonical summary",
    )

    response = (
        canonical_result_to_compatibility_response(
            result,
            q="사과",
            priority="ranking",
        )
    )

    assert response["summary"] == "canonical summary"
    assert (
        response["engine_version"]
        == "recommendation_provider_canonical"
    )
    assert response["market_sources"] == [
        "naver",
        "coupang",
    ]

    assert len(response["items"]) == 1

    item = response["items"][0]

    assert item["product_name"] == "테스트 사과"
    assert item["seller_name"] == "테스트몰"
    assert item["rank"] == 1
    assert item["v7_rank"] == 1
    assert item["query"] == "사과"
    assert item["selected_priority"] == "ranking"
    assert item["recommendation_mode"] == "ranking"


def test_adapter_preserves_canonical_rank():
    context = RecommendationContext(
        query="사과",
        priority=RecommendationPriority.MIX,
    )

    candidates = tuple(
        RecommendationCandidate(
            item={
                "product_name": f"상품 {rank}",
                "v7_final_score": 90 - rank,
            },
            score=_score_result(
                90 - rank
            ),
            rank=rank,
        )
        for rank in (1, 2, 3)
    )

    result = RecommendationResult(
        context=context,
        candidates=candidates,
        summary="summary",
    )

    response = (
        canonical_result_to_compatibility_response(
            result,
            q="사과",
            priority="ranking",
        )
    )

    assert [
        item["rank"]
        for item in response["items"]
    ] == [1, 2, 3]

    assert [
        item["v7_rank"]
        for item in response["items"]
    ] == [1, 2, 3]


def test_adapter_exposes_warnings_when_present():
    result = RecommendationResult(
        context=RecommendationContext(
            query="사과",
        ),
        summary="summary",
        warnings=(
            "market_unavailable",
            "identity_unavailable",
        ),
    )

    response = (
        canonical_result_to_compatibility_response(
            result,
            q="사과",
            priority="ranking",
        )
    )

    assert response["warnings"] == [
        "market_unavailable",
        "identity_unavailable",
    ]


def test_empty_result_preserves_empty_items_contract():
    result = RecommendationResult(
        context=RecommendationContext(
            query="사과",
        ),
        summary="추천 가능한 상품을 찾지 못했습니다.",
    )

    response = (
        canonical_result_to_compatibility_response(
            result,
            q="사과",
            priority="ranking",
        )
    )

    assert response["items"] == []
    assert (
        response["summary"]
        == "추천 가능한 상품을 찾지 못했습니다."
    )
