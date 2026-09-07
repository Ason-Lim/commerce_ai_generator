"""Provenance-backed Compound Seasoning composition registry."""

from pathlib import Path

from ._registry_support import RegistryEntry, build_lookup, load_resource, normalize_key


RESOURCE_PATH = (
    Path(__file__).resolve().parents[2]
    / "registry_data"
    / "compound_seasoning"
    / "compositions.yaml"
)
_ENTRIES = load_resource(RESOURCE_PATH, registry_name="compound_seasoning.composition")
_LOOKUP = build_lookup(_ENTRIES)


def entries() -> tuple[RegistryEntry, ...]:
    return _ENTRIES


def resolve(value: str) -> RegistryEntry | None:
    return _LOOKUP.get(normalize_key(value))
