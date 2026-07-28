from __future__ import annotations

import copy
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from threading import RLock
from typing import Any, Generic, Iterable, Mapping, TypeVar

from app.services.food.knowledge.registry_loader import (
    KnowledgeRegistryLoader,
    get_knowledge_registry_loader,
)


EntryT = TypeVar("EntryT")


class DomainRegistryError(RuntimeError):
    """도메인 전용 Knowledge Registry 기본 예외."""


class DomainRegistryEntryNotFoundError(
    DomainRegistryError
):
    """요청한 Registry 엔트리를 찾지 못한 경우."""


class DomainRegistryConfigurationError(
    DomainRegistryError
):
    """Registry 설정 또는 데이터 구조가 잘못된 경우."""


@dataclass(frozen=True)
class AliasCandidate:
    """
    Registry 엔트리의 검색 가능한 별칭 정보.
    """

    registry_key: str
    alias: str
    normalized_alias: str
    canonical_name: str
    priority: int = 0
    metadata: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "registry_key": self.registry_key,
            "alias": self.alias,
            "normalized_alias": (
                self.normalized_alias
            ),
            "canonical_name": (
                self.canonical_name
            ),
            "priority": self.priority,
            "metadata": copy.deepcopy(
                self.metadata or {}
            ),
        }


@dataclass(frozen=True)
class AliasMatch(Generic[EntryT]):
    """
    자유 텍스트에서 발견한 Registry 엔트리 매칭 결과.
    """

    entry: EntryT
    registry_key: str
    canonical_name: str
    matched_alias: str
    normalized_alias: str
    match_start: int
    match_end: int
    confidence: float
    exact_match: bool
    metadata: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        entry = self.entry

        if hasattr(entry, "to_dict"):
            entry_payload = entry.to_dict()
        elif isinstance(entry, Mapping):
            entry_payload = copy.deepcopy(
                dict(entry)
            )
        else:
            entry_payload = {
                "value": copy.deepcopy(entry)
            }

        return {
            "entry": entry_payload,
            "registry_key": self.registry_key,
            "canonical_name": (
                self.canonical_name
            ),
            "matched_alias": self.matched_alias,
            "normalized_alias": (
                self.normalized_alias
            ),
            "match_start": self.match_start,
            "match_end": self.match_end,
            "confidence": self.confidence,
            "exact_match": self.exact_match,
            "metadata": copy.deepcopy(
                self.metadata or {}
            ),
        }


class BaseKnowledgeRegistry(
    Generic[EntryT],
    ABC,
):
    """
    KnowledgeRegistryLoader 위에 구축되는 도메인 Registry 기반 클래스.

    하위 클래스는 다음을 정의한다.

    - registry_id
    - build_entry()
    """

    registry_id: str = ""

    def __init__(
        self,
        loader: KnowledgeRegistryLoader | None = None,
    ) -> None:
        if not self.registry_id:
            raise DomainRegistryConfigurationError(
                f"{type(self).__name__}.registry_id "
                "must not be empty."
            )

        self.loader = (
            loader
            or get_knowledge_registry_loader()
        )

    @abstractmethod
    def build_entry(
        self,
        registry_key: str,
        raw_entry: Mapping[str, Any],
    ) -> EntryT:
        """원시 Registry 데이터를 도메인 엔트리로 변환한다."""

    def get(
        self,
        registry_key: str,
        *,
        required: bool = False,
    ) -> EntryT | None:
        raw_entry = self.loader.get_entry(
            self.registry_id,
            registry_key,
            default=None,
        )

        if raw_entry is None:
            if required:
                raise (
                    DomainRegistryEntryNotFoundError(
                        f"{self.registry_id}: unknown "
                        f"registry key {registry_key!r}"
                    )
                )

            return None

        if not isinstance(raw_entry, Mapping):
            raise DomainRegistryConfigurationError(
                f"{self.registry_id}.{registry_key}: "
                "entry must be a mapping."
            )

        return self.build_entry(
            registry_key,
            raw_entry,
        )

    def require(
        self,
        registry_key: str,
    ) -> EntryT:
        entry = self.get(
            registry_key,
            required=True,
        )

        assert entry is not None
        return entry

    def contains(
        self,
        registry_key: str,
    ) -> bool:
        return self.loader.contains(
            self.registry_id,
            registry_key,
        )

    def keys(self) -> list[str]:
        return self.loader.list_entries(
            self.registry_id
        )

    def list(
        self,
    ) -> list[EntryT]:
        raw_data = self.loader.load_data(
            self.registry_id
        )

        if not raw_data:
            return []

        result: list[EntryT] = []

        for registry_key, raw_entry in (
            raw_data.items()
        ):
            if not isinstance(
                raw_entry,
                Mapping,
            ):
                raise (
                    DomainRegistryConfigurationError(
                        f"{self.registry_id}."
                        f"{registry_key}: entry must "
                        "be a mapping."
                    )
                )

            result.append(
                self.build_entry(
                    registry_key,
                    raw_entry,
                )
            )

        return result

    def raw_data(
        self,
    ) -> dict[str, Any]:
        return (
            self.loader.load_data(
                self.registry_id
            )
            or {}
        )

    def raw_entry(
        self,
        registry_key: str,
        *,
        default: Any = None,
    ) -> Any:
        return self.loader.get_entry(
            self.registry_id,
            registry_key,
            default=default,
        )

    def reload(self) -> None:
        self.loader.clear_cache(
            self.registry_id
        )

        self._clear_local_cache()

    def _clear_local_cache(self) -> None:
        """
        하위 클래스의 로컬 인덱스 캐시를 비우는 훅.
        """


