from __future__ import annotations

import pytest

from app.services.food.knowledge.coffee import (
    CoffeeBeanRegistry,
    CoffeeOriginRegistry,
    CoffeeParseResult,
    CoffeeParser,
    CoffeeProcessRegistry,
    CoffeeRoastRegistry,
)


def test_parser_registry_injection() -> None:
    bean_registry = CoffeeBeanRegistry()
    origin_registry = CoffeeOriginRegistry()
    roast_registry = CoffeeRoastRegistry()
    process_registry = CoffeeProcessRegistry()

    parser = CoffeeParser(
        bean_registry=bean_registry,
        origin_registry=origin_registry,
        roast_registry=roast_registry,
        process_registry=process_registry,
    )

    assert parser.bean_registry is bean_registry
    assert parser.origin_registry is origin_registry
    assert parser.roast_registry is roast_registry
    assert parser.process_registry is process_registry


def test_parse_complete_coffee_text() -> None:
    result = CoffeeParser().parse(
        "에티오피아 100% 아라비카 "
        "라이트 로스트 워시드 원두"
    )

    assert isinstance(
        result,
        CoffeeParseResult,
    )

    assert result.bean == "아라비카"
    assert result.origin == "에티오피아"
    assert result.roast == "라이트 로스트"
    assert result.process == "워시드"

    assert result.matched_field_count == 4
    assert result.is_complete is True
    assert result.is_usable is True
    assert result.confidence > 0.0
    assert result.warnings == []


def test_parse_product_uses_structured_fields() -> None:
    result = CoffeeParser().parse_product(
        {
            "product_name": "프리미엄 원두",
            "bean_type": "100% arabica",
            "origin_country": "Ethiopia",
            "roast_level": "medium light roast",
            "processing_method": "washed process",
            "option_name": "200g",
        }
    )

    assert result.bean == "아라비카"
    assert result.origin == "에티오피아"
    assert result.roast == (
        "미디엄 라이트 로스트"
    )
    assert result.process == "워시드"

    assert result.bean_match is not None
    assert result.bean_match.entry.registry_key == (
        "arabica"
    )
    assert result.origin_match.entry.registry_key == (
        "ethiopia"
    )
    assert result.roast_match.entry.registry_key == (
        "medium_light"
    )
    assert result.process_match.entry.registry_key == (
        "washed"
    )

    assert result.metadata["source_type"] == (
        "mapping"
    )
    assert (
        result.metadata[
            "structured_field_priority"
        ]
        is True
    )


def test_bean_only_is_usable() -> None:
    result = CoffeeParser().parse(
        "100% 아라비카 원두"
    )

    assert result.bean == "아라비카"
    assert result.is_usable is True
    assert result.is_complete is False
    assert result.warnings


def test_origin_only_is_not_usable() -> None:
    result = CoffeeParser().parse(
        "에티오피아 여행 상품"
    )

    assert result.origin == "에티오피아"
    assert result.bean is None
    assert result.is_usable is False


def test_origin_and_process_are_usable() -> None:
    result = CoffeeParser().parse(
        "에티오피아 워시드 커피"
    )

    assert result.origin == "에티오피아"
    assert result.process == "워시드"
    assert result.matched_field_count == 2
    assert result.is_usable is True


@pytest.mark.parametrize(
    ("text", "expected_bean"),
    [
        ("100% 아라비카 원두", "아라비카"),
        ("로부스타 커피", "로부스타"),
        ("리베리카 원두", "리베리카"),
        ("엑셀사 커피", "엑셀사"),
        (
            "아라비카 로부스타 블렌드",
            "아라비카 로부스타 블렌드",
        ),
    ],
)
def test_parser_bean_examples(
    text: str,
    expected_bean: str,
) -> None:
    result = CoffeeParser().parse(text)

    assert result.bean == expected_bean
    assert result.bean_match is not None


@pytest.mark.parametrize(
    ("text", "expected_origin"),
    [
        ("에티오피아 원두", "에티오피아"),
        ("콜롬비아산 커피", "콜롬비아"),
        ("브라질 원두", "브라질"),
        ("케냐 AA", "케냐"),
        ("과테말라 커피", "과테말라"),
        ("코스타리카 원두", "코스타리카"),
        ("수마트라 만델링", "인도네시아"),
    ],
)
def test_parser_origin_examples(
    text: str,
    expected_origin: str,
) -> None:
    result = CoffeeParser().parse(text)

    assert result.origin == expected_origin
    assert result.origin_match is not None


