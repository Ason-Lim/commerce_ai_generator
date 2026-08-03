from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any, Mapping

from app.services.food.knowledge.common.base_model import RegistryEntry, RegistryMatch
from app.services.food.knowledge.common.base_registry import AliasMatch, BaseAliasRegistry, normalize_string_list, optional_string, safe_float
from app.services.food.knowledge.registry_loader import KnowledgeRegistryLoader, get_knowledge_registry_loader

CHICKEN_TYPE_REGISTRY_ID = "chicken.types"


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


@dataclass(frozen=True, kw_only=True)
class ChickenType(RegistryEntry):
    canonical_name: str
    aliases: tuple[str, ...]
    type_category: str
    score: float
    premium: bool
    flavor_intensity: str | None
    tenderness_level: str | None
    typical_uses: tuple[str, ...]
    description: str | None

    def __post_init__(self) -> None:
        super().__post_init__()
        canonical_name = str(self.canonical_name).strip()
        type_category = str(self.type_category).strip().lower()
        if not canonical_name:
            raise ValueError("canonical_name must not be empty")
        if not type_category:
            raise ValueError("type_category must not be empty")
        object.__setattr__(self, "canonical_name", canonical_name)
        object.__setattr__(self, "type_category", type_category)
        object.__setattr__(self, "aliases", tuple(str(v).strip() for v in self.aliases if str(v).strip()))
        object.__setattr__(self, "typical_uses", tuple(str(v).strip() for v in self.typical_uses if str(v).strip()))
        object.__setattr__(self, "score", max(0.0, min(100.0, float(self.score))))
        object.__setattr__(self, "premium", bool(self.premium))
        for field_name in ("flavor_intensity", "tenderness_level", "description"):
            value = getattr(self, field_name)
            if value is not None:
                object.__setattr__(self, field_name, str(value).strip() or None)


@dataclass(frozen=True, kw_only=True)
class ChickenTypeMatch(RegistryMatch[ChickenType]):
    @property
    def chicken_type(self) -> ChickenType:
        return self.entry


class ChickenTypeRegistry(BaseAliasRegistry[ChickenType]):
    registry_id = CHICKEN_TYPE_REGISTRY_ID
    canonical_name_field = "canonical_name"
    aliases_field = "aliases"

    def __init__(self, loader: KnowledgeRegistryLoader | None = None) -> None:
        super().__init__(loader=loader or get_knowledge_registry_loader())

    def build_entry(self, registry_key: str, raw_entry: Mapping[str, Any]) -> ChickenType:
        known_fields = {"canonical_name", "aliases", "type_category", "score", "premium", "flavor_intensity", "tenderness_level", "typical_uses", "description"}
        metadata = {key: copy.deepcopy(value) for key, value in raw_entry.items() if key not in known_fields}
        canonical_name = str(raw_entry.get("canonical_name", registry_key)).strip()
        return ChickenType(
            registry_key=registry_key,
            canonical_name=canonical_name or registry_key,
            aliases=_aliases(canonical_name, raw_entry.get("aliases")),
            type_category=str(raw_entry.get("type_category", registry_key)).strip().lower() or registry_key.lower(),
            score=safe_float(raw_entry.get("score"), default=0.0),
            premium=bool(raw_entry.get("premium", False)),
            flavor_intensity=optional_string(raw_entry.get("flavor_intensity")),
            tenderness_level=optional_string(raw_entry.get("tenderness_level")),
            typical_uses=normalize_string_list(raw_entry.get("typical_uses")),
            description=optional_string(raw_entry.get("description")),
            metadata=metadata,
        )

    def match(self, text: str) -> ChickenTypeMatch | None:
        raw_match = super().match(text)
        return None if raw_match is None else self._convert_match(raw_match)

    def find_all(self, text: str) -> list[ChickenTypeMatch]:
        return [self._convert_match(match) for match in super().find_all(text)]

    def lookup(self, text: str) -> ChickenType | None:
        match = self.match(text)
        return None if match is None else match.entry

    def list(self, *, premium_only: bool = False, type_category: str | None = None) -> list[ChickenType]:
        entries = [entry for entry in super().list() if isinstance(entry, ChickenType)]
        if premium_only:
            entries = [entry for entry in entries if entry.premium]
        if type_category is not None:
            normalized = str(type_category).strip().lower()
            entries = [entry for entry in entries if entry.type_category == normalized]
        return sorted(entries, key=lambda entry: (-entry.score, entry.canonical_name))

    @staticmethod
    def _convert_match(raw_match: AliasMatch[ChickenType]) -> ChickenTypeMatch:
        return ChickenTypeMatch(entry=raw_match.entry, matched_alias=raw_match.matched_alias, normalized_alias=raw_match.normalized_alias, match_start=raw_match.match_start, match_end=raw_match.match_end, confidence=raw_match.confidence, exact_match=raw_match.exact_match)


__all__ = ["CHICKEN_TYPE_REGISTRY_ID", "ChickenType", "ChickenTypeMatch", "ChickenTypeRegistry"]
