from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping


def _normalize_optional(
    value: str | None,
) -> str | None:
    if value is None:
        return None

    normalized = value.strip()

    if not normalized:
        return None

    return normalized


def _require_non_empty(
    name: str,
    value: str,
) -> str:
    normalized = value.strip()

    if not normalized:
        raise ValueError(
            f"{name} must not be empty"
        )

    return normalized


@dataclass(frozen=True)
class EvidenceProvenance:
    """
    Immutable provenance metadata for cross-border evidence.

    Provenance identifies where evidence came from and which
    source record or observation it can be traced back to.

    This contract records time evidence but does not decide
    freshness or staleness.

    It does not perform network access or transaction execution.
    """

    source_id: str
    source_type: str
    record_id: str | None = None
    source_reference: str | None = None
    retrieved_at: str | None = None
    effective_at: str | None = None
    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "source_id",
            _require_non_empty(
                "source_id",
                self.source_id,
            ),
        )

        object.__setattr__(
            self,
            "source_type",
            _require_non_empty(
                "source_type",
                self.source_type,
            ),
        )

        object.__setattr__(
            self,
            "record_id",
            _normalize_optional(
                self.record_id
            ),
        )

        object.__setattr__(
            self,
            "source_reference",
            _normalize_optional(
                self.source_reference
            ),
        )

        object.__setattr__(
            self,
            "retrieved_at",
            _normalize_optional(
                self.retrieved_at
            ),
        )

        object.__setattr__(
            self,
            "effective_at",
            _normalize_optional(
                self.effective_at
            ),
        )

        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(
                dict(self.metadata)
            ),
        )
