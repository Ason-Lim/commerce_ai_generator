from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Any, Mapping

from app.services.food.knowledge.common.base_registry import (
    AliasCandidate,
    BaseAliasRegistry,
    DomainRegistryEntryNotFoundError,
    optional_float,
    optional_int,
    optional_string,
    safe_float,
)
from app.services.food.knowledge.registry_loader import (
    KnowledgeRegistryLoader,
    get_knowledge_registry_loader,
)


BEEF_GRADE_REGISTRY_ID = "beef.grades"


COUNTRY_ALIASES: dict[str, tuple[str, ...]] = {
    "KR": (
        "대한민국",
        "한국",
        "국내산",
        "한우",
        "육우",
        "korea",
        "korean",
    ),
    "US": (
        "미국",
        "미국산",
        "us",
        "usa",
        "american",
        "usda",
    ),
    "AU": (
        "호주",
        "호주산",
        "australia",
        "australian",
        "aus-meat",
        "aus meat",
        "msa",
    ),
    "JP": (
        "일본",
        "일본산",
        "일본 와규",
        "japan",
        "japanese",
        "jmga",
    ),
}


@dataclass(frozen=True)
class BeefGrade:
    """표준화된 쇠고기 등급 정보."""

    registry_key: str
    country_code: str
    country_name: str | None
    system: str | None
    canonical_grade: str
    aliases: tuple[str, ...]
    score: float
    premium: bool
    rank: int | None = None
    description: str | None = None
    marbling_min: float | None = None
    yield_grade: str | None = None
    quality_grade: int | None = None
    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "registry_key": self.registry_key,
            "country_code": self.country_code,
            "country_name": self.country_name,
            "system": self.system,
            "canonical_grade": self.canonical_grade,
            "aliases": list(self.aliases),
            "score": self.score,
            "premium": self.premium,
            "rank": self.rank,
            "description": self.description,
            "marbling_min": self.marbling_min,
            "yield_grade": self.yield_grade,
            "quality_grade": self.quality_grade,
            "metadata": copy.deepcopy(
                self.metadata
            ),
        }


@dataclass(frozen=True)
class BeefGradeMatch:
    """상품명에서 탐지된 쇠고기 등급 결과."""

    grade: BeefGrade
    matched_alias: str
    normalized_alias: str
    match_start: int
    match_end: int
    confidence: float
    country_hint: str | None = None

    @property
    def registry_key(self) -> str:
        return self.grade.registry_key

    @property
    def canonical_grade(self) -> str:
        return self.grade.canonical_grade

    def to_dict(self) -> dict[str, Any]:
        payload = self.grade.to_dict()

        payload.update(
            {
                "matched_alias": self.matched_alias,
                "normalized_alias": (
                    self.normalized_alias
                ),
                "match_start": self.match_start,
                "match_end": self.match_end,
                "confidence": self.confidence,
                "country_hint": self.country_hint,
            }
        )

        return payload


