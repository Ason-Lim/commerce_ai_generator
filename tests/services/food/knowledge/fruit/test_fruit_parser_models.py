from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from app.services.food.knowledge.common.parser_models import (
    BaseParseResult,
)
from app.services.food.knowledge.fruit.parser_models import (
    FruitParseResult,
)


def test_empty_fruit_parse_result() -> None:
    result = FruitParseResult(
        original_text="일반 상품",
        normalized_text="일반 상품",
    )

    assert isinstance(
        result,
        BaseParseResult,
    )
    assert result.origin is None
    assert result.variety is None
    assert result.grade is None
    assert result.brix is None
    assert result.weight_grams is None

    assert result.matched_field_count == 0
    assert result.has_match is False
    assert result.is_complete is False
    assert result.is_usable is False


def test_fruit_parse_result_with_fields() -> None:
    result = FruitParseResult(
        original_text=(
            "고당도 제주 감귤 12브릭스 2kg"
        ),
        normalized_text=(
            "고당도 제주 감귤 12브릭스 2kg"
        ),
        confidence=0.9,
        origin="제주",
        variety="감귤",
        grade="특품",
        brix=12.0,
        weight_grams=2000.0,
        detected_keywords=[
            "고당도",
        ],
    )

    assert result.has_match is True
    assert result.is_complete is True
    assert result.is_usable is True
    assert result.matched_field_count == 5


def test_confidence_is_clamped() -> None:
    result = FruitParseResult(
        original_text="사과",
        normalized_text="사과",
        confidence=3.0,
    )

    assert result.confidence == 1.0


def test_fruit_parse_result_is_frozen() -> None:
    result = FruitParseResult(
        original_text="사과",
        normalized_text="사과",
    )

    with pytest.raises(
        FrozenInstanceError,
    ):
        result.origin = "대한민국"  # type: ignore[misc]


def test_fruit_parse_result_serializes() -> None:
    result = FruitParseResult(
        original_text="고당도 사과",
        normalized_text="고당도 사과",
        confidence=0.8,
        variety="사과",
        detected_keywords=[
            "고당도",
        ],
    )

    payload = result.to_dict()

    assert payload["variety"] == "사과"
    assert payload["confidence"] == 0.8
    assert payload[
        "detected_keywords"
    ] == ["고당도"]
    assert payload[
        "matched_field_count"
    ] == 1
    assert payload["is_usable"] is True
