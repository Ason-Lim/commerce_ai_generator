from __future__ import annotations

import copy
from dataclasses import dataclass, fields
from typing import Any, Generic, Mapping, TypeVar


EntryT = TypeVar(
    "EntryT",
    bound="RegistryEntry",
)


def to_plain_value(
    value: Any,
) -> Any:
    """
    Registry 모델 값을 외부 API에서 사용하기 쉬운 형태로 변환한다.

    변환 규칙:
    - RegistryEntry -> dict
    - RegistryMatch -> dict
    - dataclass 내부 tuple -> list
    - Mapping -> dict
    - set/frozenset -> list
    - 나머지 값 -> deepcopy
    """
    if isinstance(value, RegistryEntry):
        return value.to_dict()

    if isinstance(value, RegistryMatch):
        return value.to_dict()

    if isinstance(value, Mapping):
        return {
            str(key): to_plain_value(item)
            for key, item in value.items()
        }

    if isinstance(
        value,
        (list, tuple, set, frozenset),
    ):
        return [
            to_plain_value(item)
            for item in value
        ]

    return copy.deepcopy(value)


@dataclass(
    frozen=True,
    kw_only=True,
)
class RegistryEntry:
    """
    모든 Knowledge Registry 항목의 공통 기반 모델.

    kw_only=True를 사용하는 이유:
    하위 dataclass가 필수 필드를 추가할 때 metadata의 기본값과
    필드 순서가 충돌하는 문제를 방지하기 위함이다.
    """

    registry_key: str
    metadata: dict[str, Any]

    def __post_init__(self) -> None:
        registry_key = str(
            self.registry_key
        ).strip()

        if not registry_key:
            raise ValueError(
                "registry_key must not be empty"
            )

        metadata = dict(
            self.metadata or {}
        )

        object.__setattr__(
            self,
            "registry_key",
            registry_key,
        )
        object.__setattr__(
            self,
            "metadata",
            copy.deepcopy(metadata),
        )

    def to_dict(self) -> dict[str, Any]:
        """
        dataclass의 모든 필드를 JSON 친화적인 dict로 변환한다.

        하위 모델에서 별도의 to_dict()를 작성하지 않아도
        추가 필드가 자동으로 포함된다.
        """
        return {
            item.name: to_plain_value(
                getattr(self, item.name)
            )
            for item in fields(self)
        }

    def metadata_value(
        self,
        key: str,
        default: Any = None,
    ) -> Any:
        return copy.deepcopy(
            self.metadata.get(
                key,
                default,
            )
        )

    def has_metadata(
        self,
        key: str,
    ) -> bool:
        return key in self.metadata


@dataclass(
    frozen=True,
    kw_only=True,
)
class RegistryMatch(
    Generic[EntryT]
):
    """
    별칭 기반 Registry 검색 결과의 공통 모델.
    """

    entry: EntryT
    matched_alias: str
    normalized_alias: str
    match_start: int
    match_end: int
    confidence: float
    exact_match: bool

    def __post_init__(self) -> None:
        if not isinstance(
            self.entry,
            RegistryEntry,
        ):
            raise TypeError(
                "entry must be a RegistryEntry "
                "instance"
            )

        match_start = int(
            self.match_start
        )
        match_end = int(
            self.match_end
        )

        if match_start < 0:
            raise ValueError(
                "match_start must be >= 0"
            )

        if match_end < match_start:
            raise ValueError(
                "match_end must be greater than "
                "or equal to match_start"
            )

        confidence = max(
            0.0,
            min(
                1.0,
                float(self.confidence),
            ),
        )

        object.__setattr__(
            self,
            "matched_alias",
            str(
                self.matched_alias
            ),
        )
        object.__setattr__(
            self,
            "normalized_alias",
            str(
                self.normalized_alias
            ),
        )
        object.__setattr__(
            self,
            "match_start",
            match_start,
        )
        object.__setattr__(
            self,
            "match_end",
            match_end,
        )
        object.__setattr__(
            self,
            "confidence",
            confidence,
        )
        object.__setattr__(
            self,
            "exact_match",
            bool(
                self.exact_match
            ),
        )

    @property
    def registry_key(self) -> str:
        return self.entry.registry_key

    @property
    def canonical_name(self) -> str | None:
        value = getattr(
            self.entry,
            "canonical_name",
            None,
        )

        if value is None:
            return None

        return str(value)

    @property
    def matched_length(self) -> int:
        return (
            self.match_end
            - self.match_start
        )

    def to_dict(self) -> dict[str, Any]:
        payload = self.entry.to_dict()

        payload.update(
            {
                "matched_alias": (
                    self.matched_alias
                ),
                "normalized_alias": (
                    self.normalized_alias
                ),
                "match_start": (
                    self.match_start
                ),
                "match_end": (
                    self.match_end
                ),
                "matched_length": (
                    self.matched_length
                ),
                "confidence": (
                    self.confidence
                ),
                "exact_match": (
                    self.exact_match
                ),
            }
        )

        return payload


__all__ = [
    "EntryT",
    "RegistryEntry",
    "RegistryMatch",
    "to_plain_value",
]
