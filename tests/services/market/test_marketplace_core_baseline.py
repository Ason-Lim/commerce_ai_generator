from app.services.market.aggregator import (
    aggregate_market_items,
)
from app.services.market.deduplicator import (
    deduplicate_market_items,
)
from app.services.market.delivery_policy import (
    build_platform_delivery_policy,
)
from app.services.market.normalizer import (
    normalize_market_item,
)
from app.services.market.partner_market_adapter import (
    extract_partner_market_items,
)
from app.services.market.platform_matcher import (
    detect_platform_from_item,
    detect_platform_from_mall_name,
)
from app.services.market.registry import (
    get_enabled_platform_ids,
    list_platform_configs,
)


def test_platform_registry_baseline() -> None:
    configs = list_platform_configs()

    platform_ids = {
        config.id
        for config in configs
    }

    assert platform_ids == {
        "naver",
        "coupang",
        "ssg",
        "oasis",
        "kurly",
        "lotte_mart",
        "gs_shop",
        "cj_onstyle",
    }

    assert set(get_enabled_platform_ids()) == {
        "naver",
        "coupang",
        "ssg",
        "oasis",
    }


def test_platform_alias_matching_baseline() -> None:
    cases = [
        ("네이버쇼핑", "naver"),
        ("쿠팡", "coupang"),
        ("SSG닷컴", "ssg"),
        ("오아시스마켓", "oasis"),
    ]

    for value, expected in cases:
        assert (
            detect_platform_from_mall_name(value)
            == expected
        )


def test_platform_url_matching_baseline() -> None:
    cases = [
        (
            {
                "product_url":
                "https://www.coupang.com/vp/products/1"
            },
            "coupang",
        ),
        (
            {
                "product_url":
                "https://emart.ssg.com/item/itemView.ssg"
            },
            "ssg",
        ),
    ]

    for item, expected in cases:
        assert (
            detect_platform_from_item(item)
            == expected
        )


def test_unknown_platform_matching_baseline() -> None:
    assert (
        detect_platform_from_mall_name(
            "알수없는테스트몰"
        )
        is None
    )

    assert (
        detect_platform_from_item(
            {
                "product_url":
                "https://example.invalid/product/1"
            }
        )
        is None
    )


def test_market_item_normalization_baseline() -> None:
    item = normalize_market_item(
        {
            "title": "<b>테스트 사과</b>",
            "lprice": "12,900",
            "hprice": "15,000",
            "mallName": "네이버쇼핑",
            "link": "https://shopping.naver.com/test",
        }
    )

    assert item["platform"] == "naver"
    assert item["product_name"] == "테스트 사과"
    assert item["price"] == 12900
    assert item["original_price"] == 15000
    assert item["discount_rate"] == 14.0
    assert item["mall_name"] == "네이버쇼핑"
    assert (
        item["product_url"]
        == "https://shopping.naver.com/test"
    )


def test_partner_market_adapter_baseline() -> None:
    items = [
        {
            "title": "SSG 테스트 상품",
            "mallName": "SSG.COM",
            "lprice": "10000",
            "link": "https://www.ssg.com/item/test",
        },
        {
            "title": "일반 네이버 상품",
            "mallName": "기타판매처",
            "lprice": "9000",
        },
    ]

    result = extract_partner_market_items(
        items,
        target_platform="ssg",
    )

    assert len(result) == 1

    item = result[0]

    assert item["platform"] == "ssg"
    assert item["product_name"] == "SSG 테스트 상품"
    assert item["price"] == 10000


def test_delivery_policy_baseline() -> None:
    naver = build_platform_delivery_policy(
        "naver"
    )
    coupang = build_platform_delivery_policy(
        "coupang"
    )
    ssg = build_platform_delivery_policy(
        "ssg"
    )
    oasis = build_platform_delivery_policy(
        "oasis"
    )

    assert naver["delivery_type"] == [
        "parcel"
    ]

    assert coupang["delivery_type"] == [
        "dawn",
        "same_day",
        "parcel",
    ]

    assert ssg["delivery_type"] == [
        "dawn",
        "same_day",
        "scheduled",
        "parcel",
        "pickup",
    ]

    assert oasis["delivery_type"] == [
        "dawn",
        "parcel",
    ]

    assert (
        ssg["delivery_requires_address_check"]
        is True
    )

    assert (
        oasis["delivery_requires_address_check"]
        is True
    )


def test_marketplace_deduplication_baseline() -> None:
    items = [
        {
            "platform": "naver",
            "product_name": "청송 사과 5kg",
            "price": 30000,
        },
        {
            "platform": "naver",
            "product_name": "청송 사과 5kg",
            "price": 30000,
        },
    ]

    result = deduplicate_market_items(items)

    assert len(result) == 1

    group = result[0]

    assert group["canonical_name"] == "청송 사과 5kg"
    assert group["lowest_price"] == 30000
    assert len(group["items"]) == 2

    # AO-MARKETPLACE-005 canonical contract:
    #
    # platform_count represents the number of distinct
    # non-empty platforms in the deduplication group.
    # item_count preserves the number of grouped offers.
    assert group["platform_count"] == 1
    assert group["item_count"] == 2


def test_marketplace_aggregation_baseline() -> None:
    raw_items = [
        {
            "title": "테스트 사과",
            "lprice": "12000",
            "mallName": "네이버쇼핑",
        },
        {
            "title": "테스트 사과",
            "lprice": "12000",
            "mallName": "네이버쇼핑",
        },
    ]

    result = aggregate_market_items(
        raw_items
    )

    assert (
        result["statistics"]
        == {
            "raw_item_count": 2,
            "normalized_item_count": 2,
            "group_count": 1,
            "platform_count": 1,
            "platform_distribution": {
                "naver": 2,
            },
        }
    )

    assert len(
        result["normalized_items"]
    ) == 2

    assert len(
        result["grouped_items"]
    ) == 1
