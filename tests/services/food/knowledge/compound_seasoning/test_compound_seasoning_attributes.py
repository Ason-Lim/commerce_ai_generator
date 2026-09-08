"""Test-first contracts for normalized Compound Seasoning attributes."""

from dataclasses import FrozenInstanceError
from importlib import import_module

import pytest


MODULE = "app.services.food.knowledge.compound_seasoning.attributes"


def _module():
    return import_module(MODULE)


def test_attribute_contract_exports_are_explicit():
    module = _module()
    assert module.EvidenceStatus
    assert module.AttributeEvidence
    assert module.CompoundSeasoningAttributes
    assert module.AttributeValidationError
    assert callable(module.normalize_evidence)
    assert callable(module.project_attributes)


def test_evidence_status_vocabulary_is_exact():
    status = _module().EvidenceStatus
    assert tuple(item.value for item in status) == (
        "VERIFIED",
        "PARTIALLY_VERIFIED",
        "REPORTED",
        "MISSING",
        "CONFLICTING",
    )


def test_verified_value_is_normalized_and_resolved():
    evidence = _module().normalize_evidence("  Curry   Powder  ", "VERIFIED")
    assert evidence.value == "curry powder"
    assert evidence.status.value == "VERIFIED"
    assert evidence.unresolved is False


@pytest.mark.parametrize(
    "status",
    ["PARTIALLY_VERIFIED", "REPORTED", "MISSING", "CONFLICTING"],
)
def test_non_verified_status_remains_explicitly_unresolved(status):
    evidence = _module().normalize_evidence("powder", status)
    assert evidence.status.value == status
    assert evidence.unresolved is True


def test_missing_value_is_never_invented():
    evidence = _module().normalize_evidence(None, "MISSING")
    assert evidence.value is None
    assert evidence.unresolved is True


def test_empty_verified_value_fails_closed():
    with pytest.raises(_module().AttributeValidationError):
        _module().normalize_evidence("  ", "VERIFIED")


def test_invalid_evidence_status_fails_closed():
    with pytest.raises(_module().AttributeValidationError):
        _module().normalize_evidence("powder", "ASSUMED")


def test_attribute_evidence_is_immutable():
    evidence = _module().normalize_evidence("powder", "VERIFIED")
    with pytest.raises(FrozenInstanceError):
        evidence.value = "paste"


def test_projection_exposes_exact_form_composition_usage_fields():
    attributes = _module().project_attributes(
        form=("powder", "VERIFIED"),
        composition=("multi_ingredient_blend", "VERIFIED"),
        usage=("general_seasoning", "VERIFIED"),
    )
    assert attributes.form.value == "powder"
    assert attributes.composition.value == "multi_ingredient_blend"
    assert attributes.usage.value == "general_seasoning"


def test_equivalent_normalized_projection_is_deterministic():
    module = _module()
    left = module.project_attributes(
        form=(" Powder ", "VERIFIED"),
        composition=("Multi Ingredient Blend", "VERIFIED"),
        usage=("General Seasoning", "VERIFIED"),
    )
    right = module.project_attributes(
        usage=("general seasoning", "VERIFIED"),
        form=("powder", "VERIFIED"),
        composition=("multi ingredient blend", "VERIFIED"),
    )
    assert left == right
