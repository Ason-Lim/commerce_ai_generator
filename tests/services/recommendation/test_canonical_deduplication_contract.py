from app.services.recommendation.deduplication import (
    build_identity_key,
    deduplicate_market_items,
    normalize_name,
)


def test_promotion_noise_is_removed():
    assert normalize_name(
        "[특가] 청송 사과 5kg 무료배송"
    ) == "청송 사과 5kg"


def test_exact_name_duplicate_uses_lower_price():
    items = [
        {
            "platform": "naver",
            "product_name": "청송 사과 5kg",
            "price": 30000,
        },
        {
            "platform": "coupang",
            "product_name": "청송 사과 5kg",
            "price": 29000,
        },
    ]

    result = deduplicate_market_items(items)

    assert len(result) == 1
    assert result[0]["price"] == 29000


def test_promotion_noise_duplicate_collapses():
    items = [
        {
            "platform": "naver",
            "product_name": (
                "[특가] 청송 사과 5kg 무료배송"
            ),
            "price": 30000,
        },
        {
            "platform": "naver",
            "product_name": "청송 사과 5kg",
            "price": 29000,
        },
    ]

    result = deduplicate_market_items(items)

    assert len(result) == 1
    assert result[0]["price"] == 29000


def test_cross_platform_exact_name_collapses():
    items = [
        {
            "platform": "naver",
            "mall_name": "seller-a",
            "product_name": "제주 감귤 3kg",
            "price": 20000,
        },
        {
            "platform": "coupang",
            "mall_name": "seller-b",
            "product_name": "제주 감귤 3kg",
            "price": 21000,
        },
    ]

    result = deduplicate_market_items(items)

    assert len(result) == 1
    assert result[0]["price"] == 20000


def test_explicit_identity_key_collapses_different_names():
    items = [
        {
            "platform": "naver",
            "product_name": "상품 A",
            "product_identity_key": "canonical-1",
            "price": 20000,
        },
        {
            "platform": "coupang",
            "product_name": "완전히 다른 표시명",
            "product_identity_key": "canonical-1",
            "price": 19000,
        },
    ]

    result = deduplicate_market_items(items)

    assert len(result) == 1
    assert result[0]["price"] == 19000


def test_explicit_identity_precedes_fallback_identity():
    item = {
        "platform": "naver",
        "mall_name": "seller-a",
        "product_name": "상품 A",
        "product_identity_key": "canonical-1",
    }

    assert build_identity_key(item) == (
        "identity:canonical-1"
    )


def test_legacy_ranking_scores_do_not_choose_representative():
    items = [
        {
            "platform": "naver",
            "product_name": "테스트 상품",
            "price": 10000,
            "v8_final_score": 80,
            "v7_final_score": 90,
            "platform_boost_score": 99,
        },
        {
            "platform": "naver",
            "product_name": "테스트 상품",
            "price": 9000,
            "v8_final_score": 1,
            "v7_final_score": 1,
            "platform_boost_score": 1,
        },
    ]

    result = deduplicate_market_items(items)

    assert len(result) == 1
    assert result[0]["price"] == 9000


def test_equal_price_preserves_first_candidate():
    first = {
        "platform": "naver",
        "product_name": "동일 상품",
        "price": 10000,
    }
    second = {
        "platform": "coupang",
        "product_name": "동일 상품",
        "price": 10000,
    }

    result = deduplicate_market_items(
        [first, second]
    )

    assert result == [first]


def test_non_dict_input_is_ignored():
    items = [
        {
            "product_name": "상품 A",
            "price": 10000,
        },
        None,
        "invalid",
    ]

    result = deduplicate_market_items(items)

    assert len(result) == 1
    assert result[0]["product_name"] == "상품 A"
