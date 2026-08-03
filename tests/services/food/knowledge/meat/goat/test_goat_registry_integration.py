from __future__ import annotations

import pytest

from app.services.food.knowledge import (
    FoodKnowledgeResult,
    get_food_provider,
    list_food_providers,
    require_food_provider,
    resolve_food_provider,
)
from app.services.food.knowledge.meat.goat import (
    GoatBreedRegistry,
    GoatCutRegistry,
    GoatKnowledgeProvider,
    GoatTypeRegistry,
)


def test_goat_provider_registered_once() -> None:
    matches = [
        provider
        for provider in list_food_providers()
        if provider.category_id == "goat"
    ]

    assert len(matches) == 1
    assert isinstance(
        matches[0],
        GoatKnowledgeProvider,
    )


def test_get_and_require_goat_provider() -> None:
    provider = get_food_provider("goat")

    assert isinstance(
        provider,
        GoatKnowledgeProvider,
    )
    assert (
        require_food_provider("goat")
        is provider
    )


@pytest.mark.parametrize(
    "product_name",
    [
        "국내산 흑염소 정육 1kg",
        "어린염소 보어 염소안심",
        "Boer goat tenderloin",
        "Korean black goat meat",
        "염소다리살 냉동육",
    ],
)
def test_resolve_goat_provider(
    product_name: str,
) -> None:
    provider = resolve_food_provider(
        product_name=product_name
    )

    assert isinstance(
        provider,
        GoatKnowledgeProvider,
    )


@pytest.mark.parametrize(
    "product_name",
    [
        "한우 등심 500g",
        "양고기 프렌치랙",
        "닭가슴살 1kg",
        "훈제오리 슬라이스",
        "사슴 안심",
        "안심 500g",
        "등심 1kg",
    ],
)
def test_non_goat_boundary(
    product_name: str,
) -> None:
    provider = resolve_food_provider(
        product_name=product_name
    )

    assert not isinstance(
        provider,
        GoatKnowledgeProvider,
    )


def test_goat_registry_data_loads() -> None:
    type_registry = GoatTypeRegistry()
    breed_registry = GoatBreedRegistry()
    cut_registry = GoatCutRegistry()

    assert type_registry.registry_id == (
        "goat.types"
    )
    assert breed_registry.registry_id == (
        "goat.breeds"
    )
    assert cut_registry.registry_id == (
        "goat.cuts"
    )

    assert type_registry.list()
    assert breed_registry.list()
    assert cut_registry.list()


def test_goat_registry_keys_are_unique() -> None:
    registries = [
        GoatTypeRegistry(),
        GoatBreedRegistry(),
        GoatCutRegistry(),
    ]

    for registry in registries:
        keys = [
            entry.registry_key
            for entry in registry.list()
        ]

        assert len(keys) == len(set(keys))


def test_registry_to_result_e2e() -> None:
    provider = resolve_food_provider(
        product_name=(
            "국내산 어린염소 보어 "
            "염소안심 500g"
        )
    )

    assert isinstance(
        provider,
        GoatKnowledgeProvider,
    )

    result = provider.analyze(
        {
            "product_name": (
                "국내산 어린염소 보어 "
                "염소안심 500g"
            ),
            "goat_type": "어린 염소",
            "goat_breed": "Boer",
            "cut": "goat tenderloin",
            "country": "대한민국",
            "quality_score": 80,
            "price_score": 70,
            "trust_score": 90,
        }
    )

    assert isinstance(
        result,
        FoodKnowledgeResult,
    )
    assert result.category_id == "goat"
    assert result.attributes[
        "goat_type"
    ] == "어린염소"
    assert result.attributes["breed"] == "보어"
    assert result.attributes["cut"] == "염소안심"
    assert result.scores["knowledge"] == 95.0
    assert result.final_score == 87.5
    assert result.warnings == []


def test_provider_ids_remain_unique() -> None:
    category_ids = [
        provider.category_id
        for provider in list_food_providers()
    ]

    assert len(category_ids) == len(
        set(category_ids)
    )
