from __future__ import annotations

import pytest

from app.services.food.knowledge.cheese import (
    CHEESE_AGING_REGISTRY_ID,
    CHEESE_MILK_SOURCE_REGISTRY_ID,
    CHEESE_ORIGIN_REGISTRY_ID,
    CHEESE_TEXTURE_REGISTRY_ID,
    CHEESE_TYPE_REGISTRY_ID,
    CheeseAgingMatch,
    CheeseAgingRegistry,
    CheeseMilkSourceMatch,
    CheeseMilkSourceRegistry,
    CheeseOriginMatch,
    CheeseOriginRegistry,
    CheeseTextureMatch,
    CheeseTextureRegistry,
    CheeseTypeMatch,
    CheeseTypeRegistry,
)
from app.services.food.knowledge.registry_loader import (
    list_knowledge_registries,
)


def test_cheese_registry_ids() -> None:
    assert CHEESE_TYPE_REGISTRY_ID == (
        "cheese.types"
    )
    assert CHEESE_MILK_SOURCE_REGISTRY_ID == (
        "cheese.milk_sources"
    )
    assert CHEESE_ORIGIN_REGISTRY_ID == (
        "cheese.origins"
    )
    assert CHEESE_TEXTURE_REGISTRY_ID == (
        "cheese.textures"
    )
    assert CHEESE_AGING_REGISTRY_ID == (
        "cheese.aging"
    )


def test_cheese_registry_files_are_discovered() -> None:
    registry_ids = set(
        list_knowledge_registries()
    )

    assert {
        "cheese.types",
        "cheese.milk_sources",
        "cheese.origins",
        "cheese.textures",
        "cheese.aging",
    }.issubset(registry_ids)


def test_cheese_registry_entry_counts() -> None:
    assert len(CheeseTypeRegistry().list()) == 8
    assert len(
        CheeseMilkSourceRegistry().list()
    ) == 5
    assert len(CheeseOriginRegistry().list()) == 7
    assert len(CheeseTextureRegistry().list()) == 7
    assert len(CheeseAgingRegistry().list()) == 5


@pytest.mark.parametrize(
    ("text", "expected_key"),
    [
        ("이탈리아 모차렐라 치즈", "mozzarella"),
        ("숙성 체다치즈", "cheddar"),
        ("프랑스 브리 치즈", "brie"),
        ("까망베르 치즈", "camembert"),
        ("네덜란드 고다치즈", "gouda"),
        (
            "파르미자노 레지아노",
            "parmesan",
        ),
        ("블루 치즈", "blue_cheese"),
        ("플레인 크림치즈", "cream_cheese"),
    ],
)
def test_cheese_type_matching(
    text: str,
    expected_key: str,
) -> None:
    match = CheeseTypeRegistry().match(text)

    assert isinstance(
        match,
        CheeseTypeMatch,
    )
    assert (
        match.entry.registry_key
        == expected_key
    )


@pytest.mark.parametrize(
    ("text", "expected_key"),
    [
        ("우유로 만든 체다", "cow"),
        ("산양유 치즈", "goat"),
        ("양유 페코리노", "sheep"),
        ("물소 우유 모차렐라", "buffalo"),
        ("혼합 원유 치즈", "mixed"),
    ],
)
def test_cheese_milk_source_matching(
    text: str,
    expected_key: str,
) -> None:
    match = CheeseMilkSourceRegistry().match(
        text
    )

    assert isinstance(
        match,
        CheeseMilkSourceMatch,
    )
    assert (
        match.entry.registry_key
        == expected_key
    )


@pytest.mark.parametrize(
    ("text", "expected_key"),
    [
        ("이탈리아산 파르미자노", "italy"),
        ("프랑스 브리", "france"),
        ("네덜란드 고다", "netherlands"),
        ("영국 체다", "united_kingdom"),
        ("스위스 치즈", "switzerland"),
        ("미국산 체다", "united_states"),
        ("국내산 자연치즈", "korea"),
    ],
)
def test_cheese_origin_matching(
    text: str,
    expected_key: str,
) -> None:
    match = CheeseOriginRegistry().match(text)

    assert isinstance(
        match,
        CheeseOriginMatch,
    )
    assert (
        match.entry.registry_key
        == expected_key
    )


@pytest.mark.parametrize(
    ("text", "expected_key"),
    [
        ("프레시 생치즈", "fresh"),
        ("부드러운 소프트 치즈", "soft"),
        ("세미소프트 치즈", "semi_soft"),
        ("세미 하드 치즈", "semi_hard"),
        ("단단한 하드치즈", "hard"),
        ("크럼블리 치즈", "crumbly"),
        ("발라 먹는 치즈", "spreadable"),
    ],
)
def test_cheese_texture_matching(
    text: str,
    expected_key: str,
) -> None:
    match = CheeseTextureRegistry().match(text)

    assert isinstance(
        match,
        CheeseTextureMatch,
    )
    assert (
        match.entry.registry_key
        == expected_key
    )


@pytest.mark.parametrize(
    ("text", "expected_key"),
    [
        ("무숙성 프레시 치즈", "fresh"),
        ("단기 숙성 치즈", "short_aged"),
        ("중기 숙성 치즈", "medium_aged"),
        ("12개월 숙성 치즈", "long_aged"),
        ("24개월 숙성 치즈", "extra_aged"),
    ],
)
def test_cheese_aging_matching(
    text: str,
    expected_key: str,
) -> None:
    match = CheeseAgingRegistry().match(text)

    assert isinstance(
        match,
        CheeseAgingMatch,
    )
    assert (
        match.entry.registry_key
        == expected_key
    )


def test_unknown_cheese_registry_text_returns_none() -> None:
    text = "상품 정보가 없는 일반 문자열"

    assert CheeseTypeRegistry().match(text) is None
    assert (
        CheeseMilkSourceRegistry().match(text)
        is None
    )
    assert (
        CheeseOriginRegistry().match(text)
        is None
    )
    assert (
        CheeseTextureRegistry().match(text)
        is None
    )
    assert CheeseAgingRegistry().match(text) is None


def test_cheese_registry_lists_are_sorted_by_score() -> None:
    registries = [
        CheeseTypeRegistry(),
        CheeseMilkSourceRegistry(),
        CheeseOriginRegistry(),
        CheeseTextureRegistry(),
        CheeseAgingRegistry(),
    ]

    for registry in registries:
        scores = [
            entry.score
            for entry in registry.list()
        ]

        assert scores == sorted(
            scores,
            reverse=True,
        )


def test_cheese_registry_keys_are_unique() -> None:
    registries = [
        CheeseTypeRegistry(),
        CheeseMilkSourceRegistry(),
        CheeseOriginRegistry(),
        CheeseTextureRegistry(),
        CheeseAgingRegistry(),
    ]

    for registry in registries:
        keys = [
            entry.registry_key
            for entry in registry.list()
        ]

        assert len(keys) == len(set(keys))


def test_cheese_registry_match_serializes() -> None:
    match = CheeseTypeRegistry().match(
        "이탈리아 모차렐라 치즈"
    )

    assert match is not None

    payload = match.to_dict()

    assert payload["registry_key"] == (
        "mozzarella"
    )
    assert payload["canonical_name"] == (
        "모차렐라"
    )
    assert payload["matched_alias"]
    assert 0.0 <= payload["confidence"] <= 1.0
