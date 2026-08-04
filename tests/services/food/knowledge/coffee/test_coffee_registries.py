from __future__ import annotations

import pytest

from app.services.food.knowledge.coffee import (
    COFFEE_BEAN_REGISTRY_ID,
    COFFEE_ORIGIN_REGISTRY_ID,
    COFFEE_PROCESS_REGISTRY_ID,
    COFFEE_ROAST_REGISTRY_ID,
    CoffeeBeanMatch,
    CoffeeBeanRegistry,
    CoffeeOriginMatch,
    CoffeeOriginRegistry,
    CoffeeProcessMatch,
    CoffeeProcessRegistry,
    CoffeeRoastMatch,
    CoffeeRoastRegistry,
)
from app.services.food.knowledge.registry_loader import (
    list_knowledge_registries,
)


def test_coffee_registry_ids() -> None:
    assert COFFEE_BEAN_REGISTRY_ID == (
        "coffee.beans"
    )
    assert COFFEE_ORIGIN_REGISTRY_ID == (
        "coffee.origins"
    )
    assert COFFEE_ROAST_REGISTRY_ID == (
        "coffee.roasts"
    )
    assert COFFEE_PROCESS_REGISTRY_ID == (
        "coffee.processes"
    )


def test_coffee_registry_files_are_discovered() -> None:
    registry_ids = set(
        list_knowledge_registries()
    )

    assert {
        "coffee.beans",
        "coffee.origins",
        "coffee.roasts",
        "coffee.processes",
    }.issubset(registry_ids)


def test_coffee_registry_entry_counts() -> None:
    assert len(CoffeeBeanRegistry().list()) == 5
    assert len(CoffeeOriginRegistry().list()) == 7
    assert len(CoffeeRoastRegistry().list()) == 5
    assert len(CoffeeProcessRegistry().list()) == 6


@pytest.mark.parametrize(
    ("text", "expected_key"),
    [
        ("100% 아라비카 원두", "arabica"),
        ("로부스타 커피", "robusta"),
        ("리베리카 원두", "liberica"),
        ("엑셀사 커피", "excelsa"),
        (
            "아라비카 로부스타 블렌드",
            "arabica_robusta_blend",
        ),
    ],
)
def test_coffee_bean_matching(
    text: str,
    expected_key: str,
) -> None:
    match = CoffeeBeanRegistry().match(text)

    assert isinstance(
        match,
        CoffeeBeanMatch,
    )
    assert match.entry.registry_key == expected_key


@pytest.mark.parametrize(
    ("text", "expected_key"),
    [
        ("에티오피아 원두", "ethiopia"),
        ("콜롬비아산 커피", "colombia"),
        ("브라질 원두", "brazil"),
        ("케냐 AA 커피", "kenya"),
        ("과테말라 커피", "guatemala"),
        ("코스타리카 원두", "costa_rica"),
        ("수마트라 만델링", "indonesia"),
    ],
)
def test_coffee_origin_matching(
    text: str,
    expected_key: str,
) -> None:
    match = CoffeeOriginRegistry().match(text)

    assert isinstance(
        match,
        CoffeeOriginMatch,
    )
    assert match.entry.registry_key == expected_key


@pytest.mark.parametrize(
    ("text", "expected_key"),
    [
        ("라이트 로스트 원두", "light"),
        (
            "미디엄 라이트 로스트",
            "medium_light",
        ),
        ("미디엄 로스트 커피", "medium"),
        (
            "미디엄 다크 로스트",
            "medium_dark",
        ),
        ("프렌치 로스트 원두", "dark"),
    ],
)
def test_coffee_roast_matching(
    text: str,
    expected_key: str,
) -> None:
    match = CoffeeRoastRegistry().match(text)

    assert isinstance(
        match,
        CoffeeRoastMatch,
    )
    assert match.entry.registry_key == expected_key


@pytest.mark.parametrize(
    ("text", "expected_key"),
    [
        ("워시드 에티오피아", "washed"),
        ("내추럴 프로세스", "natural"),
        ("허니 프로세스 원두", "honey"),
        ("무산소 발효 커피", "anaerobic"),
        (
            "카보닉 마세레이션",
            "carbonic_maceration",
        ),
        ("길링 바사 수마트라", "wet_hulled"),
    ],
)
def test_coffee_process_matching(
    text: str,
    expected_key: str,
) -> None:
    match = CoffeeProcessRegistry().match(text)

    assert isinstance(
        match,
        CoffeeProcessMatch,
    )
    assert match.entry.registry_key == expected_key


def test_unknown_registry_text_returns_none() -> None:
    text = "분류할 수 없는 일반 상품"

    assert CoffeeBeanRegistry().match(text) is None
    assert CoffeeOriginRegistry().match(text) is None
    assert CoffeeRoastRegistry().match(text) is None
    assert CoffeeProcessRegistry().match(text) is None


def test_registry_lists_are_sorted_by_score() -> None:
    registries = [
        CoffeeBeanRegistry(),
        CoffeeOriginRegistry(),
        CoffeeRoastRegistry(),
        CoffeeProcessRegistry(),
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


def test_registry_keys_are_unique() -> None:
    registries = [
        CoffeeBeanRegistry(),
        CoffeeOriginRegistry(),
        CoffeeRoastRegistry(),
        CoffeeProcessRegistry(),
    ]

    for registry in registries:
        keys = [
            entry.registry_key
            for entry in registry.list()
        ]

        assert len(keys) == len(set(keys))


def test_premium_filter() -> None:
    premium_beans = CoffeeBeanRegistry().list(
        premium_only=True
    )

    assert premium_beans
    assert all(
        entry.premium
        for entry in premium_beans
    )


def test_registry_match_serializes() -> None:
    match = CoffeeOriginRegistry().match(
        "에티오피아 원두"
    )

    assert match is not None

    payload = match.to_dict()

    assert payload["registry_key"] == "ethiopia"
    assert payload["canonical_name"] == (
        "에티오피아"
    )
    assert payload["country_code"] == "ET"
    assert payload["matched_alias"]
    assert 0.0 <= payload["confidence"] <= 1.0
