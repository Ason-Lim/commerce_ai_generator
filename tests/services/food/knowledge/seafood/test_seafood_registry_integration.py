from __future__ import annotations

import pytest

from app.services.food.category_registry import (
    get_food_category,
    resolve_food_category,
)
from app.services.food.knowledge.registry import (
    get_food_provider,
    list_food_providers,
    resolve_food_provider,
)
from app.services.food.knowledge.seafood.provider import (
    SeafoodKnowledgeProvider,
)


LEGACY_PROVIDER_ORDER = [
    "fruit",
    "vegetable",
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


def test_seafood_category_is_registered():
    category = get_food_category("seafood")

    assert category is not None
    assert category.category_id == "seafood"
    assert category.provider_id == "seafood"
    assert category.display_name == "수산물"


@pytest.mark.parametrize(
    "product_name",
    [
        "노르웨이 연어 500g",
        "냉동 새우 800g",
        "자연산 대게 1kg",
        "생물 전복 1kg",
        "손질 오징어 500g",
    ],
)
def test_category_registry_resolves_representative_seafood(
    product_name,
):
    category = resolve_food_category(
        product_name=product_name
    )

    assert category is not None
    assert category.category_id == "seafood"


def test_seafood_provider_is_registered():
    provider = get_food_provider("seafood")

    assert provider is not None
    assert isinstance(
        provider,
        SeafoodKnowledgeProvider,
    )


def test_provider_ids_are_unique():
    providers = list_food_providers()

    ids = [
        provider.category_id
        for provider in providers
    ]

    assert len(ids) == len(set(ids))


def test_seafood_provider_is_appended_after_legacy_providers():
    providers = list_food_providers()

    actual_order = [
        provider.category_id
        for provider in providers
    ]

    assert actual_order == [
        *LEGACY_PROVIDER_ORDER,
        "seafood",
    ]


def test_legacy_provider_relative_order_is_preserved():
    actual_order = [
        provider.category_id
        for provider in list_food_providers()
        if provider.category_id != "seafood"
    ]

    assert actual_order == LEGACY_PROVIDER_ORDER


@pytest.mark.parametrize(
    ("product_name", "expected_category"),
    [
        ("노르웨이 연어 500g", "seafood"),
        ("냉동 새우 800g", "seafood"),
        ("자연산 대게 1kg", "seafood"),
        ("생물 전복 1kg", "seafood"),
        ("손질 오징어 500g", "seafood"),
    ],
)
def test_runtime_resolves_representative_seafood(
    product_name,
    expected_category,
):
    provider = resolve_food_provider(
        product_name=product_name
    )

    assert provider is not None
    assert provider.category_id == expected_category


def test_explicit_seafood_category_selects_provider():
    provider = resolve_food_provider(
        category_id="seafood"
    )

    assert provider is not None
    assert provider.category_id == "seafood"


@pytest.mark.parametrize(
    ("product_name", "expected_category"),
    [
        ("제주 사과 3kg", "fruit"),
        ("양배추 1통", "vegetable"),
        ("에티오피아 원두 500g", "coffee"),
    ],
)
def test_existing_domains_remain_selectable(
    product_name,
    expected_category,
):
    provider = resolve_food_provider(
        product_name=product_name
    )

    assert provider is not None
    assert provider.category_id == expected_category


@pytest.mark.parametrize(
    "product_name",
    [
        "간장게장",
        "양념게장",
    ],
)
def test_composite_crab_food_is_not_claimed_by_seafood_provider(
    product_name,
):
    provider = resolve_food_provider(
        product_name=product_name
    )

    assert (
        provider is None
        or provider.category_id != "seafood"
    )
