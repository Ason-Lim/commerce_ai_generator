from __future__ import annotations

from app.services.food.knowledge.registry import (
    get_food_provider,
    list_food_providers,
    resolve_food_provider,
)


def test_default_food_providers_are_registered() -> None:
    category_ids = [
        provider.category_id
        for provider in list_food_providers()
    ]

    assert category_ids == [
        "fruit",
        "beef",
        "lamb",
        "chicken",
        "duck",
    ]


def test_registry_gets_lamb_provider() -> None:
    provider = get_food_provider(
        "lamb"
    )

    assert provider is not None
    assert provider.category_id == "lamb"


def test_registry_resolves_lamb_product() -> None:
    provider = resolve_food_provider(
        product_name=(
            "뉴질랜드 어린양 프렌치랙"
        )
    )

    assert provider is not None
    assert provider.category_id == "lamb"


def test_registry_still_resolves_beef_product() -> None:
    provider = resolve_food_provider(
        product_name=(
            "국내산 한우 1++ 등심"
        )
    )

    assert provider is not None
    assert provider.category_id == "beef"


def test_registry_still_resolves_fruit_product() -> None:
    provider = resolve_food_provider(
        product_name=(
            "고당도 사과 선물세트"
        )
    )

    assert provider is not None
    assert provider.category_id == "fruit"
