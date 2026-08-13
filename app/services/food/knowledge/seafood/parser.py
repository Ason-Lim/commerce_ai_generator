from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.services.food.knowledge.common import (
    calculate_field_confidence,
    detect_keywords,
    extract_product_name as extract_common_product_name,
    extract_weight_grams as extract_common_weight_grams,
    first_non_empty,
    normalize_text,
)
from app.services.food.knowledge.seafood.parser_models import (
    SeafoodParseResult,
)
from app.services.food.knowledge.seafood.registries import (
    PROCESSING_STATE_ALIASES,
    SEAFOOD_KEYWORDS,
    SEAFOOD_SPECIES_REGISTRY,
    WILD_FARMED_ALIASES,
)


_SPECIES_KEYS = (
    "species",
    "seafood_species",
    "fish_species",
    "product_species",
)

_GROUP_KEYS = (
    "seafood_group",
    "seafood_type",
    "product_group",
)

_ORIGIN_KEYS = (
    "origin",
    "country_of_origin",
    "origin_name",
    "production_area",
    "region",
)

_GRADE_KEYS = (
    "grade",
    "product_grade",
    "quality_grade",
)

_WILD_FARMED_KEYS = (
    "wild_farmed_status",
    "production_environment",
    "production_method",
)

_PROCESSING_STATE_KEYS = (
    "processing_state",
    "freshness",
    "storage_state",
    "product_state",
)


class SeafoodParser:
    """
    Seafood 도메인의 canonical parser.

    책임:
    - Seafood 식별 정보 추출
    - Registry 기반 species 정규화
    - 구조화 데이터 우선 처리
    - Parse confidence 계산

    담당하지 않는 책임:
    - Attribute 구성
    - 점수 계산
    - Rule 평가
    - Provider orchestration
    - Registry 변경
    """

    def parse(
        self,
        product: Mapping[str, Any],
    ) -> SeafoodParseResult:
        if not isinstance(product, Mapping):
            raise TypeError(
                "product must be a Mapping"
            )

        product_name = extract_product_name(product)
        normalized_name = normalize_text(product_name)

        raw_species = _normalize_optional_text(
            first_non_empty(
                product,
                _SPECIES_KEYS,
            )
        )

        species = (
            normalize_species(raw_species)
            if raw_species
            else detect_species(normalized_name)
        )

        raw_group = _normalize_optional_text(
            first_non_empty(
                product,
                _GROUP_KEYS,
            )
        )

        seafood_group = (
            normalize_seafood_group(raw_group)
            if raw_group
            else group_for_species(species)
        )

        origin = _normalize_optional_text(
            first_non_empty(
                product,
                _ORIGIN_KEYS,
            )
        )

        grade = _normalize_optional_text(
            first_non_empty(
                product,
                _GRADE_KEYS,
            )
        )

        raw_wild_farmed = _normalize_optional_text(
            first_non_empty(
                product,
                _WILD_FARMED_KEYS,
            )
        )

        wild_farmed_status = (
            normalize_alias_value(
                raw_wild_farmed,
                WILD_FARMED_ALIASES,
            )
            if raw_wild_farmed
            else detect_alias_value(
                normalized_name,
                WILD_FARMED_ALIASES,
            )
        )

        raw_processing_state = _normalize_optional_text(
            first_non_empty(
                product,
                _PROCESSING_STATE_KEYS,
            )
        )

        processing_state = (
            normalize_alias_value(
                raw_processing_state,
                PROCESSING_STATE_ALIASES,
            )
            if raw_processing_state
            else detect_alias_value(
                normalized_name,
                PROCESSING_STATE_ALIASES,
            )
        )

        weight_grams = extract_weight_grams(product)

        detected_keywords = detect_seafood_keywords(
            product_name
        )

        confidence = calculate_parse_confidence(
            product_name=product_name,
            species=species,
            seafood_group=seafood_group,
            origin=origin,
            wild_farmed_status=wild_farmed_status,
            processing_state=processing_state,
            weight_grams=weight_grams,
        )

        warnings: list[str] = []

        if (
            detected_keywords
            and species is None
        ):
            warnings.append(
                "Seafood 신호는 있으나 species가 "
                "확정되지 않았습니다."
            )

        return SeafoodParseResult(
            original_text=product_name,
            normalized_text=normalized_name,
            confidence=confidence,
            seafood_group=seafood_group,
            species=species,
            origin=origin,
            grade=grade,
            wild_farmed_status=wild_farmed_status,
            processing_state=processing_state,
            weight_grams=weight_grams,
            detected_keywords=detected_keywords,
            warnings=warnings,
        )


_DEFAULT_SEAFOOD_PARSER = SeafoodParser()


def parse_seafood(
    product: Mapping[str, Any],
) -> SeafoodParseResult:
    return _DEFAULT_SEAFOOD_PARSER.parse(product)


def parse_seafood_product(
    product: Mapping[str, Any],
) -> dict[str, Any]:
    parsed = parse_seafood(product)

    return {
        "product_name": parsed.original_text,
        "seafood_group": parsed.seafood_group,
        "species": parsed.species,
        "origin": parsed.origin,
        "grade": parsed.grade,
        "wild_farmed_status": (
            parsed.wild_farmed_status
        ),
        "processing_state": (
            parsed.processing_state
        ),
        "weight_grams": parsed.weight_grams,
        "detected_keywords": list(
            parsed.detected_keywords
        ),
        "warnings": list(parsed.warnings),
        "confidence": parsed.confidence,
    }


