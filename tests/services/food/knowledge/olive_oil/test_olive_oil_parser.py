from __future__ import annotations

import pytest

from app.services.food.knowledge.olive_oil import (
    OliveOilParseResult,
    OliveOilParser,
)
from app.services.food.knowledge.olive_oil.grade_registry import (
    OliveOilGradeRegistry,
)
from app.services.food.knowledge.olive_oil.origin_registry import (
    OliveOilOriginRegistry,
)
from app.services.food.knowledge.olive_oil.processing_registry import (
    OliveOilProcessingRegistry,
)
from app.services.food.knowledge.olive_oil.type_registry import (
    OliveOilTypeRegistry,
)
from app.services.food.knowledge.olive_oil.variety_registry import (
    OliveOilVarietyRegistry,
)


def test_parser_registry_injection() -> None:
    type_registry = OliveOilTypeRegistry()
    variety_registry = OliveOilVarietyRegistry()
    origin_registry = OliveOilOriginRegistry()
    processing_registry = (
        OliveOilProcessingRegistry()
    )
    grade_registry = OliveOilGradeRegistry()

    parser = OliveOilParser(
        type_registry=type_registry,
        variety_registry=variety_registry,
        origin_registry=origin_registry,
        processing_registry=processing_registry,
        grade_registry=grade_registry,
    )

    assert parser.type_registry is type_registry
    assert parser.variety_registry is variety_registry
    assert parser.origin_registry is origin_registry
    assert (
        parser.processing_registry
        is processing_registry
    )
    assert parser.grade_registry is grade_registry


def test_parse_complete_olive_oil_text() -> None:
    result = OliveOilParser().parse(
        "스페인산 아르베키나 단일 품종 "
        "냉압착 엑스트라 버진 올리브오일"
    )

    assert isinstance(
        result,
        OliveOilParseResult,
    )

    assert (
        result.olive_oil_type
        == "single_varietal"
    )
    assert result.variety == "arbequina"
    assert result.origin == "spain"
    assert result.processing == "cold_pressed"
    assert result.grade == "extra_virgin"

    assert result.matched_field_count == 5
    assert result.is_complete is True
    assert result.is_usable is True
    assert result.confidence > 0.0
    assert result.warnings == []


def test_parse_product_uses_structured_fields() -> None:
    result = OliveOilParser().parse_product(
        {
            "product_name": (
                "프리미엄 올리브오일"
            ),
            "olive_oil_type": (
                "single varietal"
            ),
            "cultivar": "Arbequina",
            "origin_country": "Spain",
            "extraction_method": (
                "cold pressed"
            ),
            "grade": (
                "extra virgin olive oil"
            ),
            "option_name": "500ml",
        }
    )

    assert (
        result.olive_oil_type
        == "single_varietal"
    )
    assert result.variety == "arbequina"
    assert result.origin == "spain"
    assert result.processing == "cold_pressed"
    assert result.grade == "extra_virgin"

    assert (
        result.metadata[
            "structured_field_priority"
        ]
        is True
    )
    assert result.metadata["source_type"] == (
        "mapping"
    )


def test_structured_grade_has_priority_over_name() -> None:
    result = OliveOilParser().parse_product(
        {
            "product_name": (
                "일반 버진 올리브오일"
            ),
            "grade": (
                "extra virgin olive oil"
            ),
        }
    )

    assert result.grade == "extra_virgin"
    assert result.grade_match is not None
    assert (
        result.grade_match.entry.registry_key
        == "extra_virgin"
    )


@pytest.mark.parametrize(
    (
        "text",
        "field_name",
        "expected",
    ),
    [
        (
            "단일 품종 올리브오일",
            "olive_oil_type",
            "single_varietal",
        ),
        (
            "아르베키나 올리브오일",
            "variety",
            "arbequina",
        ),
        (
            "그리스산 올리브오일",
            "origin",
            "greece",
        ),
        (
            "냉압착 올리브오일",
            "processing",
            "cold_pressed",
        ),
        (
            "엑스트라 버진 올리브오일",
            "grade",
            "extra_virgin",
        ),
    ],
)
def test_parser_detects_each_registry_field(
    text: str,
    field_name: str,
    expected: str,
) -> None:
    result = OliveOilParser().parse(
        text
    )

    assert (
        getattr(result, field_name)
        == expected
    )


def test_grade_only_is_usable() -> None:
    result = OliveOilParser().parse(
        "엑스트라 버진"
    )

    assert result.grade == "extra_virgin"
    assert result.matched_field_count == 1
    assert result.is_usable is True
    assert result.is_complete is False
    assert result.warnings


