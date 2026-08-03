from __future__ import annotations

import pytest

from app.services.food.knowledge.meat.goat import (
    GoatBreedRegistry,
    GoatCutRegistry,
    GoatParser,
    GoatTypeRegistry,
)
from app.services.food.knowledge.meat.goat.parser_models import (
    GoatParseResult,
)


def test_parse_complete_goat_product() -> None:
    result = GoatParser().parse(
        "어린염소 보어 염소안심 500g"
    )

    assert isinstance(
        result,
        GoatParseResult,
    )
    assert result.goat_type == "어린염소"
    assert result.breed == "보어"
    assert result.cut == "염소안심"
    assert result.is_complete is True
    assert result.is_usable is True

    assert (
        result.metadata["category_id"]
        == "goat"
    )
    assert (
        result.metadata[
            "matched_field_count"
        ]
        == 3
    )
    assert result.confidence > 0.0


def test_parse_product_uses_structured_fields() -> None:
    result = GoatParser().parse_product(
        {
            "product_name": (
                "프리미엄 염소고기"
            ),
            "goat_type": "어린 염소",
            "goat_breed": "Boer",
            "cut": "goat tenderloin",
            "option_name": "냉장 500g",
        }
    )

    assert result.goat_type is not None
    assert result.breed is not None
    assert result.cut is not None

    assert (
        result
        .goat_type_match
        .entry
        .registry_key
        == "kid"
    )
    assert (
        result
        .breed_match
        .entry
        .registry_key
        == "boer"
    )
    assert (
        result
        .cut_match
        .entry
        .registry_key
        == "tenderloin"
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


def test_parse_black_goat_product() -> None:
    result = GoatParser().parse(
        "국내산 토종흑염소 "
        "염소다리살 1kg"
    )

    assert result.goat_type == "흑염소"
    assert result.breed == "한국흑염소"
    assert result.cut == "염소다리"

    assert (
        result
        .goat_type_match
        .entry
        .registry_key
        == "black_goat"
    )
    assert (
        result
        .breed_match
        .entry
        .registry_key
        == "korean_black_goat"
    )
    assert (
        result
        .cut_match
        .entry
        .registry_key
        == "leg"
    )


def test_parse_cut_only_is_usable() -> None:
    result = GoatParser().parse(
        "수입산 염소안심 1kg"
    )

    assert result.goat_type is None
    assert result.breed is None
    assert result.cut == "염소안심"
    assert result.is_complete is False
    assert result.is_usable is True

    assert (
        result.metadata[
            "matched_field_count"
        ]
        == 1
    )


def test_parse_breed_only_is_not_usable() -> None:
    result = GoatParser().parse(
        "Boer premium"
    )

    assert result.breed == "보어"
    assert result.goat_type is None
    assert result.cut is None
    assert result.is_complete is False
    assert result.is_usable is False


def test_parser_preserves_detected_aliases() -> None:
    result = GoatParser().parse(
        "어린 염소 보어 염소 안심"
    )

    assert len(
        result.detected_keywords
    ) == 3

    assert any(
        "어린" in keyword
        for keyword in result.detected_keywords
    )
    assert any(
        "보어" in keyword
        for keyword in result.detected_keywords
    )
    assert any(
        "안심" in keyword
        for keyword in result.detected_keywords
    )


def test_parser_matches_kiko_and_rack() -> None:
    result = GoatParser().parse(
        "뉴질랜드 키코 염소 "
        "고트 랙 로스트"
    )

    assert result.breed_match is not None
    assert result.cut_match is not None

    assert (
        result
        .breed_match
        .entry
        .registry_key
        == "kiko"
    )
    assert (
        result
        .cut_match
        .entry
        .registry_key
        == "rack"
    )


def test_parser_matches_goat_trim() -> None:
    result = GoatParser().parse(
        "수입산 염소고기 정육 1kg"
    )

    assert result.cut_match is not None
    assert (
        result
        .cut_match
        .entry
        .registry_key
        == "trim"
    )
    assert result.cut == "염소정육"
    assert result.is_usable is True


def test_parser_does_not_match_other_meat() -> None:
    result = GoatParser().parse(
        "한우 1++ 등심 스테이크"
    )

    assert result.goat_type is None
    assert result.breed is None
    assert result.cut is None
    assert result.is_usable is False


@pytest.mark.parametrize(
    "text",
    [
        "닭가슴살 1kg",
        "오리 백숙용 한 마리",
        "사슴안심 스테이크",
        "양고기 프렌치랙",
        "돼지고기 목살",
    ],
)
def test_parser_non_goat_boundary(
    text: str,
) -> None:
    result = GoatParser().parse(text)

    assert result.goat_type is None
    assert result.breed is None
    assert result.cut is None
    assert result.is_usable is False


def test_unknown_text_returns_unusable() -> None:
    result = GoatParser().parse(
        "상품 정보가 없는 테스트 문자열"
    )

    assert result.goat_type is None
    assert result.breed is None
    assert result.cut is None
    assert result.is_complete is False
    assert result.is_usable is False

    assert (
        result.metadata[
            "matched_field_count"
        ]
        == 0
    )


def test_parse_product_rejects_non_mapping() -> None:
    with pytest.raises(
        TypeError,
        match="product must be a Mapping",
    ):
        GoatParser().parse_product(
            "염소안심"  # type: ignore[arg-type]
        )


def test_parse_product_rejects_empty_mapping() -> None:
    with pytest.raises(
        ValueError,
        match="usable text field",
    ):
        GoatParser().parse_product({})


def test_parse_result_confidences() -> None:
    result = GoatParser().parse(
        "어린염소 보어 염소안심"
    )

    assert (
        result.goat_type_confidence
        > 0.0
    )
    assert result.breed_confidence > 0.0
    assert result.cut_confidence > 0.0
    assert result.confidence > 0.0


def test_parse_product_deduplicates_text() -> None:
    result = GoatParser().parse_product(
        {
            "product_name": "흑염소",
            "title": "흑염소",
            "goat_type": "흑염소",
        }
    )

    assert result.original_text == "흑염소"
    assert result.goat_type == "흑염소"


def test_parser_dependency_injection() -> None:
    type_registry = GoatTypeRegistry()
    breed_registry = GoatBreedRegistry()
    cut_registry = GoatCutRegistry()

    parser = GoatParser(
        type_registry=type_registry,
        breed_registry=breed_registry,
        cut_registry=cut_registry,
    )

    assert (
        parser.type_registry
        is type_registry
    )
    assert (
        parser.breed_registry
        is breed_registry
    )
    assert (
        parser.cut_registry
        is cut_registry
    )


def test_structured_cut_overrides_generic_name() -> None:
    result = GoatParser().parse_product(
        {
            "product_name": "수입 염소고기",
            "cut": "goat tenderloin",
        }
    )

    assert result.cut_match is not None
    assert (
        result
        .cut_match
        .entry
        .registry_key
        == "tenderloin"
    )
    assert result.cut == "염소안심"

    assert (
        "cut"
        in result.metadata[
            "explicit_match_fields"
        ]
    )


def test_structured_type_overrides_name_context() -> None:
    result = GoatParser().parse_product(
        {
            "product_name": (
                "일반 염소고기 정육"
            ),
            "goat_type": "어린 염소",
        }
    )

    assert result.goat_type_match is not None
    assert (
        result
        .goat_type_match
        .entry
        .registry_key
        == "kid"
    )
