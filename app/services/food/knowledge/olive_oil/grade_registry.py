from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from app.services.food.knowledge.common.base_model import (
    RegistryMatch,
)
from app.services.food.knowledge.common.base_registry import (
    optional_string,
)
from app.services.food.knowledge.olive_oil._registry_support import (
    OliveOilAliasRegistry,
    OliveOilRegistryEntry,
)


OLIVE_OIL_GRADE_REGISTRY_ID = "olive_oil.grades"


@dataclass(
    frozen=True,
    kw_only=True,
)
class OliveOilGrade(OliveOilRegistryEntry):
    """Canonical commercial Olive Oil grade."""

    grade_class: str | None = None
    virgin: bool = False
    refined: bool = False
    pomace: bool = False


@dataclass(
    frozen=True,
    kw_only=True,
)
class OliveOilGradeMatch(
    RegistryMatch[OliveOilGrade]
):
    @property
    def olive_oil_grade(self) -> OliveOilGrade:
        return self.entry


class OliveOilGradeRegistry(
    OliveOilAliasRegistry[OliveOilGrade]
):
    registry_id = OLIVE_OIL_GRADE_REGISTRY_ID
    entry_class = OliveOilGrade

    def build_entry(
        self,
        registry_key: str,
        raw_entry: Mapping[str, Any],
    ) -> OliveOilGrade:
        known_fields = {
            "canonical_name",
            "aliases",
            "score",
            "premium",
            "description",
            "grade_class",
            "virgin",
            "refined",
            "pomace",
        }

        return OliveOilGrade(
            **self.common_fields(
                registry_key=registry_key,
                raw_entry=raw_entry,
                known_fields=known_fields,
            ),
            grade_class=optional_string(
                raw_entry.get("grade_class")
            ),
            virgin=bool(
                raw_entry.get("virgin", False)
            ),
            refined=bool(
                raw_entry.get("refined", False)
            ),
            pomace=bool(
                raw_entry.get("pomace", False)
            ),
        )

    def match(
        self,
        text: str,
    ) -> OliveOilGradeMatch | None:
        raw_match = super().match(text)

        if raw_match is None:
            return None

        return self.convert_match(
            raw_match,
            OliveOilGradeMatch,
        )  # type: ignore[return-value]


__all__ = [
    "OLIVE_OIL_GRADE_REGISTRY_ID",
    "OliveOilGrade",
    "OliveOilGradeMatch",
    "OliveOilGradeRegistry",
]
