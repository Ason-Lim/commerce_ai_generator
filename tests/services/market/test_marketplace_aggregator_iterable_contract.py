from app.services.market.aggregator import (
    aggregate_market_items,
)


def _generator():
    yield {
        "title": "테스트 사과 A",
        "lprice": "12000",
        "mallName": "네이버쇼핑",
    }

    yield {
        "title": "테스트 사과 B",
        "lprice": "13000",
        "mallName": "쿠팡",
    }


def test_aggregator_preserves_generator_raw_count() -> None:
    result = aggregate_market_items(
        _generator()
    )

    statistics = result["statistics"]

    assert statistics["raw_item_count"] == 2
    assert statistics["normalized_item_count"] == 2
    assert statistics["group_count"] == 2
    assert statistics["platform_count"] == 2

    assert statistics[
        "platform_distribution"
    ] == {
        "naver": 1,
        "coupang": 1,
    }


def test_list_and_generator_statistics_match() -> None:
    items = [
        {
            "title": "테스트 사과 A",
            "lprice": "12000",
            "mallName": "네이버쇼핑",
        },
        {
            "title": "테스트 사과 B",
            "lprice": "13000",
            "mallName": "쿠팡",
        },
    ]

    list_result = aggregate_market_items(
        items
    )

    generator_result = aggregate_market_items(
        iter(items)
    )

    assert (
        list_result["statistics"]
        == generator_result["statistics"]
    )
