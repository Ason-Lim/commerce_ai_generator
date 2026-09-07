"""Test-first parser and ownership contracts for Compound Seasonings."""

from importlib import import_module

import pytest


def _parse(text):
    module = import_module("app.services.food.knowledge.compound_seasoning.parser")
    return module.parse_compound_seasoning(text)


def test_parser_empty_input_preserves_unknown():
    result = _parse("")
    assert result.canonical_id is None
    assert result.composition_class is None
    assert result.confidence == 0.0


def test_parser_unknown_input_does_not_invent_identity():
    result = _parse("mystery pantry product")
    assert result.canonical_id is None
    assert result.unresolved


def test_parser_recognizes_curry_powder_as_dry_blend():
    result = _parse("curry powder seasoning blend")
    assert result.composition_class == "curry_blend"
    assert result.form == "powder"


def test_parser_recognizes_dry_rub_without_sauce_ownership():
    result = _parse("smoked barbecue dry rub")
    assert result.composition_class == "dry_rub"
    assert "smoked" in result.processing
    assert "sauce_boundary" not in result.conflicts


@pytest.mark.parametrize("text", ["basil", "rosemary", "black pepper"])
def test_parser_does_not_absorb_single_herb_or_spice(text):
    result = _parse(text)
    assert result.canonical_id is None
    assert result.composition_class is None


@pytest.mark.parametrize(
    "text",
    ["sea salt", "soy sauce", "doenjang", "gochujang", "rice vinegar"],
)
def test_parser_preserves_existing_domain_ownership(text):
    result = _parse(text)
    assert result.canonical_id is None
    assert result.composition_class is None


@pytest.mark.parametrize(
    "text",
    ["wet seasoning paste", "liquid marinade", "dipping sauce"],
)
def test_parser_defers_wet_and_sauce_boundary_cases(text):
    result = _parse(text)
    assert result.canonical_id is None
    assert "sauce_boundary" in result.conflicts or result.unresolved


def test_parser_does_not_infer_identity_from_coincident_food_terms():
    result = _parse("salt basil vinegar")
    assert result.canonical_id is None


def test_parser_is_deterministic_for_repeated_input():
    assert _parse("garlic herb seasoning mix") == _parse(
        "garlic herb seasoning mix"
    )


def test_parser_rejects_non_string_input():
    with pytest.raises(TypeError):
        _parse(None)
