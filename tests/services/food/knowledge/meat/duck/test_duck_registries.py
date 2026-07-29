from __future__ import annotations

import pytest

from app.services.food.knowledge.meat.duck import (
    DUCK_BREED_REGISTRY_ID,
    DUCK_CUT_REGISTRY_ID,
    DUCK_TYPE_REGISTRY_ID,
    DuckBreed,
    DuckBreedMatch,
    DuckBreedRegistry,
    DuckCut,
    DuckCutMatch,
    DuckCutRegistry,
    DuckType,
    DuckTypeMatch,
    DuckTypeRegistry,
)


@pytest.fixture
def type_registry() -> DuckTypeRegistry:
    return DuckTypeRegistry()


@pytest.fixture
def breed_registry() -> DuckBreedRegistry:
    return DuckBreedRegistry()


@pytest.fixture
def cut_registry() -> DuckCutRegistry:
    return DuckCutRegistry()


def test_duck_registry_ids() -> None:
    assert DUCK_TYPE_REGISTRY_ID == "duck.types"
    assert DUCK_BREED_REGISTRY_ID == "duck.breeds"
    assert DUCK_CUT_REGISTRY_ID == "duck.cuts"


def test_duck_registry_entry_counts(
    type_registry: DuckTypeRegistry,
    breed_registry: DuckBreedRegistry,
    cut_registry: DuckCutRegistry,
) -> None:
    types = type_registry.list()
    breeds = breed_registry.list()
    cuts = cut_registry.list()

    assert len(types) == 5
    assert len(breeds) == 5
    assert len(cuts) == 11

    assert all(isinstance(entry, DuckType) for entry in types)
    assert all(isinstance(entry, DuckBreed) for entry in breeds)
    assert all(isinstance(entry, DuckCut) for entry in cuts)


@pytest.mark.parametrize(
    ("text", "expected_key"),
    [
        ("국내산 훈제오리 슬라이스", "smoked_duck"),
        ("토종 오리 백숙용", "native_duck"),
        ("어린 오리 로스트용", "duckling"),
        ("로스트 덕 한 마리", "roast_duck"),
        ("식용 오리 정육", "domestic_duck"),
    ],
)
def test_duck_type_matching(
    type_registry: DuckTypeRegistry,
    text: str,
    expected_key: str,
) -> None:
    match = type_registry.match(text)

    assert isinstance(match, DuckTypeMatch)
    assert match.entry.registry_key == expected_key


@pytest.mark.parametrize(
    ("text", "expected_key"),
    [
        ("프리미엄 체리밸리 오리", "cherry_valley"),
        ("페킨오리 냉동육", "pekin"),
        ("머스코비 오리 구이용", "muscovy"),
        ("뮬라드 오리 가슴살", "mule_duck"),
        ("청둥 오리 정육", "mallard"),
    ],
)
def test_duck_breed_matching(
    breed_registry: DuckBreedRegistry,
    text: str,
    expected_key: str,
) -> None:
    match = breed_registry.match(text)

    assert isinstance(match, DuckBreedMatch)
    assert match.entry.registry_key == expected_key


@pytest.mark.parametrize(
    ("text", "expected_key"),
    [
        ("냉동 오리가슴살 500g", "breast"),
        ("오리 안심 구이용", "tenderloin"),
        ("오리 다리살 정육", "thigh"),
        ("오리 장각 두 개", "leg"),
        ("오리 날개 냉동", "wing"),
        ("오리 목살 1kg", "neck"),
        ("오리 똥집 볶음용", "gizzard"),
        ("오리 염통 꼬치용", "heart"),
        ("오리 간 냉장", "liver"),
        ("오리 껍질 구이용", "skin"),
        ("통 오리 한 마리", "whole_duck"),
    ],
)
def test_duck_cut_matching(
    cut_registry: DuckCutRegistry,
    text: str,
    expected_key: str,
) -> None:
    match = cut_registry.match(text)

    assert isinstance(match, DuckCutMatch)
    assert match.entry.registry_key == expected_key


def test_duck_registry_lookup(
    type_registry: DuckTypeRegistry,
    breed_registry: DuckBreedRegistry,
    cut_registry: DuckCutRegistry,
) -> None:
    duck_type = type_registry.lookup("훈제 오리")
    breed = breed_registry.lookup("Cherry Valley duck")
    cut = cut_registry.lookup("duck breast")

    assert duck_type is not None
    assert breed is not None
    assert cut is not None

    assert duck_type.registry_key == "smoked_duck"
    assert breed.registry_key == "cherry_valley"
    assert cut.registry_key == "breast"


def test_duck_registry_unknown_text_returns_none(
    type_registry: DuckTypeRegistry,
    breed_registry: DuckBreedRegistry,
    cut_registry: DuckCutRegistry,
) -> None:
    text = "상품 정보가 전혀 없는 테스트 문자열"

    assert type_registry.match(text) is None
    assert breed_registry.match(text) is None
    assert cut_registry.match(text) is None


def test_duck_premium_filters(
    type_registry: DuckTypeRegistry,
    breed_registry: DuckBreedRegistry,
    cut_registry: DuckCutRegistry,
) -> None:
    premium_types = type_registry.list(premium_only=True)
    premium_breeds = breed_registry.list(premium_only=True)
    premium_cuts = cut_registry.list(premium_only=True)

    assert {
        entry.registry_key
        for entry in premium_types
    } == {
        "duckling",
        "native_duck",
    }

    assert {
        entry.registry_key
        for entry in premium_breeds
    } == {
        "muscovy",
        "mule_duck",
        "mallard",
    }

    assert {
        entry.registry_key
        for entry in premium_cuts
    } == {
        "breast",
        "tenderloin",
        "liver",
    }


def test_duck_type_category_filter(
    type_registry: DuckTypeRegistry,
) -> None:
    entries = type_registry.list(
        type_category="smoked_duck"
    )

    assert len(entries) == 1
    assert entries[0].registry_key == "smoked_duck"


def test_duck_breed_type_filter(
    breed_registry: DuckBreedRegistry,
) -> None:
    entries = breed_registry.list(
        breed_type="meat_duck"
    )

    assert {
        entry.registry_key
        for entry in entries
    } == {
        "pekin",
        "muscovy",
    }


def test_duck_cut_group_filter(
    cut_registry: DuckCutRegistry,
) -> None:
    entries = cut_registry.list(
        cut_group="leg"
    )

    assert {
        entry.registry_key
        for entry in entries
    } == {
        "thigh",
        "leg",
    }


def test_duck_registry_lists_are_sorted_by_score(
    type_registry: DuckTypeRegistry,
    breed_registry: DuckBreedRegistry,
    cut_registry: DuckCutRegistry,
) -> None:
    for entries in (
        type_registry.list(),
        breed_registry.list(),
        cut_registry.list(),
    ):
        scores = [entry.score for entry in entries]
        assert scores == sorted(scores, reverse=True)


def test_duck_registry_entries_expose_metadata(
    type_registry: DuckTypeRegistry,
) -> None:
    entry = type_registry.lookup("훈제오리")

    assert entry is not None
    assert isinstance(entry.metadata, dict)
