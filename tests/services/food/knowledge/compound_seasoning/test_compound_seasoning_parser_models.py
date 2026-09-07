"""Contract tests for the Compound Seasoning normalized parser model."""

from importlib import import_module

import pytest


def _result_type():
    module = import_module(
        "app.services.food.knowledge.compound_seasoning.parser_models"
    )
    return module.CompoundSeasoningParseResult


def test_parser_model_contract_is_exported():
    assert _result_type().__name__ == "CompoundSeasoningParseResult"


def test_parser_model_defaults_preserve_unknown_and_empty_values():
    result = _result_type()()
    assert result.canonical_id is None
    assert result.composition_class is None
    assert result.form is None
    assert result.usages == ()
    assert result.origins == ()
    assert result.processing == ()
    assert result.ingredient_roles == ()
    assert result.unresolved == ()
    assert result.conflicts == ()
    assert result.matched_evidence == ()
    assert result.confidence == 0.0
    assert result.completeness == 0.0


def test_parser_model_retains_explicit_supported_values():
    result = _result_type()(
        canonical_id="curry_powder",
        composition_class="curry_blend",
        form="powder",
        usages=("general_seasoning",),
        origins=("south_asian_context",),
        processing=("ground", "blended"),
        ingredient_roles=("spice", "salt"),
        matched_evidence=("composition:curry_blend",),
        confidence=0.75,
        completeness=0.5,
    )
    assert result.canonical_id == "curry_powder"
    assert result.composition_class == "curry_blend"
    assert result.form == "powder"
    assert result.processing == ("ground", "blended")
    assert result.confidence == 0.75
    assert result.completeness == 0.5


def test_parser_model_collections_are_tuple_contracts():
    result = _result_type()(
        usages=("rub",),
        origins=("korean_context",),
        processing=("smoked",),
        ingredient_roles=("spice",),
        unresolved=("brand_term",),
        conflicts=("wet_boundary",),
        matched_evidence=("form:powder",),
    )
    for value in (
        result.usages,
        result.origins,
        result.processing,
        result.ingredient_roles,
        result.unresolved,
        result.conflicts,
        result.matched_evidence,
    ):
        assert isinstance(value, tuple)


def test_parser_model_keeps_unresolved_and_conflicts_explicit():
    result = _result_type()(
        unresolved=("unknown_mix",),
        conflicts=("sauce_boundary",),
    )
    assert result.canonical_id is None
    assert result.unresolved == ("unknown_mix",)
    assert result.conflicts == ("sauce_boundary",)


def test_parser_model_equality_is_deterministic():
    result_type = _result_type()
    left = result_type(composition_class="dry_rub", form="powder")
    right = result_type(composition_class="dry_rub", form="powder")
    assert left == right


@pytest.mark.parametrize("field", ["confidence", "completeness"])
def test_parser_model_rejects_values_below_zero(field):
    with pytest.raises(ValueError):
        _result_type()(**{field: -0.01})


def test_parser_model_rejects_confidence_above_one():
    with pytest.raises(ValueError):
        _result_type()(confidence=1.01)
