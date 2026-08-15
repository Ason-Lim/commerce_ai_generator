from app.services.market.deduplicator import (
    deduplicate_market_items,
)


def test_same_platform_offers_count_as_one_platform() -> None:
    items = [
        {
            "platform": "naver",
            "product_name": "청송 사과 5kg",
            "price": 30000,
        },
        {
            "platform": "naver",
            "product_name": "청송 사과 5kg",
            "price": 31000,
        },
    ]

    result = deduplicate_market_items(items)

    assert len(result) == 1

    group = result[0]

    assert group["platform_count"] == 1
    assert group["item_count"] == 2
    assert len(group["items"]) == 2


def test_cross_platform_offers_count_distinct_platforms() -> None:
    items = [
        {
            "platform": "naver",
            "product_name": "청송 사과 5kg",
            "price": 30000,
        },
        {
            "platform": "coupang",
            "product_name": "청송 사과 5kg",
            "price": 31000,
        },
    ]

    result = deduplicate_market_items(items)

    assert len(result) == 1

    group = result[0]

    assert group["platform_count"] == 2
    assert group["item_count"] == 2


def test_repeated_platforms_preserve_offer_count() -> None:
    items = [
        {
            "platform": "naver",
            "product_name": "청송 사과 5kg",
            "price": 30000,
        },
        {
            "platform": "naver",
            "product_name": "청송 사과 5kg",
            "price": 31000,
        },
        {
            "platform": "coupang",
            "product_name": "청송 사과 5kg",
            "price": 32000,
        },
    ]

    result = deduplicate_market_items(items)

    group = result[0]

    assert group["platform_count"] == 2
    assert group["item_count"] == 3
    assert len(group["items"]) == 3
