from unittest.mock import patch

from app.services.market.collector import (
    collect_market_products,
)


def test_core_collector_combines_sources() -> None:
    naver_items = [
        {
            "product_name": "네이버 테스트 상품",
            "platform": "naver",
            "price": 10000,
        }
    ]

    coupang_items = [
        {
            "product_name": "쿠팡 테스트 상품",
            "platform": "coupang",
            "price": 11000,
        }
    ]

    with (
        patch(
            "app.services.market.collector."
            "collect_naver_products"
        ) as naver_collect_mock,
        patch(
            "app.services.market.collector."
            "fetch_naver_products_from_db",
            return_value=naver_items,
        ) as naver_db_mock,
        patch(
            "app.services.market.collector."
            "search_coupang_products",
            return_value=coupang_items,
        ) as coupang_mock,
    ):
        result = collect_market_products(
            "테스트 사과",
            limit=10,
        )

    naver_collect_mock.assert_called_once_with(
        "테스트 사과"
    )

    naver_db_mock.assert_called_once_with(
        "테스트 사과",
        limit=10,
    )

    coupang_mock.assert_called_once_with(
        "테스트 사과",
        limit=10,
    )

    assert result == [
        *naver_items,
        *coupang_items,
    ]


def test_core_collector_preserves_source_failure_isolation() -> None:
    naver_items = [
        {
            "product_name": "네이버 테스트 상품",
            "platform": "naver",
            "price": 10000,
        }
    ]

    with (
        patch(
            "app.services.market.collector."
            "collect_naver_products"
        ),
        patch(
            "app.services.market.collector."
            "fetch_naver_products_from_db",
            return_value=naver_items,
        ),
        patch(
            "app.services.market.collector."
            "search_coupang_products",
            side_effect=RuntimeError(
                "test coupang failure"
            ),
        ),
    ):
        result = collect_market_products(
            "테스트 사과",
            limit=10,
        )

    assert result == naver_items
