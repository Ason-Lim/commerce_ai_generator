from __future__ import annotations

import pytest

from app.services.food.knowledge import (
    FoodKnowledgeResult,
    get_food_provider,
    list_food_providers,
    resolve_food_provider,
)
from app.services.food.knowledge.meat.venison import (
    VenisonKnowledgeProvider,
)


def _category_id(
    provider: object,
) -> str | None:
    value = getattr(
        provider,
        "category_id",
        None,
    )

    return (
        str(value)
        if value is not None
        else None
    )


def test_venison_registered_once() -> None:
    matches = [
        provider
        for provider in list_food_providers()
        if _category_id(provider) == "venison"
    ]

    assert len(matches) == 1
    assert isinstance(
        matches[0],
        VenisonKnowledgeProvider,
    )


def test_existing_meat_providers_preserved() -> None:
    category_ids = {
        _category_id(provider)
        for provider in list_food_providers()
    }

    assert {
        "beef",
        "lamb",
        "chicken",
        "duck",
        "venison",
    }.issubset(category_ids)


def test_get_venison_provider() -> None:
    provider = get_food_provider("venison")

    assert isinstance(
        provider,
        VenisonKnowledgeProvider,
    )

    assert provider.category_id == "venison"
    assert provider.parent_category_id == "meat"
    assert provider.provider_id == "venison"


@pytest.mark.parametrize(
    "product_name",
    [
        "뉴질랜드산 사슴고기 500g",
        "사슴 안심 1kg",
        "사슴가슴살 냉동육",
        "premium venison tenderloin",
        "red deer venison loin",
        "New Zealand deer meat",
        "elk meat shoulder",
    ],
)
def test_resolve_venison_provider(
    product_name: str,
) -> None:
    provider = resolve_food_provider(
        product_name=product_name
    )

    assert isinstance(
        provider,
        VenisonKnowledgeProvider,
    )


@pytest.mark.parametrize(
    "product_name",
    [
        "국내산 닭날개 1kg",
        "오리 백숙용 1마리",
        "한우 등심 500g",
        "양고기 프렌치랙",
    ],
)
def test_non_venison_boundary(
    product_name: str,
) -> None:
    provider = resolve_food_provider(
        product_name=product_name
    )

    assert not isinstance(
        provider,
        VenisonKnowledgeProvider,
    )


def test_registry_to_result_e2e() -> None:
    provider = resolve_food_provider(
        product_name=(
            "뉴질랜드산 어린사슴 "
            "레드디어 사슴가슴살 500g"
        )
    )

    assert isinstance(
        provider,
        VenisonKnowledgeProvider,
    )

    result = provider.analyze(
        {
            "product_name": (
                "뉴질랜드산 어린사슴 "
                "레드디어 사슴가슴살 500g"
            ),
            "venison_type": "어린 사슴",
            "deer_species": "Red Deer",
            "cut": "venison breast",
            "country": "뉴질랜드",
            "country_code": "NZ",
            "weight": "500g",
            "storage_type": "냉동",
            "certifications": ["HACCP"],
            "quality_score": 80,
            "price_score": 70,
            "trust_score": 90,
        }
    )

    assert isinstance(
        result,
        FoodKnowledgeResult,
    )

    assert result.category_id == "venison"
    assert result.attributes[
        "venison_type"
    ] == "어린사슴"
    assert result.attributes[
        "breed"
    ] == "레드디어"
    assert result.attributes[
        "cut"
    ] == "사슴가슴살"
    assert result.attributes[
        "cut_registry_key"
    ] == "breast"
    assert result.scores[
        "knowledge"
    ] == 87.1
    assert result.final_score == 83.55
    assert result.warnings == []