def test_parser_preserves_detected_aliases() -> None:
    result = CoffeeParser().parse(
        "에티오피아 100% 아라비카 "
        "라이트 로스트 워시드"
    )

    assert len(result.detected_keywords) == 4

    assert any(
        "아라비카" in keyword
        for keyword in result.detected_keywords
    )
    assert any(
        "에티오피아" in keyword
        for keyword in result.detected_keywords
    )
    assert any(
        "라이트" in keyword
        for keyword in result.detected_keywords
    )
    assert any(
        "워시드" in keyword
        for keyword in result.detected_keywords
    )


def test_roast_alias_boundary() -> None:
    medium_light = CoffeeParser().parse(
        "미디엄 라이트 로스트"
    )
    medium = CoffeeParser().parse(
        "미디엄 로스트"
    )
    medium_dark = CoffeeParser().parse(
        "미디엄 다크 로스트"
    )

    assert medium_light.roast == (
        "미디엄 라이트 로스트"
    )
    assert medium_light.roast_match.entry.registry_key == (
        "medium_light"
    )

    assert medium.roast == "미디엄 로스트"
    assert medium.roast_match.entry.registry_key == (
        "medium"
    )

    assert medium_dark.roast == (
        "미디엄 다크 로스트"
    )
    assert medium_dark.roast_match.entry.registry_key == (
        "medium_dark"
    )


def test_unknown_text_returns_unusable() -> None:
    result = CoffeeParser().parse(
        "상품 정보가 없는 일반 문자열"
    )

    assert result.bean is None
    assert result.origin is None
    assert result.roast is None
    assert result.process is None

    assert result.matched_field_count == 0
    assert result.confidence == 0.0
    assert result.is_usable is False
    assert result.warnings


@pytest.mark.parametrize(
    "text",
    [
        "국내산 한우 1++ 등심",
        "프랑스 브리 치즈",
        "훈제오리 슬라이스",
        "토종닭 가슴살",
        "양고기 프렌치랙",
    ],
)
def test_parser_non_coffee_boundary(
    text: str,
) -> None:
    result = CoffeeParser().parse(text)

    assert result.bean is None
    assert result.is_usable is False


def test_parse_product_deduplicates_text() -> None:
    result = CoffeeParser().parse_product(
        {
            "product_name": "아라비카 원두",
            "title": "아라비카 원두",
            "bean_type": "아라비카 원두",
        }
    )

    assert result.original_text == (
        "아라비카 원두"
    )
    assert result.bean == "아라비카"


def test_parse_product_source_fields() -> None:
    result = CoffeeParser().parse_product(
        {
            "product_name": "프리미엄 원두",
            "origin": "에티오피아",
            "roast_level": "라이트 로스트",
        }
    )

    assert result.metadata["source_fields"] == [
        "product_name",
        "origin",
        "roast_level",
    ]


def test_confidences_are_bounded() -> None:
    result = CoffeeParser().parse(
        "에티오피아 아라비카 원두"
    )

    for confidence in (
        result.confidence,
        result.bean_confidence,
        result.origin_confidence,
        result.roast_confidence,
        result.process_confidence,
    ):
        assert 0.0 <= confidence <= 1.0


def test_parse_rejects_empty_text() -> None:
    with pytest.raises(
        ValueError,
        match="must not be empty",
    ):
        CoffeeParser().parse("")


def test_parse_product_rejects_non_mapping() -> None:
    with pytest.raises(
        TypeError,
        match="product must be a Mapping",
    ):
        CoffeeParser().parse_product(
            "아라비카"  # type: ignore[arg-type]
        )


def test_parse_product_rejects_empty_mapping() -> None:
    with pytest.raises(
        ValueError,
        match="product must not be empty",
    ):
        CoffeeParser().parse_product({})


def test_parse_product_rejects_no_usable_fields() -> None:
    with pytest.raises(
        ValueError,
        match="usable text field",
    ):
        CoffeeParser().parse_product(
            {
                "price": 10000,
                "review_count": 10,
            }
        )


def test_parsing_is_deterministic() -> None:
    parser = CoffeeParser()
    text = (
        "에티오피아 100% 아라비카 "
        "라이트 로스트 워시드"
    )

    first = parser.parse(text)
    second = parser.parse(text)

    assert first.to_dict() == second.to_dict()
    assert first is not second
