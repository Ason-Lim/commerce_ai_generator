from __future__ import annotations

import pytest

from app.services.food.knowledge.tea import (
    TeaParseResult,
    TeaParser,
)
from app.services.food.knowledge.tea.flavor_registry import (
    TeaFlavorRegistry,
)
from app.services.food.knowledge.tea.origin_registry import (
    TeaOriginRegistry,
)
from app.services.food.knowledge.tea.oxidation_registry import (
    TeaOxidationRegistry,
)
from app.services.food.knowledge.tea.processing_registry import (
    TeaProcessingRegistry,
)
from app.services.food.knowledge.tea.type_registry import (
    TeaTypeRegistry,
)
from app.services.food.knowledge.tea.variety_registry import (
    TeaVarietyRegistry,
)


def test_parser_registry_injection() -> None:
    type_registry = TeaTypeRegistry()
    origin_registry = TeaOriginRegistry()
    variety_registry = TeaVarietyRegistry()
    processing_registry = TeaProcessingRegistry()
    oxidation_registry = TeaOxidationRegistry()
    flavor_registry = TeaFlavorRegistry()

    parser = TeaParser(
        type_registry=type_registry,
        origin_registry=origin_registry,
        variety_registry=variety_registry,
        processing_registry=processing_registry,
        oxidation_registry=oxidation_registry,
        flavor_registry=flavor_registry,
    )

    assert parser.type_registry is type_registry
    assert parser.origin_registry is origin_registry
    assert parser.variety_registry is variety_registry
    assert (
        parser.processing_registry
        is processing_registry
    )
    assert (
        parser.oxidation_registry
        is oxidation_registry
    )
    assert parser.flavor_registry is flavor_registry


def test_parse_complete_tea_text() -> None:
    result = TeaParser().parse(
        "다즐링 야부키타 증제 "
        "부분 산화 꽃향 우롱차"
    )

    assert isinstance(
        result,
        TeaParseResult,
    )

    assert result.tea_type == "oolong"
    assert result.origin == "darjeeling"
    assert result.variety == "yabukita"
    assert result.processing == "steamed"
    assert result.oxidation == "medium"
    assert result.flavor == "floral"

    assert result.matched_field_count == 6
    assert result.is_complete is True
    assert result.is_usable is True
    assert result.confidence > 0.0
    assert result.warnings == []


def test_parse_product_uses_structured_fields() -> None:
    result = TeaParser().parse_product(
        {
            "product_name": "프리미엄 차",
            "tea_type": "green tea",
            "origin": "Jeju",
            "cultivar": "Yabukita",
            "processing_method": "steamed tea",
            "oxidation_level": "unoxidized",
            "flavor_notes": "umami",
            "option_name": "100g",
        }
    )

    assert result.tea_type == "green"
    assert result.origin == "jeju"
    assert result.variety == "yabukita"
    assert result.processing == "steamed"
    assert result.oxidation == "unoxidized"
    assert result.flavor == "umami"

    assert result.metadata["source_type"] == (
        "mapping"
    )
    assert (
        result.metadata[
            "structured_field_priority"
        ]
        is True
    )


def test_structured_field_has_priority_over_name() -> None:
    result = TeaParser().parse_product(
        {
            "product_name": "홍차",
            "tea_type": "green tea",
        }
    )

    assert result.tea_type == "green"
    assert result.tea_type_match is not None
    assert (
        result.tea_type_match.entry.registry_key
        == "green"
    )


@pytest.mark.parametrize(
    (
        "text",
        "field_name",
        "expected",
    ),
    [
        (
            "우롱차",
            "tea_type",
            "oolong",
        ),
        (
            "다즐링 차",
            "origin",
            "darjeeling",
        ),
        (
            "야부키타 녹차",
            "variety",
            "yabukita",
        ),
        (
            "증제 녹차",
            "processing",
            "steamed",
        ),
        (
            "부분 산화 우롱차",
            "oxidation",
            "medium",
        ),
        (
            "꽃향 우롱차",
            "flavor",
            "floral",
        ),
    ],
)
def test_parser_detects_each_registry_field(
    text: str,
    field_name: str,
    expected: str,
) -> None:
    result = TeaParser().parse(text)

    assert (
        getattr(result, field_name)
        == expected
    )


def test_type_only_is_usable() -> None:
    result = TeaParser().parse(
        "프리미엄 우롱차"
    )

    assert result.tea_type == "oolong"
    assert result.is_usable is True
    assert result.is_complete is False
    assert result.warnings


