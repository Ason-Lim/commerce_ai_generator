from types import SimpleNamespace

import app.services.generator_service as generator


def make_request(
    *,
    context="가성비 좋은 사과 추천",
    mode="B2C",
    priority="price",
    quantity=None,
):
    return SimpleNamespace(
        context=context,
        mode=mode,
        priority=priority,
        quantity=quantity,
    )


def raw_product(
    *,
    name,
    price,
    weight_g=1000,
    platform="네이버",
    mall_name=None,
    rating=4.5,
    review_count=100,
    brix_value=None,
    premium_flag=False,
    gift_flag=False,
):
    return {
        "name": name,
        "price": price,
        "original_price": price,
        "weight_g": weight_g,
        "platform": platform,
        "mall_name": mall_name,
        "rating": rating,
        "review_count": review_count,
        "brix_value": brix_value,
        "premium_flag": premium_flag,
        "gift_flag": gift_flag,
        "description": "",
    }


def patch_runtime(
    monkeypatch,
    products,
    *,
    normalized_keyword="사과",
):
    monkeypatch.setattr(
        generator,
        "analyze_user_query",
        lambda context: {
            "normalized_keyword": normalized_keyword,
            "raw_query": context,
        },
    )

    monkeypatch.setattr(
        generator,
        "fetch_products_from_db",
        lambda keyword: products,
    )


def test_generate_product_strategy_preserves_response_contract(
    monkeypatch,
):
    products = [
        raw_product(
            name="프리미엄 사과 1kg",
            price=12000,
            brix_value=14,
            premium_flag=True,
            review_count=500,
        ),
        raw_product(
            name="실속 사과 1kg",
            price=8000,
            brix_value=11,
            review_count=200,
        ),
        raw_product(
            name="가정용 사과 1kg",
            price=9000,
            brix_value=12,
            review_count=100,
        ),
    ]

    patch_runtime(monkeypatch, products)

    result = generator.generate_product_strategy(
        make_request()
    )

    assert result is not None

    assert set(result) == {
        "query",
        "search_keyword",
        "intent",
        "mode",
        "priority",
        "summary",
        "top3",
        "best_price",
        "best_quality",
        "products",
    }

    assert result["query"] == "가성비 좋은 사과 추천"
    assert result["search_keyword"] == "사과"
    assert result["mode"] == "B2C"
    assert result["priority"] == "price"

    assert len(result["top3"]) == 3
    assert len(result["products"]) == 3

    assert result["best_price"] is not None
    assert result["best_quality"] is not None


def test_generate_product_strategy_ranks_by_legacy_score(
    monkeypatch,
):
    products = [
        raw_product(
            name="비싼 사과",
            price=20000,
            brix_value=12,
        ),
        raw_product(
            name="저렴한 사과",
            price=5000,
            brix_value=12,
        ),
    ]

    patch_runtime(monkeypatch, products)

    result = generator.generate_product_strategy(
        make_request(priority="price")
    )

    assert result is not None

    scores = [
        product["score"]
        for product in result["products"]
    ]

    assert scores == sorted(
        scores,
        reverse=True,
    )

    assert result["products"][0]["name"] == "저렴한 사과"


def test_generate_product_strategy_deduplicates_name_and_price(
    monkeypatch,
):
    duplicate = raw_product(
        name="중복 사과",
        price=10000,
        brix_value=12,
    )

    products = [
        duplicate,
        dict(duplicate),
        raw_product(
            name="다른 사과",
            price=11000,
            brix_value=13,
        ),
    ]

    patch_runtime(monkeypatch, products)

    result = generator.generate_product_strategy(
        make_request()
    )

    assert result is not None
    assert len(result["products"]) == 2


def test_generate_product_strategy_adds_b2b_strategy_to_top3(
    monkeypatch,
):
    products = [
        raw_product(
            name="B2B 사과 A",
            price=10000,
        ),
        raw_product(
            name="B2B 사과 B",
            price=11000,
        ),
    ]

    patch_runtime(monkeypatch, products)

    result = generator.generate_product_strategy(
        make_request(
            mode="B2B",
            quantity=100,
        )
    )

    assert result is not None

    for product in result["top3"]:
        assert "b2b_strategy" in product
        assert (
            product["b2b_strategy"]["quantity"]
            == 100
        )


def test_generate_product_strategy_empty_products_returns_none(
    monkeypatch,
):
    patch_runtime(
        monkeypatch,
        [],
    )

    result = generator.generate_product_strategy(
        make_request()
    )

    # Characterization:
    # The legacy implementation currently places its
    # response return inside `if best_quality:`.
    #
    # Therefore an empty product set produces an
    # implicit None return.
    #
    # This test intentionally freezes the existing
    # behavior. It is NOT an endorsement of the
    # behavior as the future canonical contract.
    assert result is None


def test_best_price_falls_back_to_raw_price():
    products = [
        {
            "name": "A",
            "price": 12000,
            "price_per_100g": None,
        },
        {
            "name": "B",
            "price": 9000,
            "price_per_100g": None,
        },
    ]

    result = generator.find_best_price_product(
        products
    )

    assert result["name"] == "B"


def test_best_quality_uses_review_count_as_tiebreaker():
    products = [
        {
            "name": "A",
            "quality_score": 80,
            "review_count": 100,
        },
        {
            "name": "B",
            "quality_score": 80,
            "review_count": 500,
        },
    ]

    result = generator.find_best_quality_product(
        products
    )

    assert result["name"] == "B"


def test_safe_price_per_100g_preserves_legacy_guardrails():
    assert (
        generator.safe_price_per_100g(
            10000,
            1000,
        )
        == 1000
    )

    assert (
        generator.safe_price_per_100g(
            10000,
            None,
        )
        is None
    )

    assert (
        generator.safe_price_per_100g(
            10000,
            0,
        )
        is None
    )

    assert (
        generator.safe_price_per_100g(
            10000,
            5,
        )
        is None
    )

    assert (
        generator.safe_price_per_100g(
            "invalid",
            1000,
        )
        is None
    )
