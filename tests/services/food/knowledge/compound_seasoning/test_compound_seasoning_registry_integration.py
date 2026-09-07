"""Test-first contracts for Compound Seasoning F3 registries and resources."""

from importlib import import_module, util
from pathlib import Path

import pytest


PACKAGE = "app.services.food.knowledge.compound_seasoning"
REGISTRY_NAMES = ("form", "composition", "usage")
RESOURCE_NAMES = {
    "form": "forms.yaml",
    "composition": "compositions.yaml",
    "usage": "usages.yaml",
}
NEGATIVE_OWNERSHIP_TERMS = (
    "basil",
    "black pepper",
    "sea salt",
    "soy sauce",
    "doenjang",
    "gochujang",
    "rice vinegar",
    "wet seasoning paste",
    "liquid marinade",
    "finished dipping sauce",
)


def _support():
    return import_module(f"{PACKAGE}._registry_support")


def _registry(name):
    return import_module(f"{PACKAGE}.{name}_registry")


def _entries(name):
    return _registry(name).entries()


def test_support_contract_is_exported():
    support = _support()
    assert support.RegistryEntry
    assert support.RegistryValidationError
    assert callable(support.normalize_key)
    assert callable(support.load_entries)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (" Curry Powder ", "curry_powder"),
        ("SOUP-BASE", "soup_base"),
        ("garlic   herb", "garlic_herb"),
    ],
)
def test_normalize_key_is_deterministic(raw, expected):
    assert _support().normalize_key(raw) == expected


def test_normalize_key_rejects_non_string_input():
    with pytest.raises(TypeError):
        _support().normalize_key(None)


@pytest.mark.parametrize(
    "raw_entries",
    [
        [],
        [{"canonical_id": "x", "label": "X", "aliases": [], "provenance": []}],
        [
            {"canonical_id": "x", "label": "X", "aliases": [], "provenance": ["p"]},
            {"canonical_id": "x", "label": "Y", "aliases": [], "provenance": ["p"]},
        ],
        [
            {"canonical_id": "x", "label": "X", "aliases": ["shared"], "provenance": ["p"]},
            {"canonical_id": "y", "label": "Y", "aliases": ["Shared"], "provenance": ["p"]},
        ],
        [
            {
                "canonical_id": "x",
                "label": "X",
                "aliases": [],
                "provenance": ["p"],
                "unexpected": True,
            }
        ],
    ],
)
def test_loader_rejects_empty_malformed_or_duplicate_entries(raw_entries):
    support = _support()
    with pytest.raises(support.RegistryValidationError):
        support.load_entries(raw_entries, registry_name="contract")


@pytest.mark.parametrize("name", REGISTRY_NAMES)
def test_registry_module_exports_read_only_contract(name):
    module = _registry(name)
    assert isinstance(module.RESOURCE_PATH, Path)
    assert callable(module.entries)
    assert callable(module.resolve)


@pytest.mark.parametrize("name", REGISTRY_NAMES)
def test_registry_uses_exact_selected_resource_name(name):
    assert _registry(name).RESOURCE_PATH.name == RESOURCE_NAMES[name]


@pytest.mark.parametrize("name", REGISTRY_NAMES)
def test_registry_is_nonempty(name):
    assert _entries(name)


@pytest.mark.parametrize("name", REGISTRY_NAMES)
def test_registry_entries_are_immutable_and_provenanced(name):
    entries = _entries(name)
    assert isinstance(entries, tuple)
    for entry in entries:
        assert entry.canonical_id
        assert entry.label
        assert isinstance(entry.aliases, tuple)
        assert isinstance(entry.provenance, tuple)
        assert entry.provenance


@pytest.mark.parametrize("name", REGISTRY_NAMES)
def test_registry_canonical_ids_are_unique(name):
    canonical_ids = [entry.canonical_id for entry in _entries(name)]
    assert len(canonical_ids) == len(set(canonical_ids))


@pytest.mark.parametrize("name", REGISTRY_NAMES)
def test_registry_aliases_are_normalized_and_unique(name):
    support = _support()
    aliases = [alias for entry in _entries(name) for alias in entry.aliases]
    normalized = [support.normalize_key(alias) for alias in aliases]
    assert all(alias == normalized_alias for alias, normalized_alias in zip(aliases, normalized))
    assert len(normalized) == len(set(normalized))


@pytest.mark.parametrize("name", REGISTRY_NAMES)
def test_registry_resolves_each_canonical_id(name):
    module = _registry(name)
    for entry in module.entries():
        assert module.resolve(entry.canonical_id) == entry


@pytest.mark.parametrize("name", REGISTRY_NAMES)
def test_registry_resolves_each_alias(name):
    module = _registry(name)
    for entry in module.entries():
        for alias in entry.aliases:
            assert module.resolve(alias) == entry


@pytest.mark.parametrize("name", REGISTRY_NAMES)
def test_registry_preserves_unknown_as_none(name):
    assert _registry(name).resolve("unmapped-contract-value") is None


@pytest.mark.parametrize("name", REGISTRY_NAMES)
def test_registry_repeated_load_and_lookup_are_deterministic(name):
    module = _registry(name)
    first = module.entries()
    second = module.entries()
    assert first == second
    assert first is second
    assert module.resolve(first[0].canonical_id) == module.resolve(
        first[0].canonical_id
    )


def test_selected_registries_do_not_absorb_neighbor_domain_terms():
    for name in REGISTRY_NAMES:
        module = _registry(name)
        for term in NEGATIVE_OWNERSHIP_TERMS:
            assert module.resolve(term) is None


@pytest.mark.parametrize("module_name", ["origin_registry", "processing_registry"])
def test_deferred_optional_registry_modules_remain_absent(module_name):
    _support()
    assert util.find_spec(f"{PACKAGE}.{module_name}") is None
