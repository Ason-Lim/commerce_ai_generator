from __future__ import annotations

import pytest

from app.services.food.knowledge.cheese import (
    CheeseAgingRegistry,
    CheeseMilkSourceRegistry,
    CheeseOriginRegistry,
    CheeseParser,
    CheeseParseResult,
    CheeseTextureRegistry,
    CheeseTypeRegistry,
)


def test_parser_registry_injection() -> None:
    type_registry = CheeseTypeRegistry()
    milk_registry = CheeseMilkSourceRegistry()
    origin_registry = CheeseOriginRegistry()
    texture_registry = CheeseTextureRegistry()
    aging_registry = CheeseAgingRegistry()

    parser = CheeseParser(
        type_registry=type_registry,
        milk_source_registry=milk_registry,
        origin_registry=origin_registry,
        texture_registry=texture_registry,
        aging_registry=aging_registry,
    )

    assert parser.type_registry is type_registry
    assert (
        parser.milk_source_registry
        is milk_registry
    )
    assert parser.origin_registry is origin_registry
    assert (
        parser.texture_registry
        is texture_registry
    )
    assert parser.aging_registry is aging_registry


def test_parse_complete_cheese_text() -> None:
    result = CheeseParser().parse(
        "프랑스 산양유 브리 "
        "부드러운 치즈 12개월 숙성"
    )

    assert isinstance(
        result,
        CheeseParseResult,
    )

    assert result.cheese_type == "브리"
    assert result.milk_source == "산양유"
    assert result.origin == "프랑스"
    assert result.texture == "연성"
    assert result.aging == "장기숙성"

    assert result.matched_field_count == 5
    assert result.is_complete is True
    assert result.is_usable is True
    assert result.confidence > 0.0
    assert result.warnings == []


def test_parse_product_uses_structured_fields() -> None:
    result = CheeseParser().parse_product(
        {
            "product_name": "프리미엄 치즈",
            "cheese_type": "parmigiano reggiano",
            "milk_source": "cow milk",
            "origin_country": "Italy",
            "texture": "hard cheese",
            "aging": "24개월 숙성",
            "option_name": "200g",
        }
    )

    assert result.cheese_type == (
        "파르미자노 레지아노"
    )
    assert result.milk_source == "우유"
    assert result.origin == "이탈리아"
    assert result.texture == "경질"
    assert result.aging == "초장기숙성"

    assert (
        result.cheese_type_match
        is not None
    )
    assert (
        result.cheese_type_match
        .entry
        .registry_key
        == "parmesan"
    )
    assert (
        result.milk_source_match
        .entry
        .registry_key
        == "cow"
    )
    assert (
        result.origin_match
        .entry
        .registry_key
        == "italy"
    )
    assert (
        result.texture_match
        .entry
        .registry_key
        == "hard"
    )
    assert (
        result.aging_match
        .entry
        .registry_key
        == "extra_aged"
    )

    assert (
        result.metadata["source_type"]
        == "mapping"
    )
    assert (
        result.metadata[
            "structured_field_priority"
        ]
        is True
    )


def test_parse_type_only_is_usable() -> None:
    result = CheeseParser().parse(
        "플레인 크림치즈 200g"
    )

    assert result.cheese_type == "크림치즈"
    assert result.is_usable is True
    assert result.is_complete is False
    assert result.warnings


def test_parse_milk_only_is_not_usable() -> None:
    result = CheeseParser().parse(
        "산양유 1L"
    )

    assert result.milk_source == "산양유"
    assert result.cheese_type is None
    assert result.is_usable is False


def test_parse_origin_and_aging_is_usable() -> None:
    result = CheeseParser().parse(
        "프랑스산 12개월 숙성"
    )

    assert result.origin == "프랑스"
    assert result.aging == "장기숙성"
    assert result.matched_field_count == 2
    assert result.is_usable is True


@pytest.mark.parametrize(
    ("text", "expected_type"),
    [
        ("이탈리아 모짜렐라", "모차렐라"),
        ("숙성 체다치즈", "체다"),
        ("프랑스 까망베르", "카망베르"),
        ("네덜란드 고다", "고다"),
        (
            "파르미자노 레지아노",
            "파르미자노 레지아노",
        ),
        ("블루 치즈 소스용", "블루치즈"),
    ],
)
def test_parser_cheese_type_examples(
    text: str,
    expected_type: str,
) -> None:
    result = CheeseParser().parse(text)

    assert result.cheese_type == expected_type
    assert result.cheese_type_match is not None