class BaseAliasRegistry(
    BaseKnowledgeRegistry[EntryT],
    ABC,
):
    """
    별칭 검색을 지원하는 도메인 Registry 기반 클래스.

    YAML 엔트리에서 기본적으로 다음 필드를 읽는다.

    canonical_name: 표준 이름
    aliases: 별칭 목록
    """

    canonical_name_field = "canonical_name"
    aliases_field = "aliases"

    def __init__(
        self,
        loader: KnowledgeRegistryLoader | None = None,
    ) -> None:
        super().__init__(loader=loader)

        self._alias_index: (
            tuple[AliasCandidate, ...] | None
        ) = None

        self._index_lock = RLock()

    def normalize_text(
        self,
        value: Any,
    ) -> str:
        """
        기본 별칭 비교 정규화.

        - 소문자 변환
        - 공백과 구두점 제거
        - 숫자, 영문, 한글, + 유지

        하위 Registry에서 필요하면 재정의할 수 있다.
        """

        if value is None:
            return ""

        text = str(value).strip().lower()
        text = text.replace("＋", "+")

        return re.sub(
            r"[^0-9a-z가-힣+]+",
            "",
            text,
        )

    def canonical_name_from_raw(
        self,
        registry_key: str,
        raw_entry: Mapping[str, Any],
    ) -> str:
        value = raw_entry.get(
            self.canonical_name_field,
            registry_key,
        )

        normalized = str(value).strip()

        return normalized or registry_key

    def aliases_from_raw(
        self,
        registry_key: str,
        raw_entry: Mapping[str, Any],
    ) -> list[str]:
        """
        표준명과 aliases를 합쳐 중복 없는 별칭 목록을 만든다.
        """

        canonical_name = (
            self.canonical_name_from_raw(
                registry_key,
                raw_entry,
            )
        )

        raw_aliases = raw_entry.get(
            self.aliases_field,
            [],
        )

        values: list[Any] = [
            canonical_name,
        ]

        if isinstance(
            raw_aliases,
            (list, tuple, set),
        ):
            values.extend(raw_aliases)

        elif raw_aliases:
            values.append(raw_aliases)

        result: list[str] = []
        seen: set[str] = set()

        for value in values:
            alias = str(value).strip()

            if not alias:
                continue

            normalized_alias = (
                self.normalize_text(alias)
            )

            if (
                not normalized_alias
                or normalized_alias in seen
            ):
                continue

            seen.add(normalized_alias)
            result.append(alias)

        return result

    def alias_metadata_from_raw(
        self,
        registry_key: str,
        raw_entry: Mapping[str, Any],
    ) -> dict[str, Any]:
        """
        별칭 후보에 저장할 부가 정보.

        국가, 카테고리 등 검색 우선순위 판단에 필요한 값은
        하위 클래스에서 재정의할 수 있다.
        """

        return {}

    def lookup(
        self,
        query: str,
        *,
        required: bool = False,
    ) -> EntryT | None:
        match = self.match(query)

        if match is not None:
            return match.entry

        if required:
            raise DomainRegistryEntryNotFoundError(
                f"{self.registry_id}: no match "
                f"for {query!r}"
            )

        return None

    def match(
        self,
        text: str,
    ) -> AliasMatch[EntryT] | None:
        normalized_text = self.normalize_text(
            text
        )

        if not normalized_text:
            return None

        matches: list[
            tuple[
                tuple[int, int, int, int],
                AliasCandidate,
                int,
            ]
        ] = []

        for candidate in self.alias_candidates():
            position = normalized_text.find(
                candidate.normalized_alias
            )

            if position < 0:
                continue

            exact_match = (
                normalized_text
                == candidate.normalized_alias
            )

            ranking = (
                int(exact_match),
                len(
                    candidate.normalized_alias
                ),
                candidate.priority,
                -position,
            )

            matches.append(
                (
                    ranking,
                    candidate,
                    position,
                )
            )

        if not matches:
            return None

        matches.sort(
            key=lambda item: item[0],
            reverse=True,
        )

        _, candidate, position = matches[0]

        return self._build_match(
            normalized_text=normalized_text,
            candidate=candidate,
            position=position,
        )

    def find_all(
        self,
        text: str,
    ) -> list[AliasMatch[EntryT]]:
        normalized_text = self.normalize_text(
            text
        )

        if not normalized_text:
            return []

        best_by_key: dict[
            str,
            AliasMatch[EntryT],
        ] = {}

        for candidate in self.alias_candidates():
            position = normalized_text.find(
                candidate.normalized_alias
            )

            if position < 0:
                continue

            match = self._build_match(
                normalized_text=normalized_text,
                candidate=candidate,
                position=position,
            )

            existing = best_by_key.get(
                candidate.registry_key
            )

            if (
                existing is None
                or self._match_sort_key(match)
                > self._match_sort_key(existing)
            ):
                best_by_key[
                    candidate.registry_key
                ] = match

        return sorted(
            best_by_key.values(),
            key=self._match_sort_key,
            reverse=True,
        )

    def aliases(self) -> list[str]:
        values = {
            candidate.alias
            for candidate
            in self.alias_candidates()
        }

        return sorted(
            values,
            key=lambda alias: (
                -len(
                    self.normalize_text(alias)
                ),
                alias,
            ),
        )

    def alias_candidates(
        self,
    ) -> tuple[AliasCandidate, ...]:
        with self._index_lock:
            if self._alias_index is None:
                self._alias_index = (
                    self._build_alias_index()
                )

            return self._alias_index

    def _build_alias_index(
        self,
    ) -> tuple[AliasCandidate, ...]:
        raw_data = self.raw_data()

        candidates: list[AliasCandidate] = []

        for registry_key, raw_entry in (
            raw_data.items()
        ):
            if not isinstance(
                raw_entry,
                Mapping,
            ):
                raise (
                    DomainRegistryConfigurationError(
                        f"{self.registry_id}."
                        f"{registry_key}: entry must "
                        "be a mapping."
                    )
                )

            canonical_name = (
                self.canonical_name_from_raw(
                    registry_key,
                    raw_entry,
                )
            )

            aliases = self.aliases_from_raw(
                registry_key,
                raw_entry,
            )

            metadata = (
                self.alias_metadata_from_raw(
                    registry_key,
                    raw_entry,
                )
            )

            alias_count = len(aliases)

            for index, alias in enumerate(
                aliases
            ):
                normalized_alias = (
                    self.normalize_text(alias)
                )

                if not normalized_alias:
                    continue

                candidates.append(
                    AliasCandidate(
                        registry_key=registry_key,
                        alias=alias,
                        normalized_alias=(
                            normalized_alias
                        ),
                        canonical_name=(
                            canonical_name
                        ),
                        priority=(
                            alias_count - index
                        ),
                        metadata=copy.deepcopy(
                            metadata
                        ),
                    )
                )

        candidates.sort(
            key=lambda candidate: (
                len(
                    candidate.normalized_alias
                ),
                candidate.priority,
                candidate.registry_key,
            ),
            reverse=True,
        )

        return tuple(candidates)

    def calculate_match_confidence(
        self,
        *,
        normalized_text: str,
        candidate: AliasCandidate,
        exact_match: bool,
    ) -> float:
        """
        기본 매칭 신뢰도.

        부분 일치: 0.75
        정확 일치: +0.20
        긴 별칭: 최대 +0.05
        """

        confidence = 0.75

        if exact_match:
            confidence += 0.20

        alias_length_bonus = min(
            len(candidate.normalized_alias)
            / 100,
            0.05,
        )

        confidence += alias_length_bonus

        return round(
            min(confidence, 1.0),
            2,
        )

    def _build_match(
        self,
        *,
        normalized_text: str,
        candidate: AliasCandidate,
        position: int,
    ) -> AliasMatch[EntryT]:
        entry = self.require(
            candidate.registry_key
        )

        exact_match = (
            normalized_text
            == candidate.normalized_alias
        )

        confidence = (
            self.calculate_match_confidence(
                normalized_text=(
                    normalized_text
                ),
                candidate=candidate,
                exact_match=exact_match,
            )
        )

        return AliasMatch(
            entry=entry,
            registry_key=(
                candidate.registry_key
            ),
            canonical_name=(
                candidate.canonical_name
            ),
            matched_alias=candidate.alias,
            normalized_alias=(
                candidate.normalized_alias
            ),
            match_start=position,
            match_end=(
                position
                + len(
                    candidate.normalized_alias
                )
            ),
            confidence=confidence,
            exact_match=exact_match,
            metadata=copy.deepcopy(
                candidate.metadata or {}
            ),
        )

    @staticmethod
    def _match_sort_key(
        match: AliasMatch[EntryT],
    ) -> tuple[float, int, int]:
        return (
            match.confidence,
            len(match.normalized_alias),
            -match.match_start,
        )

    def clear_cache(self) -> None:
        """
        Registry의 로컬 별칭 인덱스 캐시를 초기화한다.

        Loader가 보관하는 YAML 데이터 캐시는 유지한다.
        YAML 데이터까지 다시 읽어야 할 때는 reload()를 사용한다.
        """
        self._clear_local_cache()

    def _clear_local_cache(self) -> None:
        with self._index_lock:
            self._alias_index = None