def test_type_only_is_usable() -> None:
    result = OliveOilParser().parse(
        "단일 품종 상품"
    )

    assert (
        result.olive_oil_type
        == "single_varietal"
    )
    assert result.is_usable is True
    assert result.is_complete is False


def test_origin_only_is_not_usable() -> None:
    result = OliveOilParser().parse(
        "스페인 여행 상품"
    )

    assert result.origin == "spain"
    assert result.grade is None
    assert result.olive_oil_type is None
    assert result.is_usable is False
    assert result.warnings


def test_two_supporting_fields_are_usable() -> None:
    result = OliveOilParser().parse(
        "스페인 아르베키나 상품"
    )

    assert result.origin == "spain"
    assert result.variety == "arbequina"
    assert result.matched_field_count == 2
    assert result.is_usable is True


def test_detected_keywords_are_preserved() -> None:
    result = OliveOilParser().parse(
        "스페인산 아르베키나 냉압착 "
        "엑스트라 버진 올리브오일"
    )

    assert "스페인산" in result.detected_keywords
    assert "아르베키나" in result.detected_keywords
    assert "냉압착" in result.detected_keywords
    assert (
        "엑스트라 버진 올리브오일"
        in result.detected_keywords
    )


def test_unknown_text_returns_unusable() -> None:
    result = OliveOilParser().parse(
        "상품 정보가 없는 일반 문자열"
    )

    assert result.olive_oil_type is None
    assert result.variety is None
    assert result.origin is None
    assert result.processing is None
    assert result.grade is None

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
        "제주 녹차",
    ],
)
def test_parser_non_olive_oil_boundary(
    text: str,
) -> None:
    result = OliveOilParser().parse(
        text
    )

    assert result.olive_oil_type is None
    assert result.grade is None
    assert result.is_usable is False


def test_parse_product_deduplicates_text() -> None:
    result = OliveOilParser().parse_product(
        {
            "product_name": (
                "스페인 올리브오일"
            ),
            "title": (
                "스페인 올리브오일"
            ),
            "grade": (
                "엑스트라 버진"
            ),
        }
    )

    assert result.original_text == (
        "스페인 올리브오일 엑스트라 버진"
    )
    assert result.origin == "spain"
    assert result.grade == "extra_virgin"


def test_parse_product_source_fields() -> None:
    result = OliveOilParser().parse_product(
        {
            "product_name": (
                "프리미엄 올리브오일"
            ),
            "origin": "스페인",
            "processing": "냉압착",
        }
    )

    assert result.metadata["source_fields"] == [
        "product_name",
        "origin",
        "processing",
    ]


def test_parser_metadata_contract() -> None:
    result = OliveOilParser().parse(
        "스페인 엑스트라 버진 올리브오일"
    )

    assert (
        result.metadata["category_id"]
        == "olive_oil"
    )
    assert (
        result.metadata["source_type"]
        == "text"
    )
    assert (
        result.metadata[
            "structured_field_priority"
        ]
        is False
    )
    assert (
        result.metadata[
            "expected_field_count"
        ]
        == 5
    )
    assert (
        result.metadata[
            "matched_field_count"
        ]
        >= 2
    )


def test_confidences_are_bounded() -> None:
    result = OliveOilParser().parse(
        "스페인 아르베키나 냉압착 "
        "엑스트라 버진 올리브오일"
    )

    for confidence in (
        result.confidence,
        result.olive_oil_type_confidence,
        result.variety_confidence,
        result.origin_confidence,
        result.processing_confidence,
        result.grade_confidence,
    ):
        assert 0.0 <= confidence <= 1.0


def test_parse_rejects_empty_text() -> None:
    with pytest.raises(
        ValueError,
        match="must not be empty",
    ):
        OliveOilParser().parse("")


def test_parse_product_rejects_non_mapping() -> None:
    with pytest.raises(
        TypeError,
        match="product must be a Mapping",
    ):
        OliveOilParser().parse_product(
            "olive oil"  # type: ignore[arg-type]
        )


def test_parse_product_rejects_empty_mapping() -> None:
    with pytest.raises(
        ValueError,
        match="product must not be empty",
    ):
        OliveOilParser().parse_product({})


def test_parse_product_rejects_no_usable_fields() -> None:
    with pytest.raises(
        ValueError,
        match="usable text field",
    ):
        OliveOilParser().parse_product(
            {
                "price": 10000,
                "review_count": 10,
            }
        )


def test_parsing_is_deterministic() -> None:
    parser = OliveOilParser()
    text = (
        "스페인산 아르베키나 단일 품종 "
        "냉압착 엑스트라 버진 올리브오일"
    )

    first = parser.parse(text)
    second = parser.parse(text)

    assert first.to_dict() == second.to_dict()
    assert first is not second