class BeefGradeRegistry(
    BaseAliasRegistry[BeefGrade]
):
    """
    YAML 기반 쇠고기 등급 Registry.

    기존 공개 API를 유지하면서 별칭 인덱스, 조회,
    다중 탐지 및 캐시 기능은 BaseAliasRegistry를 사용한다.
    """

    registry_id = BEEF_GRADE_REGISTRY_ID
    canonical_name_field = "canonical_grade"
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
    ) -> BeefGrade:
        known_fields = {
            "country_code",
            "country_name",
            "system",
            "canonical_grade",
            "aliases",
            "score",
            "premium",
            "rank",
            "description",
            "marbling_min",
            "yield_grade",
            "quality_grade",
        }

        metadata = {
            key: copy.deepcopy(value)
            for key, value in raw_entry.items()
            if key not in known_fields
        }

        canonical_grade = str(
            raw_entry.get(
                "canonical_grade",
                registry_key,
            )
        ).strip()

        return BeefGrade(
            registry_key=registry_key,
            country_code=(
                normalize_country_code(
                    raw_entry.get("country_code")
                )
                or ""
            ),
            country_name=optional_string(
                raw_entry.get("country_name")
            ),
            system=optional_string(
                raw_entry.get("system")
            ),
            canonical_grade=(
                canonical_grade or registry_key
            ),
            aliases=self._entry_aliases(
                canonical_grade,
                raw_entry.get("aliases"),
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
            rank=optional_int(
                raw_entry.get("rank")
            ),
            description=optional_string(
                raw_entry.get("description")
            ),
            marbling_min=optional_float(
                raw_entry.get("marbling_min")
            ),
            yield_grade=optional_string(
                raw_entry.get("yield_grade")
            ),
            quality_grade=optional_int(
                raw_entry.get("quality_grade")
            ),
            metadata=metadata,
        )

    def normalize_text(
        self,
        value: Any,
    ) -> str:
        return normalize_grade_text(value)

    def alias_metadata_from_raw(
        self,
        registry_key: str,
        raw_entry: Mapping[str, Any],
    ) -> dict[str, Any]:
        return {
            "country_code": (
                normalize_country_code(
                    raw_entry.get("country_code")
                )
            ),
            "system": optional_string(
                raw_entry.get("system")
            ),
        }

    def get(
        self,
        registry_key: str,
        *,
        required: bool = False,
    ) -> BeefGrade | None:
        return super().get(
            registry_key,
            required=required,
        )

    def lookup(
        self,
        query: str,
        *,
        country_code: str | None = None,
        required: bool = False,
    ) -> BeefGrade | None:
        match = self.match(
            query,
            country_code=country_code,
        )

        if match is not None:
            return match.grade

        if required:
            raise DomainRegistryEntryNotFoundError(
                f"{self.registry_id}: no grade "
                f"match for {query!r}"
            )

        return None

    def match(
        self,
        text: str,
        *,
        country_code: str | None = None,
    ) -> BeefGradeMatch | None:
        normalized_text = self.normalize_text(
            text
        )

        if not normalized_text:
            return None

        requested_country = (
            normalize_country_code(country_code)
        )

        detected_country = (
            requested_country
            or detect_country_code(text)
        )

        matches: list[
            tuple[
                tuple[int, int, int, int],
                AliasCandidate,
                int,
            ]
        ] = []

        for candidate in self.alias_candidates():
            candidate_country = (
                normalize_country_code(
                    (candidate.metadata or {}).get(
                        "country_code"
                    )
                )
            )

            if (
                requested_country
                and candidate_country
                != requested_country
            ):
                continue

            position = normalized_text.find(
                candidate.normalized_alias
            )

            if position < 0:
                continue

            exact_match = (
                normalized_text
                == candidate.normalized_alias
            )

            country_match = bool(
                detected_country
                and candidate_country
                == detected_country
            )

            ranking = (
                int(country_match),
                int(exact_match),
                len(candidate.normalized_alias),
                candidate.priority,
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

        grade = self.require(
            candidate.registry_key
        )

        confidence = (
            self._calculate_grade_confidence(
                normalized_text=normalized_text,
                candidate=candidate,
                grade=grade,
                detected_country=(
                    detected_country
                ),
            )
        )

        return BeefGradeMatch(
            grade=grade,
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
            country_hint=detected_country,
        )

    def find_all(
        self,
        text: str,
        *,
        country_code: str | None = None,
    ) -> list[BeefGradeMatch]:
        normalized_text = self.normalize_text(
            text
        )

        if not normalized_text:
            return []

        requested_country = (
            normalize_country_code(country_code)
        )

        detected_country = (
            requested_country
            or detect_country_code(text)
        )

        best_by_key: dict[
            str,
            BeefGradeMatch,
        ] = {}

        for candidate in self.alias_candidates():
            candidate_country = (
                normalize_country_code(
                    (candidate.metadata or {}).get(
                        "country_code"
                    )
                )
            )

            if (
                requested_country
                and candidate_country
                != requested_country
            ):
                continue

            position = normalized_text.find(
                candidate.normalized_alias
            )

            if position < 0:
                continue

            grade = self.require(
                candidate.registry_key
            )

            match = BeefGradeMatch(
                grade=grade,
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
                confidence=(
                    self._calculate_grade_confidence(
                        normalized_text=(
                            normalized_text
                        ),
                        candidate=candidate,
                        grade=grade,
                        detected_country=(
                            detected_country
                        ),
                    )
                ),
                country_hint=detected_country,
            )

            existing = best_by_key.get(
                grade.registry_key
            )

            if (
                existing is None
                or self._grade_match_sort_key(
                    match
                )
                > self._grade_match_sort_key(
                    existing
                )
            ):
                best_by_key[
                    grade.registry_key
                ] = match

        return sorted(
            best_by_key.values(),
            key=self._grade_match_sort_key,
            reverse=True,
        )

    def list(
        self,
        *,
        country_code: str | None = None,
        premium_only: bool = False,
    ) -> list[BeefGrade]:
        grades = super().list()

        normalized_country = (
            normalize_country_code(country_code)
        )

        filtered: list[BeefGrade] = []

        for grade in grades:
            if (
                normalized_country
                and grade.country_code
                != normalized_country
            ):
                continue

            if (
                premium_only
                and not grade.premium
            ):
                continue

            filtered.append(grade)

        return sorted(
            filtered,
            key=lambda grade: (
                grade.country_code,
                (
                    grade.rank
                    if grade.rank is not None
                    else 999
                ),
                -grade.score,
                grade.canonical_grade,
            ),
        )

    def countries(self) -> list[str]:
        return sorted(
            {
                grade.country_code
                for grade in self.list()
                if grade.country_code
            }
        )

    def systems(self) -> list[str]:
        return sorted(
            {
                grade.system
                for grade in self.list()
                if grade.system
            }
        )

    def aliases(
        self,
        *,
        country_code: str | None = None,
    ) -> list[str]:
        normalized_country = (
            normalize_country_code(country_code)
        )

        values: set[str] = set()

        for candidate in self.alias_candidates():
            candidate_country = (
                normalize_country_code(
                    (candidate.metadata or {}).get(
                        "country_code"
                    )
                )
            )

            if (
                normalized_country
                and candidate_country
                != normalized_country
            ):
                continue

            values.add(candidate.alias)

        return sorted(
            values,
            key=lambda value: (
                -len(self.normalize_text(value)),
                value,
            ),
        )

    def clear_cache(self) -> None:
        """
        기존 BeefGradeRegistry API 호환 메서드.

        별칭 인덱스만 초기화하며 Loader 캐시는 유지한다.
        """

        self._clear_local_cache()

    def reload(self) -> None:
        """
        YAML Loader 캐시와 별칭 인덱스를 함께 초기화한다.
        """

        super().reload()

    @staticmethod
    def _entry_aliases(
        canonical_grade: str,
        raw_aliases: Any,
    ) -> tuple[str, ...]:
        values: list[Any] = [
            canonical_grade,
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

            normalized = normalize_grade_text(
                alias
            )

            if (
                not normalized
                or normalized in seen
            ):
                continue

            seen.add(normalized)
            result.append(alias)

        return tuple(result)

    @staticmethod
    def _calculate_grade_confidence(
        *,
        normalized_text: str,
        candidate: AliasCandidate,
        grade: BeefGrade,
        detected_country: str | None,
    ) -> float:
        confidence = 0.75

        if (
            normalized_text
            == candidate.normalized_alias
        ):
            confidence += 0.15

        if (
            detected_country
            and detected_country
            == grade.country_code
        ):
            confidence += 0.10

        return round(
            min(confidence, 1.0),
            2,
        )

    @staticmethod
    def _grade_match_sort_key(
        match: BeefGradeMatch,
    ) -> tuple[float, int, int]:
        return (
            match.confidence,
            len(match.normalized_alias),
            -match.match_start,
        )


def normalize_grade_text(
    value: Any,
) -> str:
    if value is None:
        return ""

    import re

    text = str(value).strip().lower()
    text = text.replace("＋", "+")
    text = text.replace("플러스", "+")

    return re.sub(
        r"[^0-9a-z가-힣+]+",
        "",
        text,
    )


def normalize_country_code(
    value: Any,
) -> str | None:
    if value is None:
        return None

    normalized = str(value).strip().upper()

    if not normalized:
        return None

    aliases = {
        "KOREA": "KR",
        "KOREAN": "KR",
        "대한민국": "KR",
        "한국": "KR",
        "USA": "US",
        "UNITED STATES": "US",
        "미국": "US",
        "AUSTRALIA": "AU",
        "호주": "AU",
        "JAPAN": "JP",
        "일본": "JP",
    }

    return aliases.get(
        normalized,
        normalized,
    )


def detect_country_code(
    text: Any,
) -> str | None:
    normalized_text = normalize_grade_text(
        text
    )

    if not normalized_text:
        return None

    detected: list[
        tuple[int, int, str]
    ] = []

    for country_code, aliases in (
        COUNTRY_ALIASES.items()
    ):
        for alias in aliases:
            normalized_alias = (
                normalize_grade_text(alias)
            )

            position = normalized_text.find(
                normalized_alias
            )

            if position < 0:
                continue

            detected.append(
                (
                    position,
                    -len(normalized_alias),
                    country_code,
                )
            )

    if not detected:
        return None

    detected.sort()

    return detected[0][2]


_default_beef_grade_registry = (
    BeefGradeRegistry()
)


def get_beef_grade_registry(
) -> BeefGradeRegistry:
    return _default_beef_grade_registry


def get_beef_grade(
    registry_key: str,
    *,
    required: bool = False,
) -> BeefGrade | None:
    return get_beef_grade_registry().get(
        registry_key,
        required=required,
    )


def lookup_beef_grade(
    query: str,
    *,
    country_code: str | None = None,
    required: bool = False,
) -> BeefGrade | None:
    return get_beef_grade_registry().lookup(
        query,
        country_code=country_code,
        required=required,
    )


def match_beef_grade(
    text: str,
    *,
    country_code: str | None = None,
) -> BeefGradeMatch | None:
    return get_beef_grade_registry().match(
        text,
        country_code=country_code,
    )


def list_beef_grades(
    *,
    country_code: str | None = None,
    premium_only: bool = False,
) -> list[BeefGrade]:
    return get_beef_grade_registry().list(
        country_code=country_code,
        premium_only=premium_only,
    )


__all__ = [
    "BEEF_GRADE_REGISTRY_ID",
    "COUNTRY_ALIASES",
    "BeefGrade",
    "BeefGradeMatch",
    "BeefGradeRegistry",
    "normalize_grade_text",
    "normalize_country_code",
    "detect_country_code",
    "get_beef_grade_registry",
    "get_beef_grade",
    "lookup_beef_grade",
    "match_beef_grade",
    "list_beef_grades",
]
