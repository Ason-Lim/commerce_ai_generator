from __future__ import annotations

import pytest

from app.services.food.knowledge.meat.goat import (
    GOAT_BREED_REGISTRY_ID,
    GOAT_CUT_REGISTRY_ID,
    GOAT_TYPE_REGISTRY_ID,
    GoatBreed,
    GoatBreedMatch,
    GoatBreedRegistry,
    GoatCut,
    GoatCutMatch,
    GoatCutRegistry,
    GoatType,
    GoatTypeMatch,
    GoatTypeRegistry,
)


@pytest.fixture
def type_registry() -> GoatTypeRegistry:
    return GoatTypeRegistry()


@pytest.fixture
def breed_registry() -> GoatBreedRegistry:
    return GoatBreedRegistry()


@pytest.fixture
def cut_registry() -> GoatCutRegistry:
    return GoatCutRegistry()


def test_goat_registry_ids() -> None:
    assert GOAT_TYPE_REGISTRY_ID == "goat.types"
    assert GOAT_BREED_REGISTRY_ID == "goat.breeds"
    assert GOAT_CUT_REGISTRY_ID == "goat.cuts"


def test_goat_registry_entry_counts(
    type_registry: GoatTypeRegistry,
    breed_registry: GoatBreedRegistry,
    cut_registry: GoatCutRegistry,
) -> None:
    types = type_registry.list()
    breeds = breed_registry.list()
    cuts = cut_registry.list()

    assert len(types) == 5
    assert len(breeds) == 5
    assert len(cuts) == 11

    assert all(
        isinstance(entry, GoatType)
        for entry in types
    )
    assert all(
        isinstance(entry, GoatBreed)
        for entry in breeds
    )
    assert all(
        isinstance(entry, GoatCut)
        for entry in cuts
    )


@pytest.mark.parametrize(
    ("text", "expected_key"),
    [
        ("프리미엄 어린 염소", "kid"),
        ("young goat meat", "young_goat"),
        ("성체 염소 정육", "adult_goat"),
        ("국내산 흑염소", "black_goat"),
        ("신선 염소고기", "fresh_goat"),
    ],
)
def test_goat_type_matching(
    type_registry: GoatTypeRegistry,
    text: str,
    expected_key: str,
) -> None:
    match = type_registry.match(text)

    assert isinstance(match, GoatTypeMatch)
    assert match.entry.registry_key == expected_key


@pytest.mark.parametrize(
    ("text", "expected_key"),
    [
        ("남아공 보어염소", "boer"),
        ("뉴질랜드 키코 염소", "kiko"),
        ("블랙 벵갈 염소", "black_bengal"),
        ("스위스 자넨염소", "saanen"),
        ("국내산 토종흑염소", "korean_black_goat"),
    ],
)
def test_goat_breed_matching(
    breed_registry: GoatBreedRegistry,
    text: str,
    expected_key: str,
) -> None:
    match = breed_registry.match(text)

    assert isinstance(match, GoatBreedMatch)
    assert match.entry.registry_key == expected_key


@pytest.mark.parametrize(
    ("text", "expected_key"),
    [
        ("염소안심 스테이크", "tenderloin"),
        ("염소 등심 구이", "loin"),
        ("고트 랙 로스트", "rack"),
        ("염소 다리살", "leg"),
        ("염소 어깨 찜용", "shoulder"),
        ("염소 갈비살", "rib"),
        ("염소 목살", "neck"),
        ("염소 사태", "shank"),
        ("염소 가슴살", "breast"),
        ("염소고기 정육", "trim"),
        ("통 염소 한 마리", "whole"),
    ],
)
def test_goat_cut_matching(
    cut_registry: GoatCutRegistry,
    text: str,
    expected_key: str,
) -> None:
    match = cut_registry.match(text)

    assert isinstance(match, GoatCutMatch)
    assert match.entry.registry_key == expected_key


def test_goat_registry_unknown_returns_none(
    type_registry: GoatTypeRegistry,
    breed_registry: GoatBreedRegistry,
    cut_registry: GoatCutRegistry,
) -> None:
    text = "식품 정보가 없는 일반 문자열"

    assert type_registry.match(text) is None
    assert breed_registry.match(text) is None
    assert cut_registry.match(text) is None


def test_goat_registry_lists_sorted_by_score(
    type_registry: GoatTypeRegistry,
    breed_registry: GoatBreedRegistry,
    cut_registry: GoatCutRegistry,
) -> None:
    for entries in (
        type_registry.list(),
        breed_registry.list(),
        cut_registry.list(),
    ):
        scores = [
            entry.score
            for entry in entries
        ]

        assert scores == sorted(
            scores,
            reverse=True,
        )