def test_parser_preserves_detected_aliases() -> None:
    result = CheeseParser().parse(
        "프랑스 산양유 브리 "
        "소프트 치즈 12개월 숙성"
    )

    assert len(result.detected_keywords) == 5

    assert any(
        "브리" in keyword
        for keyword in result.detected_keywords
    )
    assert any(
        "산양" in keyword
        for keyword in result.detected_keywords
    )
    assert any(
        "프랑스" in keyword
        for keyword in result.detected_keywords
    )
    assert any(
        "소프트" in keyword
        for keyword in result.detected_keywords
    )
    assert any(
        "12개월" in keyword
        for keyword in result.detected_keywords
    )


def test_parser_texture_alias_boundary() -> None:
    semi_hard = CheeseParser().parse(
        "세미 하드 치즈"
    )
    hard = CheeseParser().parse(
        "단단한 하드치즈"
    )

    assert semi_hard.texture == "반경질"
    assert (
        semi_hard.texture_match
        .entry
        .registry_key
        == "semi_hard"
    )

    assert hard.texture == "경질"
    assert (
        hard.texture_match
        .entry
        .registry_key
        == "hard"
    )


def test_parser_unknown_text_returns_unusable() -> None:
    result = CheeseParser().parse(
        "상품 정보가 없는 일반 문자열"
    )

    assert result.cheese_type is None
    assert result.milk_source is None
    assert result.origin is None
    assert result.texture is None
    assert result.aging is None

    assert result.matched_field_count == 0
    assert result.confidence == 0.0
    assert result.is_usable is False
    assert result.warnings


@pytest.mark.parametrize(
    "text",
    [
        "한우 1++ 등심 500g",
        "양고기 프렌치랙",
        "훈제오리 슬라이스",
        "닭가슴살 1kg",
        "사슴 안심 스테이크",
    ],
)
def test_parser_non_cheese_boundary(
    text: str,
) -> None:
    result = CheeseParser().parse(text)

    assert result.cheese_type is None
    assert result.is_usable is False


def test_parse_product_deduplicates_text() -> None:
    result = CheeseParser().parse_product(
        {
            "product_name": "체다치즈",
            "title": "체다치즈",
            "cheese_type": "체다치즈",
        }
    )

    assert result.original_text == "체다치즈"
    assert result.cheese_type == "체다"


def test_parse_product_source_fields() -> None:
    result = CheeseParser().parse_product(
        {
            "product_name": "브리 치즈",
            "country": "프랑스",
            "aging": "단기 숙성",
        }
    )

    assert result.metadata["source_fields"] == [
        "product_name",
        "country",
        "aging",
    ]


def test_parser_confidences_are_bounded() -> None:
    result = CheeseParser().parse(
        "프랑스 브리 치즈"
    )

    for confidence in (
        result.confidence,
        result.cheese_type_confidence,
        result.milk_source_confidence,
        result.origin_confidence,
        result.texture_confidence,
        result.aging_confidence,
    ):
        assert 0.0 <= confidence <= 1.0


def test_parse_rejects_empty_text() -> None:
    with pytest.raises(
        ValueError,
        match="must not be empty",
    ):
        CheeseParser().parse("")


def test_parse_product_rejects_non_mapping() -> None:
    with pytest.raises(
        TypeError,
        match="product must be a Mapping",
    ):
        CheeseParser().parse_product(
            "체다치즈"  # type: ignore[arg-type]
        )


def test_parse_product_rejects_empty_mapping() -> None:
    with pytest.raises(
        ValueError,
        match="product must not be empty",
    ):
        CheeseParser().parse_product({})


def test_parse_product_rejects_no_usable_fields() -> None:
    with pytest.raises(
        ValueError,
        match="usable text field",
    ):
        CheeseParser().parse_product(
            {
                "price": 10000,
                "review_count": 10,
            }
        )


def test_parsing_is_deterministic() -> None:
    parser = CheeseParser()
    text = (
        "프랑스 산양유 브리 "
        "소프트 치즈 12개월 숙성"
    )

    first = parser.parse(text)
    second = parser.parse(text)

    assert first.to_dict() == second.to_dict()
    assert first is not second
