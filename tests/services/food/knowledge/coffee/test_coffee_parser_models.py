from __future__ import annotations

from app.services.food.knowledge.coffee import (
    CoffeeParseResult,
)


def test_empty_coffee_parse_result() -> None:
    result = CoffeeParseResult(
        original_text="일반 상품",
        normalized_text="일반 상품",
    )

    assert result.bean is None
    assert result.origin is None
    assert result.roast is None
    assert result.process is None

    assert result.matched_field_count == 0
    assert result.has_match is False
    assert result.is_complete is False
    assert result.is_usable is False


def test_bean_only_is_usable() -> None:
    result = CoffeeParseResult(
        original_text="아라비카",
        normalized_text="아라비카",
        confidence=1.0,
        bean="아라비카",
        bean_confidence=1.0,
    )

    assert result.has_bean is True
    assert result.matched_field_count == 1
    assert result.is_usable is True


def test_origin_only_is_not_usable() -> None:
    result = CoffeeParseResult(
        original_text="에티오피아",
        normalized_text="에티오피아",
        confidence=1.0,
        origin="에티오피아",
        origin_confidence=1.0,
    )

    assert result.has_origin is True
    assert result.matched_field_count == 1
    assert result.is_usable is False


def test_two_supporting_fields_are_usable() -> None:
    result = CoffeeParseResult(
        original_text="에티오피아 워시드",
        normalized_text="에티오피아 워시드",
        origin="에티오피아",
        process="워시드",
        origin_confidence=1.0,
        process_confidence=1.0,
    )

    assert result.matched_field_count == 2
    assert result.is_usable is True


def test_complete_parse_result() -> None:
    result = CoffeeParseResult(
        original_text=(
            "에티오피아 아라비카 "
            "라이트 로스트 워시드"
        ),
        normalized_text=(
            "에티오피아 아라비카 "
            "라이트 로스트 워시드"
        ),
        confidence=1.0,
        bean="아라비카",
        origin="에티오피아",
        roast="라이트 로스트",
        process="워시드",
        bean_confidence=1.0,
        origin_confidence=1.0,
        roast_confidence=1.0,
        process_confidence=1.0,
    )

    assert result.matched_field_count == 4
    assert result.is_complete is True
    assert result.is_usable is True


def test_confidences_are_clamped() -> None:
    result = CoffeeParseResult(
        original_text="아라비카",
        normalized_text="아라비카",
        confidence=2.0,
        bean_confidence=-1.0,
        origin_confidence=3.0,
    )

    assert result.confidence == 1.0
    assert result.bean_confidence == 0.0
    assert result.origin_confidence == 1.0


def test_evidence_is_deduplicated() -> None:
    result = CoffeeParseResult(
        original_text="아라비카",
        normalized_text="아라비카",
        detected_keywords=[
            "아라비카",
            "아라비카",
            "",
        ],
        warnings=[
            "경고",
            "경고",
            " ",
        ],
    )

    assert result.detected_keywords == [
        "아라비카",
    ]
    assert result.warnings == ["경고"]


def test_parse_result_serializes() -> None:
    result = CoffeeParseResult(
        original_text="아라비카 원두",
        normalized_text="아라비카 원두",
        confidence=0.9,
        bean="아라비카",
        bean_confidence=0.9,
        detected_keywords=["아라비카"],
    )

    payload = result.to_dict()

    assert payload["bean"] == "아라비카"
    assert payload["matched_field_count"] == 1
    assert payload["is_complete"] is False
    assert payload["is_usable"] is True
