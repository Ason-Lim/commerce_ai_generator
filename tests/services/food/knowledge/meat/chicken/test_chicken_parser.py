from __future__ import annotations

import pytest

from app.services.food.knowledge.meat.chicken.parser import (
    ChickenParser,
)
from app.services.food.knowledge.meat.chicken.parser_models import (
    ChickenParseResult,
)


def test_parse_complete_chicken_product() -> None:
    result = ChickenParser().parse(
        "토종닭 Ross 308 닭다리살 500g"
    )

    assert isinstance(result, ChickenParseResult)
    assert result.chicken_type == "토종닭"
    assert result.breed == "로스 308"
    assert result.cut == "닭다리살"
    assert result.is_complete is True
    assert result.is_usable is True
    assert result.metadata["category_id"] == "chicken"
    assert result.metadata["matched_field_count"] == 3
    assert result.confidence > 0.0


def test_parse_product_uses_structured_fields() -> None:
    result = ChickenParser().parse_product(
        {
            "product_name": "국내산 닭고기",
            "chicken_type": "영계",
            "chicken_breed": "Cobb 500",
            "cut": "닭안심",
            "option_name": "냉장 500g",
        }
    )

    assert result.chicken_type == "영계"
    assert result.breed == "코브 500"
    assert result.cut == "닭안심"
    assert result.metadata["source_type"] == "mapping"
    assert "product_name" in result.metadata[
        "source_fields"
    ]
    assert "chicken_type" in result.metadata[
        "source_fields"
    ]
    assert "chicken_breed" in result.metadata[
        "source_fields"
    ]
    assert "cut" in result.metadata[
        "source_fields"
    ]


def test_parse_cut_only_is_usable_but_incomplete() -> None:
    result = ChickenParser().parse(
        "국내산 닭가슴살 1kg"
    )

    assert result.chicken_type is None
    assert result.breed is None
    assert result.cut == "닭가슴살"
    assert result.is_complete is False
    assert result.is_usable is True
    assert result.metadata["matched_field_count"] == 1


def test_parse_breed_only_is_not_usable() -> None:
    result = ChickenParser().parse(
        "Arbor Acres"
    )

    assert result.breed == "아버 에이커스"
    assert result.chicken_type is None
    assert result.cut is None
    assert result.is_complete is False
    assert result.is_usable is False


def test_parser_preserves_detected_aliases() -> None:
    result = ChickenParser().parse(
        "오골계 닭근위"
    )

    assert "오골계" in result.detected_keywords
    assert "닭근위" in result.detected_keywords


def test_parser_does_not_infer_ambiguous_cut() -> None:
    result = ChickenParser().parse(
        "국내산 닭다리 500g"
    )

    assert result.cut is None


def test_parser_does_not_match_other_meat_cut() -> None:
    result = ChickenParser().parse(
        "한우 안심 스테이크"
    )

    assert result.chicken_type is None
    assert result.breed is None
    assert result.cut is None
    assert result.is_usable is False


def test_parse_product_rejects_non_mapping() -> None:
    with pytest.raises(
        TypeError,
        match="product must be a Mapping",
    ):
        ChickenParser().parse_product(  # type: ignore[arg-type]
            "닭가슴살"
        )


def test_parse_product_rejects_empty_mapping() -> None:
    with pytest.raises(
        ValueError,
        match="usable text field",
    ):
        ChickenParser().parse_product({})
