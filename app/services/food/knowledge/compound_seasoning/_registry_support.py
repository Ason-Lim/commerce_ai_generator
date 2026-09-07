"""Shared immutable loader contracts for Compound Seasoning registries."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any

import yaml


class RegistryValidationError(ValueError):
    """Raised when a registry resource violates its fail-closed contract."""


@dataclass(frozen=True, slots=True)
class RegistryEntry:
    """One immutable, normalized, and provenance-backed registry entry."""

    canonical_id: str
    label: str
    aliases: tuple[str, ...]
    provenance: tuple[str, ...]


_EXPECTED_FIELDS = frozenset({"canonical_id", "label", "aliases", "provenance"})
_SEPARATOR_PATTERN = re.compile(r"[^a-z0-9]+")


def normalize_key(value: str) -> str:
    """Return a deterministic lookup key without guessing domain ownership."""

    if not isinstance(value, str):
        raise TypeError("registry key must be a string")
    return _SEPARATOR_PATTERN.sub("_", value.strip().casefold()).strip("_")


def _nonempty_string(value: Any, *, field: str, registry_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RegistryValidationError(
            f"{registry_name}: {field} must be a non-empty string"
        )
    return value.strip()


def _string_sequence(value: Any, *, field: str, registry_name: str) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise RegistryValidationError(f"{registry_name}: {field} must be a list")
    return tuple(
        _nonempty_string(item, field=field, registry_name=registry_name)
        for item in value
    )


def load_entries(
    raw_entries: Any, *, registry_name: str
) -> tuple[RegistryEntry, ...]:
    """Validate raw entries and return one stable immutable tuple."""

    if (
        isinstance(raw_entries, (str, bytes))
        or not isinstance(raw_entries, Sequence)
        or not raw_entries
    ):
        raise RegistryValidationError(f"{registry_name}: entries must be a non-empty list")

    entries: list[RegistryEntry] = []
    canonical_ids: set[str] = set()
    lookup_keys: set[str] = set()

    for position, raw_entry in enumerate(raw_entries):
        if not isinstance(raw_entry, Mapping):
            raise RegistryValidationError(
                f"{registry_name}: entry {position} must be a mapping"
            )
        fields = frozenset(raw_entry)
        if fields != _EXPECTED_FIELDS:
            raise RegistryValidationError(
                f"{registry_name}: entry {position} fields must be exactly "
                f"{sorted(_EXPECTED_FIELDS)}"
            )

        canonical_id = normalize_key(
            _nonempty_string(
                raw_entry["canonical_id"],
                field="canonical_id",
                registry_name=registry_name,
            )
        )
        if not canonical_id or canonical_id in canonical_ids:
            raise RegistryValidationError(
                f"{registry_name}: duplicate or empty canonical_id {canonical_id!r}"
            )
        if canonical_id in lookup_keys:
            raise RegistryValidationError(
                f"{registry_name}: canonical_id collides with an alias: {canonical_id}"
            )

        label = _nonempty_string(
            raw_entry["label"], field="label", registry_name=registry_name
        )
        raw_aliases = _string_sequence(
            raw_entry["aliases"], field="aliases", registry_name=registry_name
        )
        aliases = tuple(normalize_key(alias) for alias in raw_aliases)
        if any(not alias for alias in aliases):
            raise RegistryValidationError(f"{registry_name}: aliases must not normalize empty")
        if len(aliases) != len(set(aliases)):
            raise RegistryValidationError(f"{registry_name}: duplicate alias in one entry")
        if canonical_id in aliases:
            raise RegistryValidationError(
                f"{registry_name}: canonical_id must not be repeated as an alias"
            )
        duplicate_aliases = set(aliases).intersection(lookup_keys | canonical_ids)
        if duplicate_aliases:
            raise RegistryValidationError(
                f"{registry_name}: duplicate lookup key {sorted(duplicate_aliases)[0]}"
            )

        provenance = _string_sequence(
            raw_entry["provenance"], field="provenance", registry_name=registry_name
        )
        if not provenance:
            raise RegistryValidationError(
                f"{registry_name}: provenance must be a non-empty list"
            )

        canonical_ids.add(canonical_id)
        lookup_keys.update(aliases)
        entries.append(
            RegistryEntry(
                canonical_id=canonical_id,
                label=label,
                aliases=aliases,
                provenance=provenance,
            )
        )

    return tuple(entries)


def load_resource(resource_path: Path, *, registry_name: str) -> tuple[RegistryEntry, ...]:
    """Load one YAML resource through the same strict entry contract."""

    try:
        with resource_path.open("r", encoding="utf-8") as stream:
            raw_entries = yaml.safe_load(stream)
    except (OSError, yaml.YAMLError) as exc:
        raise RegistryValidationError(
            f"{registry_name}: unable to load registry resource"
        ) from exc
    return load_entries(raw_entries, registry_name=registry_name)


def build_lookup(entries: tuple[RegistryEntry, ...]) -> dict[str, RegistryEntry]:
    """Build the already-validated canonical and alias lookup table."""

    return {
        key: entry
        for entry in entries
        for key in (entry.canonical_id, *entry.aliases)
    }
