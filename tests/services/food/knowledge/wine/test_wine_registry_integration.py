from __future__ import annotations

import pytest

from app.services.food.knowledge.registry import (
    FOOD_KNOWLEDGE_REGISTRY,
    get_food_provider,
    list_food_providers,
    require_food_provider,
    resolve_food_provider,
)
from app.services.food.knowledge.wine.provider import (
    WineKnowledgeProvider,
)


def test_wine_provider_is_registered() -> None:
    provider = get_food_provider("wine")

    assert isinstance(
        provider,
        WineKnowledgeProvider,
    )


def test_wine_provider_is_required() -> None:
    provider = require_food_provider(
        "wine"
    )

    assert isinstance(
        provider,
        WineKnowledgeProvider,
    )


def test_wine_category_is_listed() -> None:
    assert (
        "wine"
        in FOOD_KNOWLEDGE_REGISTRY.list_category_ids()
    )


def test_wine_provider_is_in_provider_list() -> None:
    providers = list_food_providers()

    assert any(
        isinstance(
            provider,
            WineKnowledgeProvider,
        )
        for provider in providers
    )


@pytest.mark.parametrize(
    "category_id",
    [
        "wine",
        "WINE",
        " wine ",
        "와인",
        "보르도",
        "chardonnay",
    ],
)
def test_resolve_wine_provider_by_category(
    category_id: str,
) -> None:
    provider = resolve_food_provider(
        category_id=category_id
    )

    assert isinstance(
        provider,
        WineKnowledgeProvider,
    )


@pytest.mark.parametrize(
    "product_name",
    [
        "2020 보르도 레드 와인",
        "부르고뉴 샤르도네 화이트와인",
        "Napa Valley Cabernet Sauvignon Wine",
        "리슬링 스파클링 와인",
    ],
)
def test_resolve_wine_provider_by_product_name(
    product_name: str,
) -> None:
    provider = resolve_food_provider(
        product_name=product_name
    )

    assert isinstance(
        provider,
        WineKnowledgeProvider,
    )


@pytest.mark.parametrize(
    "product_name",
    [
        "국산 사과 5kg",
        "한우 등심 1++",
        "모차렐라 치즈 200g",
    ],
)
def test_wine_provider_does_not_capture_other_domains(
    product_name: str,
) -> None:
    provider = resolve_food_provider(
        product_name=product_name
    )

    assert not isinstance(
        provider,
        WineKnowledgeProvider,
    )


def test_resolved_wine_provider_runs_analysis() -> None:
    provider = resolve_food_provider(
        product_name=(
            "2020 보르도 카베르네 소비뇽 "
            "레드 와인"
        )
    )

    assert isinstance(
        provider,
        WineKnowledgeProvider,
    )

    result = provider.analyze(
        {
            "product_name": (
                "2020 보르도 카베르네 소비뇽 "
                "레드 와인 드라이 13.5%"
            ),
            "producer": "Example Winery",
            "volume": "750ml",
        }
    )

    assert result.category_id == "wine"
    assert result.attributes["region"] == "bordeaux"
    assert (
        result.attributes["grape"]
        == "cabernet_sauvignon"
    )
