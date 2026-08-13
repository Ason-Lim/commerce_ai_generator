from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from app.services.food.knowledge.seafood.parser_models import (
    SeafoodParseResult,
)


def test_seafood_parse_result_is_frozen():
    parsed = SeafoodParseResult(
        original_text="냉동 새우 500g",
        normalized_text="냉동 새우 500g",
        confidence=0.8,
        seafood_group="crustacean",
        species="shrimp",
    )

    with pytest.raises(FrozenInstanceError):
        parsed.species = "crab"


def test_seafood_parse_result_reports_match_state():
    parsed = SeafoodParseResult(
        original_text="생연어",
        normalized_text="생연어",
        confidence=0.8,
        seafood_group="fish",
        species="salmon",
    )

    assert parsed.has_match is True
    assert parsed.is_complete is True
    assert parsed.is_usable is True
    assert parsed.matched_field_count == 2


def test_seafood_parse_result_serializes():
    parsed = SeafoodParseResult(
        original_text="냉동 새우 800g",
        normalized_text="냉동 새우 800g",
        confidence=0.8,
        seafood_group="crustacean",
        species="shrimp",
        processing_state="frozen",
        weight_grams=800.0,
    )

    payload = parsed.to_dict()

    assert payload["species"] == "shrimp"
    assert payload["seafood_group"] == "crustacean"
    assert payload["processing_state"] == "frozen"
    assert payload["weight_grams"] == 800.0