def extract_product_name(
    product: Mapping[str, Any],
) -> str:
    return extract_common_product_name(product)


def extract_weight_grams(
    value: Mapping[str, Any] | Any,
) -> float | None:
    if isinstance(value, Mapping):
        return extract_common_weight_grams(
            value,
            fallback_to_product_name=True,
        )

    return extract_common_weight_grams(
        {"weight": value},
        fallback_to_product_name=False,
    )


def detect_species(
    text: str,
) -> str | None:
    normalized_text = normalize_text(text)

    candidates: list[
        tuple[int, str]
    ] = []

    for canonical_id, metadata in (
        SEAFOOD_SPECIES_REGISTRY.items()
    ):
        for alias in metadata["aliases"]:
            normalized_alias = normalize_text(
                str(alias)
            )

            if (
                normalized_alias
                and normalized_alias
                in normalized_text
            ):
                candidates.append(
                    (
                        len(normalized_alias),
                        canonical_id,
                    )
                )

    if not candidates:
        return None

    candidates.sort(reverse=True)

    return candidates[0][1]


def normalize_species(
    value: str | None,
) -> str | None:
    if not value:
        return None

    normalized_value = normalize_text(value)

    if normalized_value in SEAFOOD_SPECIES_REGISTRY:
        return normalized_value

    for canonical_id, metadata in (
        SEAFOOD_SPECIES_REGISTRY.items()
    ):
        aliases = {
            normalize_text(str(alias))
            for alias in metadata["aliases"]
        }

        if normalized_value in aliases:
            return canonical_id

    # 구조화된 명시값은 추측하지 않고
    # 원문 정규화 값으로 보존한다.
    return normalized_value or None


def group_for_species(
    species: str | None,
) -> str | None:
    if not species:
        return None

    metadata = SEAFOOD_SPECIES_REGISTRY.get(
        species
    )

    if metadata is None:
        return None

    return str(metadata["group"])


def normalize_seafood_group(
    value: str | None,
) -> str | None:
    if not value:
        return None

    normalized = normalize_text(value)

    mappings = {
        "fish": "fish",
        "어류": "fish",
        "crustacean": "crustacean",
        "갑각류": "crustacean",
        "mollusk": "mollusk",
        "연체류": "mollusk",
        "cephalopod": "cephalopod",
        "두족류": "cephalopod",
        "shellfish": "shellfish",
        "패류": "shellfish",
    }

    return mappings.get(
        normalized,
        normalized or None,
    )


def normalize_alias_value(
    value: str | None,
    registry: Mapping[
        str,
        tuple[str, ...],
    ],
) -> str | None:
    if not value:
        return None

    normalized_value = normalize_text(value)

    if normalized_value in registry:
        return normalized_value

    for canonical_id, aliases in registry.items():
        normalized_aliases = {
            normalize_text(alias)
            for alias in aliases
        }

        if normalized_value in normalized_aliases:
            return canonical_id

    return normalized_value or None


def detect_alias_value(
    text: str,
    registry: Mapping[
        str,
        tuple[str, ...],
    ],
) -> str | None:
    normalized_text = normalize_text(text)

    candidates: list[
        tuple[int, str]
    ] = []

    for canonical_id, aliases in registry.items():
        for alias in aliases:
            normalized_alias = normalize_text(alias)

            if (
                normalized_alias
                and normalized_alias
                in normalized_text
            ):
                candidates.append(
                    (
                        len(normalized_alias),
                        canonical_id,
                    )
                )

    if not candidates:
        return None

    candidates.sort(reverse=True)

    return candidates[0][1]


def detect_seafood_keywords(
    product_name: str,
) -> list[str]:
    return detect_keywords(
        product_name,
        SEAFOOD_KEYWORDS,
        case_sensitive=False,
    )


def calculate_parse_confidence(
    *,
    product_name: Any,
    species: Any,
    seafood_group: Any,
    origin: Any,
    wild_farmed_status: Any,
    processing_state: Any,
    weight_grams: Any,
) -> float:
    return calculate_field_confidence(
        {
            "product_name": product_name,
            "species": species,
            "seafood_group": seafood_group,
            "origin": origin,
            "wild_farmed_status": (
                wild_farmed_status
            ),
            "processing_state": processing_state,
            "weight_grams": weight_grams,
        },
        weights={
            "product_name": 0.20,
            "species": 0.30,
            "seafood_group": 0.15,
            "origin": 0.10,
            "wild_farmed_status": 0.10,
            "processing_state": 0.10,
            "weight_grams": 0.05,
        },
    )


def _normalize_optional_text(
    value: Any,
) -> str | None:
    if value is None:
        return None

    normalized = normalize_text(
        str(value)
    )

    return normalized or None


__all__ = [
    "SeafoodParser",
    "parse_seafood",
    "parse_seafood_product",
    "extract_product_name",
    "extract_weight_grams",
    "detect_species",
    "normalize_species",
    "group_for_species",
    "normalize_seafood_group",
    "detect_seafood_keywords",
    "calculate_parse_confidence",
]
