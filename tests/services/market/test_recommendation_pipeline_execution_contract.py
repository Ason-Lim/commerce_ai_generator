from unittest.mock import patch

from app.services.recommendation_pipeline import (
    run_recommendation_pipeline,
)


def test_ranking_executes_once_per_pipeline_request() -> None:
    market_items = [
        {
            "product_name": "테스트 사과",
            "price": 12000,
            "platform": "naver",
        }
    ]

    ranked_items = [
        {
            "product_name": "테스트 사과",
            "price": 12000,
            "platform": "naver",
            "v7_final_score": 80,
        }
    ]

    with (
        patch(
            "app.services.recommendation_pipeline."
            "collect_market_products",
            return_value=market_items,
        ),
        patch(
            "app.services.recommendation_pipeline."
            "deduplicate_market_items",
            side_effect=lambda items: items,
        ),
        patch(
            "app.services.recommendation_pipeline."
            "normalize_platform_items",
            side_effect=lambda items: items,
        ),
        patch(
            "app.services.recommendation_pipeline."
            "enrich_items_with_food_intelligence",
            side_effect=lambda items: items,
        ),
        patch(
            "app.services.recommendation_pipeline."
            "rank_market_items_v8",
            return_value=ranked_items,
        ) as rank_mock,
    ):
        result = run_recommendation_pipeline(
            q="테스트 사과",
            priority="ranking",
            limit=10,
        )

    assert rank_mock.call_count == 1
    assert len(result["items"]) == 1
    assert result["items"][0]["rank"] == 1
