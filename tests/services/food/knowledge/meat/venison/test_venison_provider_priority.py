from __future__ import annotations

import pytest

from app.services.food.knowledge import (
    resolve_food_provider,
)
from app.services.food.knowledge.meat.beef import (
    BeefKnowledgeProvider,
)
from app.services.food.knowledge.meat.venison import (
    VenisonKnowledgeProvider,
)


@pytest.mark.parametrize(
    "product_name",
    [
        "사슴 안심",
        "사슴 안심 1kg",
        "사슴 등심",
        "사슴 등심 500g",
        "사슴가슴살",
        "뉴질랜드산 사슴고기",
        "레드디어 안심",
        "레드디어 등심",
        "premium venison tenderloin",
        "red deer sirloin",
        "deer meat loin",
        "elk meat shoulder",
    ],
)
def test_explicit_venison_species_precedes_beef_cut_match(
    product_name: str,
) -> None:
    provider = resolve_food_provider(
        product_name=product_name,
    )

    assert isinstance(
        provider,
        VenisonKnowledgeProvider,
    )


@pytest.mark.parametrize(
    "product_name",
    [
        "한우 안심",
        "한우 등심",
        "소고기 안심",
        "소고기 등심",
        "쇠고기 안심",
        "국내산 한우 채끝",
        "beef tenderloin",
        "beef sirloin",
    ],
)
def test_explicit_beef_products_remain_beef(
    product_name: str,
) -> None:
    provider = resolve_food_provider(
        product_name=product_name,
    )

    assert isinstance(
        provider,
        BeefKnowledgeProvider,
    )


@pytest.mark.parametrize(
    "product_name",
    [
        "안심",
        "안심 1kg",
        "등심",
        "등심 500g",
        "채끝",
        "가슴살",
        "냉동 안심",
    ],
)
def test_generic_cut_terms_do_not_false_positive_as_venison(
    product_name: str,
) -> None:
    provider = resolve_food_provider(
        product_name=product_name,
    )

    assert not isinstance(
        provider,
        VenisonKnowledgeProvider,
    )


@pytest.mark.parametrize(
    "product_name",
    [
        "사슴 안심",
        "사슴 등심",
        "레드디어 안심",
        "premium venison tenderloin",
    ],
)
def test_provider_resolution_is_deterministic(
    product_name: str,
) -> None:
    provider_types = []

    for _ in range(5):
        provider = resolve_food_provider(
            product_name=product_name,
        )

        provider_types.append(
            type(provider)
            if provider is not None
            else None
        )

    assert len(set(provider_types)) == 1
    assert provider_types[0] is VenisonKnowledgeProvider
