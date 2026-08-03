from __future__ import annotations

from app.services.food.knowledge.meat.goat.parser_models import (
    GoatParseResult,
)


def test_empty_goat_parse_result() -> None:
    result = GoatParseResult(
        original_text="일반 상품",
        normalized_text="일반 상품",
    )

    assert result.goat_type is None
    assert result.breed is None
    assert result.cut is None
    assert result.is_complete is False
    assert result.is_usable is False


def test_goat_type_only_is_usable() -> None:
    result = GoatParseResult(
        original_text="흑염소",
        normalized_text="흑염소",
        goat_type="흑염소",
        goat_type_confidence=1.0,
    )

    assert result.has_goat_type is True
    assert result.is_complete is False
    assert result.is_usable is True


def test_goat_cut_only_is_usable() -> None:
    result = GoatParseResult(
        original_text="염소안심",
        normalized_text="염소안심",
        cut="염소안심",
        cut_confidence=1.0,
    )

    assert result.has_cut is True
    assert result.is_complete is False
    assert result.is_usable is True


def test_breed_only_is_not_usable() -> None:
    result = GoatParseResult(
        original_text="Boer",
        normalized_text="boer",
        breed="보어",
        breed_confidence=1.0,
    )

    assert result.has_breed is True
    assert result.is_complete is False
    assert result.is_usable is False


def test_complete_goat_parse_result() -> None:
    result = GoatParseResult(
        original_text="어린염소 보어 염소안심",
        normalized_text="어린염소 보어 염소안심",
        confidence=1.0,
        goat_type="어린염소",
        breed="보어",
        cut="염소안심",
        goat_type_confidence=1.0,
        breed_confidence=1.0,
        cut_confidence=1.0,
    )

    assert result.is_complete is True
    assert result.is_usable is True
