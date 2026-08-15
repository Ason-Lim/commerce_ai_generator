from unittest.mock import patch

from app.services import market_aggregator
from app.services.market import collector


def _run_legacy(
    naver_items: list[dict],
    coupang_items: list[dict],
) -> list[dict]:
    with (
        patch.object(
            market_aggregator,
            "collect_naver_products",
        ),
        patch.object(
            market_aggregator,
            "fetch_naver_products_from_db",
            return_value=naver_items,
        ),
        patch.object(
            market_aggregator,
            "search_coupang_products",
            return_value=coupang_items,
        ),
    ):
        return market_aggregator.collect_market_products(
            "테스트 사과",
            limit=10,
        )


def _run_canonical(
    naver_items: list[dict],
    coupang_items: list[dict],
) -> list[dict]:
    with (
        patch.object(
            collector,
            "collect_naver_products",
        ),
        patch.object(
            collector,
            "fetch_naver_products_from_db",
            return_value=naver_items,
        ),
        patch.object(
            collector,
            "search_coupang_products",
            return_value=coupang_items,
        ),
    ):
        return collector.collect_market_products(
            "테스트 사과",
            limit=10,
        )


def test_legacy_and_canonical_collectors_are_equivalent() -> None:
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

    assert _run_legacy(
        naver_items,
        coupang_items,
    ) == _run_canonical(
        naver_items,
        coupang_items,
    )


def test_legacy_and_canonical_empty_source_contracts_match() -> None:
    assert _run_legacy(
        [],
        [],
    ) == _run_canonical(
        [],
        [],
    )
