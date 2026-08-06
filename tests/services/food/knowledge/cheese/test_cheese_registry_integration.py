from __future__ import annotations

import pytest

from app.services.food.knowledge.cheese import (
    CheeseKnowledgeProvider,
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


def test_cheese_provider_is_registered() -> None:
    provider = get_food_provider("cheese")

    assert isinstance(
        provider,
        CheeseKnowledgeProvider,
    )
    assert provider.category_id == "cheese"


def test_cheese_provider_is_in_registry() -> None:
    assert "cheese" in FOOD_KNOWLEDGE_REGISTRY

    category_ids = (
        FOOD_KNOWLEDGE_REGISTRY
        .list_category_ids()
    )

    assert "cheese" in category_ids


def test_cheese_provider_registration_order() -> None:
    category_ids = (
        FOOD_KNOWLEDGE_REGISTRY
        .list_category_ids()
    )

    assert category_ids == [
        "fruit",
        "cheese",
        "coffee",
        "wine",
        "tea",
        "olive_oil",
        "herb_spice",
        "venison",
        "goat",
        "beef",
        "lamb",
        "chicken",
        "duck",
    ]


def test_list_food_providers_contains_cheese() -> None:
    providers = list_food_providers()

    cheese_providers = [
        provider
        for provider in providers
        if provider.category_id == "cheese"
    ]

    assert len(cheese_providers) == 1
    assert isinstance(
        cheese_providers[0],
        CheeseKnowledgeProvider,
    )


def test_require_cheese_provider() -> None:
    provider = require_food_provider(
        "cheese"
    )

    assert isinstance(
        provider,
        CheeseKnowledgeProvider,
    )


@pytest.mark.parametrize(
    "category_id",
    [
        "cheese",
        "CHEESE",
        " cheese ",
    ],
)
def test_resolve_provider_by_category_id(
    category_id: str,
) -> None:
    provider = resolve_food_provider(
        category_id=category_id
    )

    assert isinstance(
        provider,
        CheeseKnowledgeProvider,
    )


@pytest.mark.parametrize(
    "category_id",
    [
        "치즈",
        "모차렐라",
        "parmesan",
    ],
)
def test_resolve_provider_by_category_alias(
    category_id: str,
) -> None:
    provider = resolve_food_provider(
        category_id=category_id
    )

    assert isinstance(
        provider,
        CheeseKnowledgeProvider,
    )


@pytest.mark.parametrize(
    "product_name",
    [
        "프랑스 브리 치즈 200g",
        "이탈리아 모짜렐라 치즈",
        "숙성 체다치즈",
        "24개월 숙성 파르미자노 레지아노",
        "blue cheese 150g",
        "plain cream cheese",
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
        CheeseKnowledgeProvider,
    )


@pytest.mark.parametrize(
    ("product_name", "expected_category_id"),
    [
        ("국내산 한우 1++ 등심", "beef"),
        ("프리미엄 도퍼 어린양 프렌치랙", "lamb"),
        ("보어 어린 염소 갈비", "goat"),
        ("훈제오리 슬라이스", "duck"),
        ("토종닭 가슴살", "chicken"),
        ("사슴 안심 스테이크", "venison"),
        ("고당도 사과", "fruit"),
    ],
)
def test_cheese_registration_preserves_existing_routing(
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


def test_resolver_selects_cheese_by_explicit_category() -> None:
    provider = resolve_knowledge_provider(
        {
            "product_name": "프리미엄 유제품",
        },
        category_id="cheese",
    )

    assert isinstance(
        provider,
        CheeseKnowledgeProvider,
    )


def test_resolver_selects_cheese_by_product_name() -> None:
    provider = resolve_knowledge_provider(
        {
            "product_name": (
                "프랑스 브리 치즈 200g"
            ),
        }
    )

    assert isinstance(
        provider,
        CheeseKnowledgeProvider,
    )


def test_analyze_food_product_with_cheese_category() -> None:
    result = analyze_food_product(
        {
            "product_name": (
                "프랑스 산양유 브리 "
                "소프트 치즈 12개월 숙성"
            ),
            "quality_score": 80,
            "price_score": 70,
            "trust_score": 90,
        },
        category_id="cheese",
        strict=True,
    )

    assert result is not None
    assert result.category_id == "cheese"
    assert result.attributes[
        "cheese_type"
    ] == "브리"
    assert result.final_score == 86.3


def test_resolve_food_knowledge_auto_selects_cheese() -> None:
    result = resolve_food_knowledge(
        {
            "product_name": (
                "24개월 숙성 "
                "파르미자노 레지아노"
            ),
            "quality_score": 80,
            "price_score": 70,
            "trust_score": 90,
        },
        strict=True,
    )

    assert result is not None
    assert result.category_id == "cheese"
    assert result.attributes[
        "cheese_type"
    ] == "파르미자노 레지아노"
    assert result.attributes[
        "aging"
    ] == "초장기숙성"
    assert result.final_score == 88.2


def test_unknown_product_still_returns_none() -> None:
    provider = resolve_food_provider(
        product_name=(
            "분류할 수 없는 일반 상품"
        )
    )

    assert provider is None


def test_duplicate_cheese_registration_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match=(
            "이미 등록된 Food Provider"
        ),
    ):
        FOOD_KNOWLEDGE_REGISTRY.register(
            CheeseKnowledgeProvider()
        )
