from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Mapping


class EvidenceKind(str, Enum):
    REPOSITORY = "repository"
    SOURCE = "source"
    TEST = "test"
    REGRESSION = "regression"
    COMPILATION = "compilation"
    BOUNDARY = "boundary"
    CONTRACT = "contract"
    REGISTRY = "registry"
    INTEGRATION = "integration"
    GIT = "git"
    REPORT = "report"
    OTHER = "other"


@dataclass(frozen=True, kw_only=True)
class VerificationEvidence:
    evidence_id: str
    kind: EvidenceKind
    title: str
    location: str | None = None
    summary: str | None = None
    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        evidence_id = self.evidence_id.strip()
        title = self.title.strip()

        if not evidence_id:
            raise ValueError(
                "evidence_id must not be empty"
            )

        if not title:
            raise ValueError(
                "title must not be empty"
            )

        object.__setattr__(
            self,
            "evidence_id",
            evidence_id,
        )
        object.__setattr__(
            self,
            "title",
            title,
        )
        object.__setattr__(
            self,
            "metadata",
            dict(self.metadata),
        )

    @property
    def path(self) -> Path | None:
        if self.location is None:
            return None

        return Path(self.location)

    def to_dict(self) -> dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "kind": self.kind.value,
            "title": self.title,
            "location": self.location,
            "summary": self.summary,
            "metadata": dict(self.metadata),
        }


__all__ = [
    "EvidenceKind",
    "VerificationEvidence",
]
