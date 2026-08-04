from __future__ import annotations

import pytest

from app.services.food.knowledge.wine.acidity_registry import (
    WineAcidityRegistry,
)
from app.services.food.knowledge.wine.body_registry import (
    WineBodyRegistry,
)
from app.services.food.knowledge.wine.grape_registry import (
    WineGrapeRegistry,
)
from app.services.food.knowledge.wine.region_registry import (
    WineRegionRegistry,
)
from app.services.food.knowledge.wine.sweetness_registry import (
    WineSweetnessRegistry,
)
from app.services.food.knowledge.wine.type_registry import (
    WineTypeRegistry,
)


@pytest.mark.parametrize(
    (
        "registry",
        "text",
        "expected_key",
    ),
    [
        (
            WineTypeRegistry(),
            "레드 와인",
            "red",
        ),
        (
            WineGrapeRegistry(),
            "카베르네 소비뇽",
            "cabernet_sauvignon",
        ),
        (
            WineRegionRegistry(),
            "보르도",
            "bordeaux",
        ),
        (
            WineSweetnessRegistry(),
            "드라이",
            "dry",
        ),
        (
            WineBodyRegistry(),
            "풀 바디",
            "full",
        ),
        (
            WineAcidityRegistry(),
            "높은 산도",
            "high",
        ),
    ],
)
def test_wine_registry_matches_alias(
    registry: object,
    text: str,
    expected_key: str,
) -> None:
    match = registry.match(text)  # type: ignore[attr-defined]

    assert match is not None
    assert match.entry.registry_key == expected_key
    assert match.matched_alias
    assert match.normalized_alias
    assert 0.0 <= match.confidence <= 1.0
    assert match.match_start >= 0
    assert match.match_end > match.match_start
    assert match.exact_match is True


@pytest.mark.parametrize(
    (
        "registry",
        "text",
    ),
    [
        (
            WineTypeRegistry(),
            "레드 와인",
        ),
        (
            WineGrapeRegistry(),
            "샤르도네",
        ),
        (
            WineRegionRegistry(),
            "나파 밸리",
        ),
        (
            WineSweetnessRegistry(),
            "세미 드라이",
        ),
        (
            WineBodyRegistry(),
            "미디엄 바디",
        ),
        (
            WineAcidityRegistry(),
            "낮은 산도",
        ),
    ],
)
def test_wine_registry_lookup_returns_entry(
    registry: object,
    text: str,
) -> None:
    entry = registry.lookup(text)  # type: ignore[attr-defined]

    assert entry is not None
    assert entry.registry_key
    assert entry.canonical_name
    assert entry.aliases
    assert 0.0 <= entry.score <= 100.0


@pytest.mark.parametrize(
    "registry",
    [
        WineTypeRegistry(),
        WineGrapeRegistry(),
        WineRegionRegistry(),
        WineSweetnessRegistry(),
        WineBodyRegistry(),
        WineAcidityRegistry(),
    ],
)
def test_wine_registry_returns_none_for_unknown_text(
    registry: object,
) -> None:
    match = registry.match(  # type: ignore[attr-defined]
        "등록되지 않은 임의의 문자열"
    )

    assert match is None


def test_wine_type_registry_metadata() -> None:
    entry = WineTypeRegistry().lookup(
        "스파클링 와인"
    )

    assert entry is not None
    assert entry.registry_key == "sparkling"
    assert entry.sparkling is True
    assert entry.fortified is False


def test_wine_grape_registry_metadata() -> None:
    entry = WineGrapeRegistry().lookup(
        "리슬링"
    )

    assert entry is not None
    assert entry.registry_key == "riesling"
    assert entry.color == "white"
    assert entry.aromatic is True


def test_wine_region_registry_metadata() -> None:
    entry = WineRegionRegistry().lookup(
        "부르고뉴"
    )

    assert entry is not None
    assert entry.registry_key == "burgundy"
    assert entry.country_code == "FR"
    assert entry.appellation == "Bourgogne"


def test_wine_sweetness_registry_metadata() -> None:
    entry = WineSweetnessRegistry().lookup(
        "드라이"
    )

    assert entry is not None
    assert entry.sweetness_level == 1
    assert entry.residual_sugar_min == 0.0
    assert entry.residual_sugar_max == 4.0


def test_wine_body_registry_metadata() -> None:
    entry = WineBodyRegistry().lookup(
        "풀 바디"
    )

    assert entry is not None
    assert entry.body_level == 3
    assert entry.premium is True


def test_wine_acidity_registry_metadata() -> None:
    entry = WineAcidityRegistry().lookup(
        "높은 산도"
    )

    assert entry is not None
    assert entry.acidity_level == 3
    assert entry.premium is True
