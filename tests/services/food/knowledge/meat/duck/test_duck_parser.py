from __future__ import annotations

import pytest

from app.services.food.knowledge.meat.duck.parser import (
    DuckParser,
)
from app.services.food.knowledge.meat.duck.parser_models import (
    DuckParseResult,
)


def test_parse_complete_duck_product() -> None:
    result = DuckParser().parse(
        "훈제오리 체리밸리 오리가슴살 500g"
    )

    assert isinstance(result, DuckParseResult)
    assert result.duck_type == "훈제오리"
    assert result.breed == "체리밸리"
    assert result.cut == "오리가슴살"
    assert result.is_complete is True
    assert result.is_usable is True
    assert result.metadata["category_id"] == "duck"
    assert result.metadata["matched_field_count"] == 3
    assert result.confidence > 0.0


def test_parse_product_uses_structured_fields() -> None:
    result = DuckParser().parse_product(
        {
            "product_name": "국내산 오리고기",
            "duck_type": "어린 오리",
            "duck_breed": "페킨오리",
            "cut": "오리 안심",
            "option_name": "냉장 500g",
        }
    )

    assert result.duck_type is not None
    assert result.breed is not None
    assert result.cut is not None

    assert result.duck_type_match is not None
    assert result.breed_match is not None
    assert result.cut_match is not None

    assert (
        result.duck_type_match.entry.registry_key
        == "duckling"
    )
    assert (
        result.breed_match.entry.registry_key
        == "pekin"
    )
    assert (
        result.cut_match.entry.registry_key
        == "tenderloin"
    )

    assert result.metadata["source_type"] == "mapping"

    source_fields = result.metadata["source_fields"]

    assert "product_name" in source_fields
    assert "duck_type" in source_fields
    assert "duck_breed" in source_fields
    assert "cut" in source_fields


def test_parse_cut_only_is_usable_but_incomplete() -> None:
    result = DuckParser().parse(
        "국내산 오리가슴살 1kg"
    )

    assert result.duck_type is None
    assert result.breed is None
    assert result.cut == "오리가슴살"
    assert result.is_complete is False
    assert result.is_usable is True
    assert result.metadata["matched_field_count"] == 1


def test_parse_breed_only_is_not_usable() -> None:
    result = DuckParser().parse(
        "Cherry Valley duck"
    )

    assert result.breed == "체리밸리"
    assert result.duck_type is None
    assert result.cut is None
    assert result.is_complete is False
    assert result.is_usable is False


def test_parser_preserves_detected_aliases() -> None:
    result = DuckParser().parse(
        "훈제 오리 오리 똥집"
    )

    assert "훈제오리" in result.detected_keywords
    assert "오리똥집" in result.detected_keywords


def test_parser_matches_native_duck_and_leg() -> None:
    result = DuckParser().parse(
        "토종 오리 오리 장각"
    )

    assert result.duck_type_match is not None
    assert result.cut_match is not None

    assert (
        result.duck_type_match.entry.registry_key
        == "native_duck"
    )
    assert (
        result.cut_match.entry.registry_key
        == "leg"
    )


def test_parser_matches_muscovy_and_skin() -> None:
    result = DuckParser().parse(
        "머스코비 오리 껍질 구이용"
    )

    assert result.breed_match is not None
    assert result.cut_match is not None

    assert (
        result.breed_match.entry.registry_key
        == "muscovy"
    )
    assert (
        result.cut_match.entry.registry_key
        == "skin"
    )


def test_parser_does_not_match_other_meat_cut() -> None:
    result = DuckParser().parse(
        "한우 등심 스테이크"
    )

    assert result.duck_type is None
    assert result.breed is None
    assert result.cut is None
    assert result.is_usable is False


def test_parse_unknown_text_returns_unusable_result() -> None:
    result = DuckParser().parse(
        "상품 정보가 없는 테스트 문자열"
    )

    assert result.duck_type is None
    assert result.breed is None
    assert result.cut is None
    assert result.is_complete is False
    assert result.is_usable is False
    assert result.metadata["matched_field_count"] == 0


def test_parse_product_rejects_non_mapping() -> None:
    with pytest.raises(
        TypeError,
        match="product must be a Mapping",
    ):
        DuckParser().parse_product(  # type: ignore[arg-type]
            "오리가슴살"
        )


def test_parse_product_rejects_empty_mapping() -> None:
    with pytest.raises(
        ValueError,
        match="usable text field",
    ):
        DuckParser().parse_product({})


def test_parse_result_exposes_match_confidences() -> None:
    result = DuckParser().parse(
        "훈제오리 체리밸리 오리가슴살"
    )

    assert result.duck_type_confidence > 0.0
    assert result.breed_confidence > 0.0
    assert result.cut_confidence > 0.0
    assert result.confidence > 0.0


def test_parse_product_deduplicates_repeated_text() -> None:
    result = DuckParser().parse_product(
        {
            "product_name": "훈제오리",
            "title": "훈제오리",
            "duck_type": "훈제오리",
        }
    )

    assert result.original_text == "훈제오리"
    assert result.duck_type == "훈제오리"


def test_parser_dependency_injection() -> None:
    from app.services.food.knowledge.meat.duck import (
        DuckBreedRegistry,
        DuckCutRegistry,
        DuckTypeRegistry,
    )

    type_registry = DuckTypeRegistry()
    breed_registry = DuckBreedRegistry()
    cut_registry = DuckCutRegistry()

    parser = DuckParser(
        type_registry=type_registry,
        breed_registry=breed_registry,
        cut_registry=cut_registry,
    )

    assert parser.type_registry is type_registry
    assert parser.breed_registry is breed_registry
    assert parser.cut_registry is cut_registry
