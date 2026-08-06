from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any, Generic, Mapping, TypeVar

from app.services.food.knowledge.common.base_model import (
    RegistryEntry,
    RegistryMatch,
)
from app.services.food.knowledge.common.base_registry import (
    AliasMatch,
    BaseAliasRegistry,
    normalize_string_list,
    optional_string,
    safe_float,
)
from app.services.food.knowledge.registry_loader import (
    KnowledgeRegistryLoader,
    get_knowledge_registry_loader,
)


def build_aliases(
    canonical_name: str,
    raw_aliases: Any,
) -> tuple[str, ...]:
    """
    canonical_name을 포함하는 중복 없는 alias tuple을 만든다.

    비교에는 casefold를 사용하지만 원본 표기는 보존한다.
    """
    values = [
        canonical_name,
        *normalize_string_list(raw_aliases),
    ]

    result: list[str] = []
    seen: set[str] = set()

    for value in values:
        text = str(value).strip()
        key = text.casefold()

        if not text or key in seen:
            continue

        seen.add(key)
        result.append(text)

    return tuple(result)


@dataclass(
    frozen=True,
    kw_only=True,
)
class HerbSpiceRegistryEntry(RegistryEntry):
    """
    Herb & Spice Registry 공통 immutable entry 계약.

    Registry는 데이터만 보관하며,
    파싱·점수 계산·비즈니스 로직을 수행하지 않는다.
    """

    canonical_name: str
    aliases: tuple[str, ...]
    score: float
    premium: bool
    description: str | None

    def __post_init__(self) -> None:
        super().__post_init__()

        canonical_name = str(
            self.canonical_name
        ).strip()

        if not canonical_name:
            raise ValueError(
                "canonical_name must not be empty"
            )

        object.__setattr__(
            self,
            "canonical_name",
            canonical_name,
        )
        object.__setattr__(
            self,
            "aliases",
            build_aliases(
                canonical_name,
                self.aliases,
            ),
        )
        object.__setattr__(
            self,
            "score",
            max(
                0.0,
                min(
                    100.0,
                    float(self.score),
                ),
            ),
        )
        object.__setattr__(
            self,
            "premium",
            bool(self.premium),
        )
        object.__setattr__(
            self,
            "description",
            optional_string(
                self.description
            ),
        )


EntryT = TypeVar(
    "EntryT",
    bound=HerbSpiceRegistryEntry,
)


class HerbSpiceAliasRegistry(
    BaseAliasRegistry[EntryT],
    Generic[EntryT],
):
    """
    Herb & Spice 선언형 Alias Registry 공통 기반.

    YAML loading, alias lookup, longest-match 처리는
    공통 BaseAliasRegistry 계약을 그대로 사용한다.
    """

    canonical_name_field = "canonical_name"
    aliases_field = "aliases"

    entry_class: type[EntryT]

    def __init__(
        self,
        loader: KnowledgeRegistryLoader | None = None,
    ) -> None:
        super().__init__(
            loader=(
                loader
                or get_knowledge_registry_loader()
            )
        )

    def common_fields(
        self,
        *,
        registry_key: str,
        raw_entry: Mapping[str, Any],
        known_fields: set[str],
    ) -> dict[str, Any]:
        """
        YAML entry에서 공통 Registry 필드를 생성한다.

        known_fields에 없는 값은 metadata에 보존한다.
        """
        canonical_name = str(
            raw_entry.get(
                "canonical_name",
                registry_key,
            )
        ).strip()

        metadata = {
            key: copy.deepcopy(value)
            for key, value in raw_entry.items()
            if key not in known_fields
        }

        return {
            "registry_key": registry_key,
            "canonical_name": (
                canonical_name or registry_key
            ),
            "aliases": build_aliases(
                canonical_name or registry_key,
                raw_entry.get("aliases"),
            ),
            "score": safe_float(
                raw_entry.get("score"),
                default=0.0,
            ),
            "premium": bool(
                raw_entry.get("premium", False)
            ),
            "description": optional_string(
                raw_entry.get("description")
            ),
            "metadata": metadata,
        }

    def convert_match(
        self,
        raw_match: AliasMatch[EntryT],
        match_class: type[RegistryMatch[EntryT]],
    ) -> RegistryMatch[EntryT]:
        """
        공통 AliasMatch를 도메인별 typed RegistryMatch로 변환한다.
        """
        return match_class(
            entry=raw_match.entry,
            matched_alias=raw_match.matched_alias,
            normalized_alias=raw_match.normalized_alias,
            confidence=raw_match.confidence,
            match_start=raw_match.match_start,
            match_end=raw_match.match_end,
            exact_match=raw_match.exact_match,
        )


__all__ = [
    "HerbSpiceAliasRegistry",
    "HerbSpiceRegistryEntry",
    "build_aliases",
]