def test_origin_only_is_not_usable() -> None:
    result = TeaParser().parse(
        "다즐링 여행 상품"
    )

    assert result.origin == "darjeeling"
    assert result.tea_type is None
    assert result.is_usable is False
    assert result.warnings


def test_two_supporting_fields_are_usable() -> None:
    result = TeaParser().parse(
        "다즐링 꽃향 상품"
    )

    assert result.origin == "darjeeling"
    assert result.flavor == "floral"
    assert result.matched_field_count == 2
    assert result.is_usable is True


def test_detected_keywords_are_preserved() -> None:
    result = TeaParser().parse(
        "제주 야부키타 증제 "
        "비산화 감칠맛 녹차"
    )

    assert len(result.detected_keywords) == 6

    assert "제주" in result.detected_keywords
    assert "야부키타" in result.detected_keywords
    assert "증제" in result.detected_keywords
    assert "비산화" in result.detected_keywords
    assert "감칠맛" in result.detected_keywords
    assert "녹차" in result.detected_keywords


def test_unknown_text_returns_unusable() -> None:
    result = TeaParser().parse(
        "상품 정보가 없는 일반 문자열"
    )

    assert result.tea_type is None
    assert result.origin is None
    assert result.variety is None
    assert result.processing is None
    assert result.oxidation is None
    assert result.flavor is None

    assert result.matched_field_count == 0
    assert result.confidence == 0.0
    assert result.has_match is False
    assert result.is_usable is False
    assert result.warnings


@pytest.mark.parametrize(
    "text",
    [
        "한우 1++ 등심 500g",
        "프랑스 브리 치즈",
        "에티오피아 아라비카 원두",
        "훈제오리 슬라이스",
        "카베르네 소비뇽 레드 와인",
    ],
)
def test_parser_non_tea_boundary(
    text: str,
) -> None:
    result = TeaParser().parse(text)

    assert result.tea_type is None
    assert result.is_usable is False


def test_parse_product_deduplicates_text() -> None:
    result = TeaParser().parse_product(
        {
            "product_name": "제주 녹차",
            "title": "제주 녹차",
            "tea_type": "녹차",
        }
    )

    assert result.original_text == (
        "제주 녹차 녹차"
    )
    assert result.tea_type == "green"
    assert result.origin == "jeju"


def test_parse_product_source_fields() -> None:
    result = TeaParser().parse_product(
        {
            "product_name": "프리미엄 차",
            "origin": "제주",
            "processing": "증제",
        }
    )

    assert result.metadata["source_fields"] == [
        "product_name",
        "origin",
        "processing",
    ]


def test_parser_metadata_contract() -> None:
    result = TeaParser().parse(
        "제주 녹차"
    )

    assert result.metadata["category_id"] == "tea"
    assert result.metadata["source_type"] == "text"
    assert result.metadata[
        "structured_field_priority"
    ] is False
    assert result.metadata[
        "expected_field_count"
    ] == 6
    assert result.metadata[
        "matched_field_count"
    ] == 2
    assert result.metadata["is_complete"] is False


def test_confidences_are_bounded() -> None:
    result = TeaParser().parse(
        "제주 야부키타 증제 녹차"
    )

    for confidence in (
        result.confidence,
        result.tea_type_confidence,
        result.origin_confidence,
        result.variety_confidence,
        result.processing_confidence,
        result.oxidation_confidence,
        result.flavor_confidence,
    ):
        assert 0.0 <= confidence <= 1.0


def test_parse_rejects_empty_text() -> None:
    with pytest.raises(
        ValueError,
        match="must not be empty",
    ):
        TeaParser().parse("")


def test_parse_product_rejects_non_mapping() -> None:
    with pytest.raises(
        TypeError,
        match="product must be a Mapping",
    ):
        TeaParser().parse_product(
            "녹차"  # type: ignore[arg-type]
        )


def test_parse_product_rejects_empty_mapping() -> None:
    with pytest.raises(
        ValueError,
        match="product must not be empty",
    ):
        TeaParser().parse_product({})


def test_parse_product_rejects_no_usable_fields() -> None:
    with pytest.raises(
        ValueError,
        match="usable text field",
    ):
        TeaParser().parse_product(
            {
                "price": 10000,
                "review_count": 10,
            }
        )


def test_parsing_is_deterministic() -> None:
    parser = TeaParser()
    text = (
        "제주 야부키타 증제 "
        "비산화 감칠맛 녹차"
    )

    first = parser.parse(text)
    second = parser.parse(text)

    assert first.to_dict() == second.to_dict()
    assert first is not second