def optional_string(
    value: Any,
) -> str | None:
    if value is None:
        return None

    normalized = str(value).strip()

    return normalized or None


def safe_float(
    value: Any,
    *,
    default: float = 0.0,
) -> float:
    try:
        return float(value)
    except (
        TypeError,
        ValueError,
    ):
        return default


def optional_float(
    value: Any,
) -> float | None:
    if value is None:
        return None

    try:
        return float(value)
    except (
        TypeError,
        ValueError,
    ):
        return None


def optional_int(
    value: Any,
) -> int | None:
    if value is None:
        return None

    try:
        return int(value)
    except (
        TypeError,
        ValueError,
    ):
        return None


def normalize_string_list(
    value: Any,
) -> tuple[str, ...]:
    if value is None:
        return ()

    if isinstance(
        value,
        (list, tuple, set),
    ):
        values: Iterable[Any] = value
    else:
        values = (value,)

    result: list[str] = []
    seen: set[str] = set()

    for item in values:
        normalized = str(item).strip()

        if (
            not normalized
            or normalized in seen
        ):
            continue

        seen.add(normalized)
        result.append(normalized)

    return tuple(result)


__all__ = [
    "EntryT",
    "DomainRegistryError",
    "DomainRegistryEntryNotFoundError",
    "DomainRegistryConfigurationError",
    "AliasCandidate",
    "AliasMatch",
    "BaseKnowledgeRegistry",
    "BaseAliasRegistry",
    "optional_string",
    "safe_float",
    "optional_float",
    "optional_int",
    "normalize_string_list",
]
