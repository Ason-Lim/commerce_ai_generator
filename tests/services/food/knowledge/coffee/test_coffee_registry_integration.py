from __future__ import annotations

import pytest

from app.services.food.category_registry import (
    get_food_category,
    resolve_food_category,
)
from app.services.food.knowledge.coffee import (
    CoffeeKnowledgeProvider,
)
from app.services.food.knowledge.registry import (
    FOOD_KNOWLEDGE_REGISTRY,
    get_food_provider,
    list_food_providers,
    require_food_provider,
    resolve_food_provider,
)
from app.services.food.resolver import (
    analyze_food_product,
    resolve_food_knowledge,
    resolve_knowledge_provider,
)


def test_coffee_provider_is_registered() -> None:
    provider = get_food_provider("coffee")

    assert isinstance(
        provider,
        CoffeeKnowledgeProvider,
    )
    assert provider.category_id == "coffee"


def test_coffee_provider_is_registered_once() -> None:
    providers = [
        provider
        for provider in list_food_providers()
        if provider.category_id == "coffee"
    ]

    assert len(providers) == 1


def test_coffee_provider_is_in_registry() -> None:
    assert "coffee" in FOOD_KNOWLEDGE_REGISTRY

    assert "coffee" in (
        FOOD_KNOWLEDGE_REGISTRY
        .list_category_ids()
    )


def test_provider_registration_order() -> None:
    category_ids = (
        FOOD_KNOWLEDGE_REGISTRY
        .list_category_ids()
    )

    assert category_ids == [
        "fruit",
        "cheese",
        "coffee",
        "venison",
        "goat",
        "beef",
        "lamb",
        "chicken",
        "duck",
    ]


def test_require_coffee_provider() -> None:
    provider = require_food_provider(
        "coffee"
    )

    assert isinstance(
        provider,
        CoffeeKnowledgeProvider,
    )


@pytest.mark.parametrize(
    "category_id",
    [
        "coffee",
        "COFFEE",
        " coffee ",
        "커피",
        "원두",
        "아라비카",
        "arabica",
    ],
)
def test_resolve_provider_by_category(
    category_id: str,
) -> None:
    provider = resolve_food_provider(
        category_id=category_id
    )

    assert isinstance(
        provider,
        CoffeeKnowledgeProvider,
    )


@pytest.mark.parametrize(
    "product_name",
    [
        "에티오피아 아라비카 원두 200g",
        "프리미엄 커피 500g",
        "100% Arabica Coffee",
        "콜드브루 커피",
        "디카페인 커피 원두",
        "에스프레소 블렌드",
    ],
)
def test_resolve_provider_by_product_name(
    product_name: str,
) -> None:
    provider = resolve_food_provider(
        product_name=product_name
    )

    assert isinstance(
        provider,
        CoffeeKnowledgeProvider,
    )


@pytest.mark.parametrize(
    ("product_name", "expected_category_id"),
    [
        ("프랑스 브리 치즈 200g", "cheese"),
        ("국내산 한우 1++ 등심", "beef"),
        ("프리미엄 도퍼 어린양 프렌치랙", "lamb"),
        ("보어 어린 염소 갈비", "goat"),
        ("훈제오리 슬라이스", "duck"),
        ("토종닭 가슴살", "chicken"),
        ("사슴 안심 스테이크", "venison"),
        ("고당도 사과", "fruit"),
    ],
)
def test_coffee_registration_preserves_existing_routing(
    product_name: str,
    expected_category_id: str,
) -> None:
    provider = resolve_food_provider(
        product_name=product_name
    )

    assert provider is not None
    assert (
        provider.category_id
        == expected_category_id
    )


def test_coffee_category_is_registered() -> None:
    category = get_food_category(
        "coffee"
    )

    assert category is not None
    assert category.category_id == "coffee"
    assert category.display_name == "커피"
    assert category.provider_id == "coffee"
    assert category.parent_category_id is None


@pytest.mark.parametrize(
    "category_id",
    [
        "coffee",
        "COFFEE",
        "커피",
        "원두",
    ],
)
def test_resolve_coffee_category_by_id_or_alias(
    category_id: str,
) -> None:
    category = resolve_food_category(
        category_id=category_id
    )

    assert category is not None
    assert category.category_id == "coffee"


def test_resolve_coffee_category_by_product_name() -> None:
    category = resolve_food_category(
        product_name=(
            "에티오피아 아라비카 원두 200g"
        )
    )

    assert category is not None
    assert category.category_id == "coffee"


def test_resolver_selects_coffee_by_explicit_category() -> None:
    provider = resolve_knowledge_provider(
        {
            "product_name": "프리미엄 식품",
        },
        category_id="coffee",
    )

    assert isinstance(
        provider,
        CoffeeKnowledgeProvider,
    )


def test_resolver_selects_coffee_by_product_name() -> None:
    provider = resolve_knowledge_provider(
        {
            "product_name": (
                "에티오피아 아라비카 원두 200g"
            ),
        }
    )

    assert isinstance(
        provider,
        CoffeeKnowledgeProvider,
    )


def test_analyze_food_product_with_coffee_category() -> None:
    result = analyze_food_product(
        {
            "product_name": (
                "에티오피아 100% 아라비카 "
                "라이트 로스트 워시드 원두"
            ),
            "quality_score": 80,
            "price_score": 70,
            "trust_score": 90,
        },
        category_id="coffee",
        strict=True,
    )

    assert result is not None
    assert result.category_id == "coffee"
    assert result.attributes["bean"] == (
        "아라비카"
    )
    assert result.attributes["origin"] == (
        "에티오피아"
    )
    assert result.attributes["roast"] == (
        "라이트 로스트"
    )
    assert result.attributes["process"] == (
        "워시드"
    )
    assert result.scores["knowledge"] == (
        92.55
    )
    assert result.final_score == 86.28


def test_resolve_food_knowledge_auto_selects_coffee() -> None:
    result = resolve_food_knowledge(
        {
            "product_name": (
                "에티오피아 100% 아라비카 "
                "라이트 로스트 워시드 원두"
            ),
            "quality_score": 80,
            "price_score": 70,
            "trust_score": 90,
        },
        strict=True,
    )

    assert result is not None
    assert result.category_id == "coffee"
    assert result.metadata[
        "provider_id"
    ] == "coffee"


def test_unknown_product_still_returns_none() -> None:
    provider = resolve_food_provider(
        product_name=(
            "분류할 수 없는 일반 상품"
        )
    )

    assert provider is None


def test_provider_ids_remain_unique() -> None:
    category_ids = [
        provider.category_id
        for provider in list_food_providers()
    ]

    assert len(category_ids) == len(
        set(category_ids)
    )


def test_duplicate_coffee_registration_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match=(
            "이미 등록된 Food Provider"
        ),
    ):
        FOOD_KNOWLEDGE_REGISTRY.register(
            CoffeeKnowledgeProvider()
        )
