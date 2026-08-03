from __future__ import annotations

from app.services.food.knowledge.cheese import (
    CheeseParseResult,
)


def test_empty_cheese_parse_result() -> None:
    result = CheeseParseResult(
        original_text="일반 상품",
        normalized_text="일반 상품",
    )

    assert result.cheese_type is None
    assert result.milk_source is None
    assert result.origin is None
    assert result.texture is None
    assert result.aging is None

    assert result.matched_field_count == 0
    assert result.has_match is False
    assert result.is_complete is False
    assert result.is_usable is False


def test_cheese_type_only_is_usable() -> None:
    result = CheeseParseResult(
        original_text="체다치즈",
        normalized_text="체다치즈",
        confidence=1.0,
        cheese_type="체다",
        cheese_type_confidence=1.0,
    )

    assert result.has_cheese_type is True
    assert result.matched_field_count == 1
    assert result.is_complete is False
    assert result.is_usable is True


def test_milk_source_only_is_not_usable() -> None:
    result = CheeseParseResult(
        original_text="산양유",
        normalized_text="산양유",
        confidence=1.0,
        milk_source="산양유",
        milk_source_confidence=1.0,
    )

    assert result.has_milk_source is True
    assert result.matched_field_count == 1
    assert result.is_usable is False


def test_two_supporting_fields_are_usable() -> None:
    result = CheeseParseResult(
        original_text="프랑스 장기숙성",
        normalized_text="프랑스 장기숙성",
        confidence=1.0,
        origin="프랑스",
        aging="장기숙성",
        origin_confidence=1.0,
        aging_confidence=1.0,
    )

    assert result.matched_field_count == 2
    assert result.is_usable is True


def test_complete_cheese_parse_result() -> None:
    result = CheeseParseResult(
        original_text=(
            "프랑스 산양유 브리 "
            "연성 장기숙성"
        ),
        normalized_text=(
            "프랑스 산양유 브리 "
            "연성 장기숙성"
        ),
        confidence=1.0,
        cheese_type="브리",
        milk_source="산양유",
        origin="프랑스",
        texture="연성",
        aging="장기숙성",
        cheese_type_confidence=1.0,
        milk_source_confidence=1.0,
        origin_confidence=1.0,
        texture_confidence=1.0,
        aging_confidence=1.0,
    )

    assert result.matched_field_count == 5
    assert result.is_complete is True
    assert result.is_usable is True


def test_parse_result_clamps_confidence() -> None:
    result = CheeseParseResult(
        original_text="체다",
        normalized_text="체다",
        confidence=2.0,
        cheese_type_confidence=-1.0,
        origin_confidence=3.0,
    )

    assert result.confidence == 1.0
    assert result.cheese_type_confidence == 0.0
    assert result.origin_confidence == 1.0


def test_parse_result_deduplicates_evidence() -> None:
    result = CheeseParseResult(
        original_text="체다",
        normalized_text="체다",
        detected_keywords=[
            "체다",
            "체다",
            "",
        ],
        warnings=[
            "경고",
            "경고",
            " ",
        ],
    )

    assert result.detected_keywords == ["체다"]
    assert result.warnings == ["경고"]


def test_cheese_parse_result_serializes() -> None:
    result = CheeseParseResult(
        original_text="체다치즈",
        normalized_text="체다치즈",
        confidence=0.9,
        cheese_type="체다",
        cheese_type_confidence=0.9,
        detected_keywords=["체다치즈"],
    )

    payload = result.to_dict()

    assert payload["cheese_type"] == "체다"
    assert payload["matched_field_count"] == 1
    assert payload["is_complete"] is False
    assert payload["is_usable"] is True
    assert payload["detected_keywords"] == [
        "체다치즈",
    ]
