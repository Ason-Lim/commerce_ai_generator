from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from app.services.food.knowledge.common.parser_models import (
    BaseParseResult,
)
from app.services.food.knowledge.tea.parser_models import (
    TeaParseResult,
)
from app.services.food.knowledge.tea.type_registry import (
    TeaTypeRegistry,
)


def test_empty_tea_parse_result() -> None:
    result = TeaParseResult(
        original_text="일반 상품",
        normalized_text="일반 상품",
    )

    assert isinstance(result, BaseParseResult)

    assert result.tea_type is None
    assert result.origin is None
    assert result.variety is None
    assert result.processing is None
    assert result.oxidation is None
    assert result.flavor is None

    assert result.matched_field_count == 0
    assert result.has_match is False
    assert result.is_complete is False
    assert result.is_usable is False


def test_tea_type_only_is_usable() -> None:
    result = TeaParseResult(
        original_text="우롱차",
        normalized_text="우롱차",
        confidence=1.0,
        tea_type="oolong",
        tea_type_confidence=1.0,
    )

    assert result.has_tea_type is True
    assert result.matched_field_count == 1
    assert result.is_complete is False
    assert result.is_usable is True


def test_origin_only_is_not_usable() -> None:
    result = TeaParseResult(
        original_text="다즐링",
        normalized_text="다즐링",
        confidence=1.0,
        origin="darjeeling",
        origin_confidence=1.0,
    )

    assert result.has_origin is True
    assert result.matched_field_count == 1
    assert result.is_usable is False


def test_two_supporting_fields_are_usable() -> None:
    result = TeaParseResult(
        original_text="다즐링 꽃향",
        normalized_text="다즐링 꽃향",
        confidence=1.0,
        origin="darjeeling",
        flavor="floral",
        origin_confidence=1.0,
        flavor_confidence=1.0,
    )

    assert result.matched_field_count == 2
    assert result.is_usable is True


def test_complete_tea_parse_result() -> None:
    result = TeaParseResult(
        original_text=(
            "다즐링 야부키타 증제 "
            "부분 산화 꽃향 우롱차"
        ),
        normalized_text=(
            "다즐링 야부키타 증제 "
            "부분 산화 꽃향 우롱차"
        ),
        confidence=1.0,
        tea_type="oolong",
        origin="darjeeling",
        variety="yabukita",
        processing="steamed",
        oxidation="medium",
        flavor="floral",
        tea_type_confidence=1.0,
        origin_confidence=1.0,
        variety_confidence=1.0,
        processing_confidence=1.0,
        oxidation_confidence=1.0,
        flavor_confidence=1.0,
    )

    assert result.matched_field_count == 6
    assert result.is_complete is True
    assert result.is_usable is True


def test_field_presence_properties() -> None:
    result = TeaParseResult(
        original_text="제주 야부키타 증제 녹차",
        normalized_text="제주 야부키타 증제 녹차",
        tea_type="green",
        origin="jeju",
        variety="yabukita",
        processing="steamed",
    )

    assert result.has_tea_type is True
    assert result.has_origin is True
    assert result.has_variety is True
    assert result.has_processing is True
    assert result.has_oxidation is False
    assert result.has_flavor is False


def test_parse_result_clamps_confidences() -> None:
    result = TeaParseResult(
        original_text="녹차",
        normalized_text="녹차",
        confidence=3.0,
        tea_type_confidence=2.0,
        origin_confidence=-1.0,
        variety_confidence=7.0,
        processing_confidence=-5.0,
        oxidation_confidence=1.5,
        flavor_confidence=-0.5,
    )

    assert result.confidence == 1.0
    assert result.tea_type_confidence == 1.0
    assert result.origin_confidence == 0.0
    assert result.variety_confidence == 1.0
    assert result.processing_confidence == 0.0
    assert result.oxidation_confidence == 1.0
    assert result.flavor_confidence == 0.0


def test_parse_result_deduplicates_evidence() -> None:
    result = TeaParseResult(
        original_text="꽃향 우롱차",
        normalized_text="꽃향 우롱차",
        detected_keywords=[
            "꽃향",
            "우롱차",
            "꽃향",
            "",
            " ",
        ],
        warnings=[
            "경고",
            "경고",
            "",
            " ",
        ],
    )

    assert result.detected_keywords == [
        "꽃향",
        "우롱차",
    ]
    assert result.warnings == [
        "경고",
    ]


def test_parse_result_preserves_registry_match() -> None:
    match = TeaTypeRegistry().match(
        "우롱차"
    )

    assert match is not None

    result = TeaParseResult(
        original_text="우롱차",
        normalized_text="우롱차",
        confidence=match.confidence,
        tea_type=match.entry.registry_key,
        tea_type_confidence=match.confidence,
        tea_type_match=match,
        detected_keywords=[
            match.matched_alias,
        ],
    )

    assert result.tea_type_match is match
    assert result.tea_type == "oolong"
    assert result.has_match is True


def test_tea_parse_result_serializes() -> None:
    match = TeaTypeRegistry().match(
        "녹차"
    )

    assert match is not None

    result = TeaParseResult(
        original_text="제주 녹차",
        normalized_text="제주 녹차",
        confidence=0.9,
        tea_type="green",
        origin="jeju",
        tea_type_confidence=0.9,
        origin_confidence=0.8,
        tea_type_match=match,
        detected_keywords=[
            "제주",
            "녹차",
        ],
        warnings=[
            "example warning",
        ],
    )

    payload = result.to_dict()

    assert payload["tea_type"] == "green"
    assert payload["origin"] == "jeju"
    assert payload["matched_field_count"] == 2
    assert payload["is_complete"] is False
    assert payload["is_usable"] is True
    assert payload["has_match"] is True
    assert payload["detected_keywords"] == [
        "제주",
        "녹차",
    ]
    assert payload["warnings"] == [
        "example warning",
    ]
    assert payload["tea_type_match"] is not None


def test_tea_parse_result_is_frozen() -> None:
    result = TeaParseResult(
        original_text="녹차",
        normalized_text="녹차",
        confidence=0.8,
        tea_type="green",
    )

    with pytest.raises(FrozenInstanceError):
        result.tea_type = "black"  # type: ignore[misc]


def test_metadata_is_copied_by_base_contract() -> None:
    metadata = {
        "source": {
            "name": "test",
        }
    }

    result = TeaParseResult(
        original_text="녹차",
        normalized_text="녹차",
        metadata=metadata,
    )

    metadata["source"]["name"] = "changed"

    assert result.metadata == {
        "source": {
            "name": "test",
        }
    }
