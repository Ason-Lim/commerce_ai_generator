from copy import deepcopy

from app.services.recommendation.platform_normalization import (
    normalize_platform_item,
    normalize_platform_items,
)
from app.services.recommendation.provider import (
    normalize_platform_items as provider_normalizer,
)


def test_provider_resolves_canonical_normalizer():
    assert provider_normalizer is normalize_platform_items


def test_normalization_does_not_mutate_source():
    source = {
        "platform": "naver",
        "mall_name": "판매자A",
        "product_name": "사과 A",
        "price": 10000,
    }
    before = deepcopy(source)

    result = normalize_platform_item(source)

    assert source == before
    assert result is not source


def test_naver_presentation_contract():
    result = normalize_platform_item(
        {
            "platform": "naver",
            "mall_name": "판매자A",
        }
    )

    assert result["platform"] == "naver"
    assert result["seller_name"] == "판매자A"
    assert (
        result["platform_name"]
        == "네이버쇼핑 · 판매자A"
    )
    assert (
        result["display_market"]
        == "네이버쇼핑 · 판매자A"
    )
    assert result["platform_label"] == "네이버쇼핑"
    assert result["is_coupang"] is False
    assert result["is_ad"] is False
    assert result["platform_notice"] == ""


def test_coupang_compatibility_contract():
    result = normalize_platform_item(
        {
            "platform": "coupang",
            "mall_name": "쿠팡",
        }
    )

    assert result["platform"] == "coupang"
    assert result["seller_name"] == "쿠팡"
    assert result["platform_name"] == "쿠팡"
    assert result["display_market"] == "쿠팡"
    assert result["platform_label"] == "쿠팡"
    assert result["is_coupang"] is True
    assert result["is_ad"] is True
    assert result["platform_notice"]


def test_existing_coupang_notice_is_preserved():
    notice = "custom disclosure"

    result = normalize_platform_item(
        {
            "platform": "coupang",
            "platform_notice": notice,
        }
    )

    assert result["platform_notice"] == notice


def test_partner_notice_fallback_is_preserved():
    notice = "partner disclosure"

    result = normalize_platform_item(
        {
            "platform": "coupang",
            "partner_notice": notice,
        }
    )

    assert result["platform_notice"] == notice


def test_unknown_platform_contract():
    result = normalize_platform_item(
        {
            "platform": "unknown-shop",
            "mall_name": "기타몰",
        }
    )

    assert result["platform"] == "unknown-shop"
    assert result["seller_name"] == "기타몰"
    assert result["platform_name"] == "기타몰"
    assert result["display_market"] == "기타몰"
    assert result["platform_label"] == "unknown-shop"
    assert result["is_coupang"] is False


def test_non_dict_items_are_filtered():
    result = normalize_platform_items(
        [
            {"platform": "naver"},
            None,
            "invalid",
            123,
        ]
    )

    assert len(result) == 1
    assert result[0]["platform"] == "naver"
