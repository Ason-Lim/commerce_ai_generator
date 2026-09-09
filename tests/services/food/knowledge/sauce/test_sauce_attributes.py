from dataclasses import FrozenInstanceError
from importlib import import_module

import pytest


MODULE = "app.services.food.knowledge.sauce.attributes"


def _module():
    return import_module(MODULE)


@pytest.mark.parametrize(
    "value",
    (
        "fermented-liquid", "fermented-paste", "emulsified",
        "tomato/produce", "chili/hot", "savory/reduction",
        "dressing/marinade", "sweet/dessert", "other",
    ),
)
def test_sauce_family_vocabulary_contains_each_canonical_value(value: str) -> None:
    assert value in tuple(item.value for item in _module().SauceFamily)


@pytest.mark.parametrize(
    "value", ("liquid", "viscous", "creamy", "paste-like", "chunky", "unknown")
)
def test_sauce_texture_vocabulary_contains_each_canonical_value(value: str) -> None:
    assert value in tuple(item.value for item in _module().SauceTexture)


@pytest.mark.parametrize(
    "value", ("none", "mild", "medium", "hot", "very-hot", "unknown")
)
def test_sauce_heat_vocabulary_contains_each_canonical_value(value: str) -> None:
    assert value in tuple(item.value for item in _module().SauceHeatLevel)


@pytest.mark.parametrize(
    "value",
    (
        "dipping", "dressing", "cooking", "glazing", "marinating",
        "spreading", "finishing", "multipurpose", "unknown",
    ),
)
def test_sauce_use_vocabulary_contains_each_canonical_value(value: str) -> None:
    assert value in tuple(item.value for item in _module().SauceUse)


@pytest.mark.parametrize(
    "value", ("explicit-text", "normalized-alias", "derived-rule", "unresolved")
)
def test_evidence_provenance_contains_each_canonical_value(value: str) -> None:
    assert value in tuple(item.value for item in _module().EvidenceProvenance)


def test_attributes_defaults_preserve_unknown_and_unresolved_state() -> None:
    module = _module()
    attributes = module.SauceAttributes()
    assert attributes.family is module.SauceFamily.OTHER
    assert attributes.texture is module.SauceTexture.UNKNOWN
    assert attributes.heat_level is module.SauceHeatLevel.UNKNOWN
    assert attributes.intended_uses == ()
    assert attributes.provenance is module.EvidenceProvenance.UNRESOLVED
    assert attributes.matched_evidence == ()
    assert attributes.conflicting_evidence == ()


def test_attributes_retain_explicit_supported_values() -> None:
    module = _module()
    attributes = module.SauceAttributes(
        family=module.SauceFamily.FERMENTED_LIQUID,
        texture=module.SauceTexture.LIQUID,
        heat_level=module.SauceHeatLevel.MILD,
        intended_uses=(module.SauceUse.DIPPING, module.SauceUse.COOKING),
        provenance=module.EvidenceProvenance.EXPLICIT_TEXT,
        matched_evidence=("ponzu shoyu",),
    )
    assert attributes.family.value == "fermented-liquid"
    assert attributes.texture.value == "liquid"
    assert attributes.heat_level.value == "mild"
    assert tuple(item.value for item in attributes.intended_uses) == ("dipping", "cooking")
    assert attributes.matched_evidence == ("ponzu shoyu",)


def test_attributes_collection_fields_are_immutable_tuples() -> None:
    module = _module()
    attributes = module.SauceAttributes(
        intended_uses=[module.SauceUse.FINISHING],
        matched_evidence=["yuzu-kosho sauce"],
        conflicting_evidence=["paste identity"],
    )
    assert attributes.intended_uses == (module.SauceUse.FINISHING,)
    assert attributes.matched_evidence == ("yuzu-kosho sauce",)
    assert attributes.conflicting_evidence == ("paste identity",)


def test_unresolved_evidence_remains_explicit() -> None:
    module = _module()
    attributes = module.SauceAttributes(
        provenance=module.EvidenceProvenance.UNRESOLVED,
        matched_evidence=("generic condiment",),
    )
    assert attributes.provenance is module.EvidenceProvenance.UNRESOLVED
    assert attributes.matched_evidence == ("generic condiment",)


def test_conflicting_evidence_remains_explicit() -> None:
    module = _module()
    attributes = module.SauceAttributes(
        conflicting_evidence=("sauce identity", "ingredient identity")
    )
    assert attributes.conflicting_evidence == (
        "sauce identity", "ingredient identity"
    )


def test_equivalent_attributes_have_deterministic_value_equality() -> None:
    module = _module()
    left = module.SauceAttributes(
        family=module.SauceFamily.EMULSIFIED,
        matched_evidence=("mayonnaise",),
    )
    right = module.SauceAttributes(
        family=module.SauceFamily.EMULSIFIED,
        matched_evidence=("mayonnaise",),
    )
    assert left == right


def test_attributes_are_frozen() -> None:
    module = _module()
    attributes = module.SauceAttributes()
    with pytest.raises(FrozenInstanceError):
        attributes.family = module.SauceFamily.EMULSIFIED
