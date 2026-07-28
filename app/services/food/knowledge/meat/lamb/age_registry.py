from __future__ import annotations

import copy
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Mapping

from app.services.food.knowledge.common.base_model import (
    RegistryEntry,
    RegistryMatch,
)
from app.services.food.knowledge.common.base_registry import (
    AliasMatch,
    BaseAliasRegistry,
    normalize_string_list,
    optional_int,
    optional_string,
    safe_float,
)
from app.services.food.knowledge.registry_loader import (
    KnowledgeRegistryLoader,
    get_knowledge_registry_loader,
)


LAMB_AGE_REGISTRY_ID = "lamb.ages"


@dataclass(
    frozen=True,
    kw_only=True,
)
class LambAge(
    RegistryEntry
):
    """
    양고기 연령 분류 Registry 항목.

    age_category:
        표준 연령 분류 코드.
        예: lamb, hogget, mutton

    min_age_months / max_age_months:
        연령 범위 참고값.

    permanent_incisor_min / permanent_incisor_max:
        영구 앞니 개수 범위 참고값.

    score:
        상품의 일반적인 연도 및 선호도 기준 점수.

    policy_region:
        해당 분류 기준을 적용하는 국가 또는 시장.

    source_version:
        Registry 데이터의 기준 출처 버전.
    """

    canonical_name: str
    aliases: tuple[str, ...]
    age_category: str
    score: float
    premium: bool

    min_age_months: int | None
    max_age_months: int | None

    permanent_incisor_min: int | None
    permanent_incisor_max: int | None

    flavor_intensity: str | None
    tenderness_level: str | None

    policy_region: str | None
    source_version: str | None
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

        age_category = str(
            self.age_category
        ).strip().lower()

        if not age_category:
            raise ValueError(
                "age_category must not be empty"
            )

        aliases = tuple(
            str(alias).strip()
            for alias in self.aliases
            if str(alias).strip()
        )

        object.__setattr__(
            self,
            "canonical_name",
            canonical_name,
        )
        object.__setattr__(
            self,
            "age_category",
            age_category,
        )
        object.__setattr__(
            self,
            "aliases",
            aliases,
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

        for field_name in (
            "flavor_intensity",
            "tenderness_level",
            "policy_region",
            "source_version",
            "description",
        ):
            value = getattr(
                self,
                field_name,
            )

            if value is not None:
                object.__setattr__(
                    self,
                    field_name,
                    str(value).strip() or None,
                )

        if (
            self.min_age_months is not None
            and self.max_age_months is not None
            and self.min_age_months
            > self.max_age_months
        ):
            raise ValueError(
                "min_age_months must not exceed "
                "max_age_months"
            )

        if (
            self.permanent_incisor_min is not None
            and self.permanent_incisor_max is not None
            and self.permanent_incisor_min
            > self.permanent_incisor_max
        ):
            raise ValueError(
                "permanent_incisor_min must not exceed "
                "permanent_incisor_max"
            )


@dataclass(
    frozen=True,
    kw_only=True,
)
class LambAgeMatch(
    RegistryMatch[LambAge]
):
    """
    상품명에서 탐지된 양고기 연령 분류 결과.
    """

    @property
    def age(self) -> LambAge:
        return self.entry


class LambAgeRegistry(
    BaseAliasRegistry[LambAge]
):
    """
    YAML 기반 양고기 연령 분류 Registry.

    Registry data:
        app/services/food/registry_data/lamb/ages.yaml
    """

    registry_id = LAMB_AGE_REGISTRY_ID
    canonical_name_field = "canonical_name"
    aliases_field = "aliases"

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

    def build_entry(
        self,
        registry_key: str,
        raw_entry: Mapping[str, Any],
    ) -> LambAge:
        known_fields = {
            "canonical_name",
            "aliases",
            "age_category",
            "score",
            "premium",
            "min_age_months",
            "max_age_months",
            "permanent_incisor_min",
            "permanent_incisor_max",
            "flavor_intensity",
            "tenderness_level",
            "policy_region",
            "source_version",
            "description",
        }

        metadata = {
            key: copy.deepcopy(value)
            for key, value in raw_entry.items()
            if key not in known_fields
        }

        canonical_name = str(
            raw_entry.get(
                "canonical_name",
                registry_key,
            )
        ).strip()

        age_category = str(
            raw_entry.get(
                "age_category",
                registry_key,
            )
        ).strip().lower()

        return LambAge(
            registry_key=registry_key,
            canonical_name=(
                canonical_name
                or registry_key
            ),
            aliases=self._build_entry_aliases(
                canonical_name=canonical_name,
                raw_aliases=raw_entry.get(
                    "aliases"
                ),
            ),
            age_category=(
                age_category
                or registry_key.lower()
            ),
            score=safe_float(
                raw_entry.get("score"),
                default=0.0,
            ),
            premium=bool(
                raw_entry.get(
                    "premium",
                    False,
                )
            ),
            min_age_months=optional_int(
                raw_entry.get(
                    "min_age_months"
                )
            ),
            max_age_months=optional_int(
                raw_entry.get(
                    "max_age_months"
                )
            ),
            permanent_incisor_min=optional_int(
                raw_entry.get(
                    "permanent_incisor_min"
                )
            ),
            permanent_incisor_max=optional_int(
                raw_entry.get(
                    "permanent_incisor_max"
                )
            ),
            flavor_intensity=optional_string(
                raw_entry.get(
                    "flavor_intensity"
                )
            ),
            tenderness_level=optional_string(
                raw_entry.get(
                    "tenderness_level"
                )
            ),
            policy_region=optional_string(
                raw_entry.get(
                    "policy_region"
                )
            ),
            source_version=optional_string(
                raw_entry.get(
                    "source_version"
                )
            ),
            description=optional_string(
                raw_entry.get(
                    "description"
                )
            ),
            metadata=metadata,
        )

    def match(
        self,
        text: str,
    ) -> LambAgeMatch | None:
        raw_match = super().match(text)

        if raw_match is None:
            return None

        return self._convert_match(
            raw_match
        )

    def find_all(
        self,
        text: str,
    ) -> list[LambAgeMatch]:
        return [
            self._convert_match(match)
            for match in super().find_all(text)
        ]

    def lookup(
        self,
        text: str,
    ) -> LambAge | None:
        match = self.match(text)

        if match is None:
            return None

        return match.entry

    def list(
        self,
    ) -> list[LambAge]:
        return [
            entry
            for entry in super().list()
            if isinstance(entry, LambAge)
        ]

    def list_by_age(
        self,
    ) -> list[LambAge]:
        """
        최소 연령 기준으로 정렬해 반환한다.
        """
        return sorted(
            self.list(),
            key=lambda entry: (
                entry.min_age_months
                if entry.min_age_months
                is not None
                else 10**9,
                entry.canonical_name,
            ),
        )

    def _convert_match(
        self,
        match: AliasMatch[LambAge],
    ) -> LambAgeMatch:
        if not isinstance(
            match.entry,
            LambAge,
        ):
            raise TypeError(
                "matched entry must be LambAge"
            )

        return LambAgeMatch(
            entry=match.entry,
            matched_alias=(
                match.matched_alias
            ),
            normalized_alias=(
                match.normalized_alias
            ),
            match_start=match.match_start,
            match_end=match.match_end,
            confidence=match.confidence,
            exact_match=match.exact_match,
        )

    def _build_entry_aliases(
        self,
        *,
        canonical_name: str,
        raw_aliases: Any,
    ) -> tuple[str, ...]:
        aliases = normalize_string_list(
            raw_aliases
        )

        ordered: list[str] = []
        seen: set[str] = set()

        for alias in (
            canonical_name,
            *aliases,
        ):
            normalized_alias = str(
                alias
            ).strip()

            if not normalized_alias:
                continue

            dedupe_key = self.normalize_text(
                normalized_alias
            )

            if (
                not dedupe_key
                or dedupe_key in seen
            ):
                continue

            seen.add(dedupe_key)
            ordered.append(
                normalized_alias
            )

        return tuple(ordered)


@lru_cache(maxsize=1)
def get_lamb_age_registry() -> LambAgeRegistry:
    return LambAgeRegistry()


def get_lamb_age(
    registry_key: str,
) -> LambAge | None:
    return get_lamb_age_registry().get(
        registry_key
    )


def lookup_lamb_age(
    text: str,
) -> LambAge | None:
    return get_lamb_age_registry().lookup(
        text
    )


def match_lamb_age(
    text: str,
) -> LambAgeMatch | None:
    return get_lamb_age_registry().match(
        text
    )


def list_lamb_ages() -> list[LambAge]:
    return get_lamb_age_registry().list()


__all__ = [
    "LAMB_AGE_REGISTRY_ID",
    "LambAge",
    "LambAgeMatch",
    "LambAgeRegistry",
    "get_lamb_age_registry",
    "get_lamb_age",
    "lookup_lamb_age",
    "match_lamb_age",
    "list_lamb_ages",
]
