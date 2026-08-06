from __future__ import annotations

import pytest

from app.services.food.category_registry import (
    get_food_category,
    resolve_food_category,
)
from app.services.food.knowledge.herb_spice.provider import (
    HerbSpiceKnowledgeProvider,
)
from app.services.food.knowledge.registry import (
    FOOD_KNOWLEDGE_REGISTRY,
    get_food_provider,
    require_food_provider,
    resolve_food_provider,
)


def test_herb_spice_provider_is_registered() -> None:
    provider = get_food_provider(
        "herb_spice"
    )

    assert isinstance(
        provider,
        HerbSpiceKnowledgeProvider,
    )
    assert (
        require_food_provider(
            "herb_spice"
        )
        is provider
    )


def test_default_provider_order() -> None:
    assert (
        FOOD_KNOWLEDGE_REGISTRY
        .list_category_ids()
    ) == [
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


@pytest.mark.parametrize(
    (
        "product_name",
        "expected_category_id",
    ),
    [
        (
            "프랑스산 건조 로즈마리",
            "herb_spice",
        ),
        (
            "인도산 큐민 파우더",
            "herb_spice",
        ),
        (
            "베트남 통후추",
            "herb_spice",
        ),
        (
            "Cinnamon Bark",
            "herb_spice",
        ),
        (
            "Cardamom Pod",
            "herb_spice",
        ),
    ],
)
def test_provider_auto_selection(
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


@pytest.mark.parametrize(
    "product_name",
    [
        "양조 간장 500ml",
        "사과 식초",
        "전통 된장",
        "고추장 1kg",
        "와사비 소스",
        "튜브 와사비 페이스트",
        "페퍼민트 허브티",
        "Herbal Infusion Tea",
    ],
)
def test_provider_preserves_domain_boundary(
    product_name: str,
) -> None:
    provider = resolve_food_provider(
        product_name=product_name
    )

    assert (
        provider is None
        or provider.category_id
        != "herb_spice"
    )


def test_category_is_registered() -> None:
    category = get_food_category(
        "herb_spice"
    )

    assert category is not None
    assert category.category_id == (
        "herb_spice"
    )
    assert category.display_name == (
        "허브·향신료"
    )
    assert category.provider_id == (
        "herb_spice"
    )


@pytest.mark.parametrize(
    "product_name",
    [
        "프랑스산 건조 로즈마리",
        "인도산 큐민 파우더",
        "Cinnamon Bark",
        "Cardamom Pod",
    ],
)
def test_category_auto_selection(
    product_name: str,
) -> None:
    category = resolve_food_category(
        product_name=product_name
    )

    assert category is not None
    assert category.category_id == (
        "herb_spice"
    )


def test_explicit_category_resolution() -> None:
    category = resolve_food_category(
        category_id="herb_spice"
    )
    provider = resolve_food_provider(
        category_id="herb_spice"
    )

    assert category is not None
    assert category.category_id == (
        "herb_spice"
    )

    assert isinstance(
        provider,
        HerbSpiceKnowledgeProvider,
    )


def test_registered_provider_analysis() -> None:
    provider = resolve_food_provider(
        product_name=(
            "프랑스산 건조 로즈마리 "
            "오븐 구이용"
        )
    )

    assert isinstance(
        provider,
        HerbSpiceKnowledgeProvider,
    )

    result = provider.analyze(
        {
            "product_name": (
                "프랑스산 건조 로즈마리 "
                "오븐 구이용"
            ),
            "quality_score": 80,
            "price_score": 70,
            "trust_score": 90,
        }
    )

    assert result.category_id == (
        "herb_spice"
    )
    assert result.attributes[
        "classification"
    ] == "herb"
    assert result.attributes[
        "ingredient"
    ] == "rosemary"
    assert result.attributes[
        "origin"
    ] == "france"
    assert result.attributes[
        "form"
    ] == "dried"
    assert result.attributes[
        "usage"
    ] == "roasting"


def test_provider_registration_is_unique() -> None:
    category_ids = (
        FOOD_KNOWLEDGE_REGISTRY
        .list_category_ids()
    )

    assert (
        category_ids.count(
            "herb_spice"
        )
        == 1
    )
    assert len(category_ids) == len(
        set(category_ids)
    )
