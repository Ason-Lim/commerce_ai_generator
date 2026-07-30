from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any, Mapping

from app.services.food.knowledge.common.base_model import RegistryEntry, RegistryMatch
from app.services.food.knowledge.common.base_registry import AliasMatch, BaseAliasRegistry, normalize_string_list, optional_string, safe_float
from app.services.food.knowledge.registry_loader import KnowledgeRegistryLoader, get_knowledge_registry_loader

VENISON_BREED_REGISTRY_ID = "venison.breeds"


def _aliases(canonical_name: str, raw_aliases: Any) -> tuple[str, ...]:
    values = [canonical_name, *normalize_string_list(raw_aliases)]
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = str(value).strip()
        key = text.casefold()
        if text and key not in seen:
            seen.add(key)
            result.append(text)
    return tuple(result)


def _optional_score(value: Any) -> float | None:
    if value is None:
        return None
    return max(0.0, min(100.0, safe_float(value, default=0.0)))


@dataclass(frozen=True, kw_only=True)
class VenisonBreed(RegistryEntry):
    canonical_name: str
    aliases: tuple[str, ...]
    score: float
    premium: bool
    english_name: str | None
    origin_country: str | None
    breed_type: str | None
    flavor_score: float | None
    tenderness_score: float | None
    growth_score: float | None
    rarity_score: float | None
    description: str | None

    def __post_init__(self) -> None:
        super().__post_init__()
        canonical_name = str(self.canonical_name).strip()
        if not canonical_name:
            raise ValueError("canonical_name must not be empty")
        object.__setattr__(self, "canonical_name", canonical_name)
        object.__setattr__(self, "aliases", tuple(str(v).strip() for v in self.aliases if str(v).strip()))
        object.__setattr__(self, "score", max(0.0, min(100.0, float(self.score))))
        object.__setattr__(self, "premium", bool(self.premium))
        for field_name in ("english_name", "origin_country", "breed_type", "description"):
            value = getattr(self, field_name)
            if value is not None:
                object.__setattr__(self, field_name, str(value).strip() or None)
        for field_name in ("flavor_score", "tenderness_score", "growth_score", "rarity_score"):
            value = getattr(self, field_name)
            if value is not None:
                object.__setattr__(self, field_name, max(0.0, min(100.0, float(value))))


@dataclass(frozen=True, kw_only=True)
class VenisonBreedMatch(RegistryMatch[VenisonBreed]):
    @property
    def breed(self) -> VenisonBreed:
        return self.entry


class VenisonBreedRegistry(BaseAliasRegistry[VenisonBreed]):
    registry_id = VENISON_BREED_REGISTRY_ID
    canonical_name_field = "canonical_name"
    aliases_field = "aliases"

    def __init__(self, loader: KnowledgeRegistryLoader | None = None) -> None:
        super().__init__(loader=loader or get_knowledge_registry_loader())

    def build_entry(self, registry_key: str, raw_entry: Mapping[str, Any]) -> VenisonBreed:
        known_fields = {"canonical_name", "aliases", "score", "premium", "english_name", "origin_country", "breed_type", "flavor_score", "tenderness_score", "growth_score", "rarity_score", "description"}
        metadata = {key: copy.deepcopy(value) for key, value in raw_entry.items() if key not in known_fields}
        canonical_name = str(raw_entry.get("canonical_name", registry_key)).strip()
        return VenisonBreed(
            registry_key=registry_key,
            canonical_name=canonical_name or registry_key,
            aliases=_aliases(canonical_name, raw_entry.get("aliases")),
            score=safe_float(raw_entry.get("score"), default=0.0),
            premium=bool(raw_entry.get("premium", False)),
            english_name=optional_string(raw_entry.get("english_name")),
            origin_country=optional_string(raw_entry.get("origin_country")),
            breed_type=optional_string(raw_entry.get("breed_type")),
            flavor_score=_optional_score(raw_entry.get("flavor_score")),
            tenderness_score=_optional_score(raw_entry.get("tenderness_score")),
            growth_score=_optional_score(raw_entry.get("growth_score")),
            rarity_score=_optional_score(raw_entry.get("rarity_score")),
            description=optional_string(raw_entry.get("description")),
            metadata=metadata,
        )

    def match(self, text: str) -> VenisonBreedMatch | None:
        raw_match = super().match(text)
        return None if raw_match is None else self._convert_match(raw_match)

    def find_all(self, text: str) -> list[VenisonBreedMatch]:
        return [self._convert_match(match) for match in super().find_all(text)]

    def lookup(self, text: str) -> VenisonBreed | None:
        match = self.match(text)
        return None if match is None else match.entry

    def list(self, *, premium_only: bool = False, breed_type: str | None = None) -> list[VenisonBreed]:
        entries = [entry for entry in super().list() if isinstance(entry, VenisonBreed)]
        if premium_only:
            entries = [entry for entry in entries if entry.premium]
        if breed_type is not None:
            normalized = str(breed_type).strip().lower()
            entries = [entry for entry in entries if (entry.breed_type or "").lower() == normalized]
        return sorted(entries, key=lambda entry: (-entry.score, entry.canonical_name))

    @staticmethod
    def _convert_match(raw_match: AliasMatch[VenisonBreed]) -> VenisonBreedMatch:
        return VenisonBreedMatch(entry=raw_match.entry, matched_alias=raw_match.matched_alias, normalized_alias=raw_match.normalized_alias, match_start=raw_match.match_start, match_end=raw_match.match_end, confidence=raw_match.confidence, exact_match=raw_match.exact_match)


__all__ = ["VENISON_BREED_REGISTRY_ID", "VenisonBreed", "VenisonBreedMatch", "VenisonBreedRegistry"]
