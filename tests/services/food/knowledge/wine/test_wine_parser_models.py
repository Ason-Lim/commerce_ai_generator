from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from app.services.food.knowledge.common.parser_models import (
    BaseParseResult,
)
from app.services.food.knowledge.wine.parser_models import (
    WineParseResult,
)


def test_wine_parse_result_extends_base_contract() -> None:
    result = WineParseResult(
        original_text=(
            "보르도 카베르네 소비뇽 "
            "레드 와인 2020"
        ),
        normalized_text=(
            "보르도 카베르네 소비뇽 "
            "레드 와인 2020"
        ),
        confidence=0.92,
        wine_type="red",
        grape="cabernet_sauvignon",
        region="bordeaux",
        vintage=2020,
    )

    assert isinstance(
        result,
        BaseParseResult,
    )
    assert result.wine_type == "red"
    assert (
        result.grape
        == "cabernet_sauvignon"
    )
    assert result.region == "bordeaux"
    assert result.vintage == 2020
    assert result.matched_field_count == 3
    assert result.is_usable is True


def test_wine_parse_result_clamps_confidence() -> None:
    result = WineParseResult(
        original_text="레드 와인",
        normalized_text="레드 와인",
        confidence=5.0,
        wine_type="red",
        wine_type_confidence=3.0,
        grape_confidence=-1.0,
    )

    assert result.confidence == 1.0
    assert result.wine_type_confidence == 1.0
    assert result.grape_confidence == 0.0


@pytest.mark.parametrize(
    "vintage",
    [
        1700,
        2200,
    ],
)
def test_wine_parse_result_rejects_invalid_vintage(
    vintage: int,
) -> None:
    result = WineParseResult(
        original_text="와인",
        normalized_text="와인",
        confidence=0.5,
        vintage=vintage,
    )

    assert result.vintage is None


def test_wine_parse_result_preserves_valid_vintage() -> None:
    result = WineParseResult(
        original_text="2019 보르도 와인",
        normalized_text="2019 보르도 와인",
        confidence=0.8,
        region="bordeaux",
        vintage=2019,
    )

    assert result.vintage == 2019


def test_wine_parse_result_clamps_alcohol_percent() -> None:
    high_result = WineParseResult(
        original_text="와인",
        normalized_text="와인",
        confidence=0.5,
        alcohol_percent=120.0,
    )

    low_result = WineParseResult(
        original_text="와인",
        normalized_text="와인",
        confidence=0.5,
        alcohol_percent=-10.0,
    )

    assert high_result.alcohol_percent == 100.0
    assert low_result.alcohol_percent == 0.0


def test_wine_parse_result_deduplicates_evidence() -> None:
    result = WineParseResult(
        original_text="보르도 와인",
        normalized_text="보르도 와인",
        confidence=0.8,
        region="bordeaux",
        detected_keywords=[
            "보르도",
            "보르도",
            "",
        ],
        warnings=[
            "warning",
            "warning",
            "",
        ],
    )

    assert result.detected_keywords == [
        "보르도",
    ]
    assert result.warnings == [
        "warning",
    ]


def test_wine_parse_result_serialization() -> None:
    result = WineParseResult(
        original_text="샤르도네 화이트 와인",
        normalized_text="샤르도네 화이트 와인",
        confidence=0.9,
        wine_type="white",
        grape="chardonnay",
        detected_keywords=[
            "샤르도네",
            "화이트 와인",
        ],
    )

    payload = result.to_dict()

    assert payload["wine_type"] == "white"
    assert payload["grape"] == "chardonnay"
    assert payload["matched_field_count"] == 2
    assert payload["is_usable"] is True
    assert payload["detected_keywords"] == [
        "샤르도네",
        "화이트 와인",
    ]


def test_wine_parse_result_is_frozen() -> None:
    result = WineParseResult(
        original_text="레드 와인",
        normalized_text="레드 와인",
        confidence=0.8,
        wine_type="red",
    )

    with pytest.raises(FrozenInstanceError):
        result.wine_type = "white"  # type: ignore[misc]


def test_wine_parse_result_complete_state() -> None:
    result = WineParseResult(
        original_text="완전한 와인 데이터",
        normalized_text="완전한 와인 데이터",
        confidence=1.0,
        wine_type="red",
        grape="cabernet_sauvignon",
        region="bordeaux",
        sweetness="dry",
        body="full",
        acidity="high",
    )

    assert result.matched_field_count == 6
    assert result.is_complete is True
    assert result.is_usable is True
