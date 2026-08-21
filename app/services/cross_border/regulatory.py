from __future__ import annotations

from dataclasses import dataclass

from app.services.cross_border.context import (
    CrossBorderEvaluationContext,
)
from app.services.cross_border.freshness import (
    EvidenceFreshness,
)
from app.services.cross_border.models import (
    CrossBorderEvidence,
    EvidenceState,
)
from app.services.cross_border.provenance import (
    EvidenceProvenance,
)


def _normalize_optional(
    value: str | None,
) -> str | None:
    if value is None:
        return None

    normalized = value.strip()

    if not normalized:
        return None

    return normalized


@dataclass(frozen=True)
class RegulatoryEvidence:
    """
    Immutable bounded regulatory evidence.

    This contract preserves externally supplied regulatory
    observations in the Cross-Border evaluation context.

    UNKNOWN evidence must not manufacture a regulatory
    observation.

    This contract does not determine legal permission,
    calculate tariffs or duties, classify HS codes, retrieve
    live regulatory data, file customs declarations, or
    authorize transaction execution.
    """

    evidence: CrossBorderEvidence
    provenance: EvidenceProvenance
    context: CrossBorderEvaluationContext

    observation: str | None = None
    jurisdiction: str | None = None
    regulatory_reference: str | None = None
    freshness: EvidenceFreshness | None = None

    def __post_init__(self) -> None:
        observation = _normalize_optional(
            self.observation
        )
        jurisdiction = _normalize_optional(
            self.jurisdiction
        )
        regulatory_reference = _normalize_optional(
            self.regulatory_reference
        )

        if (
            self.evidence.state
            is EvidenceState.UNKNOWN
        ):
            if observation is not None:
                raise ValueError(
                    "UNKNOWN regulatory evidence must not "
                    "carry an observation"
                )
        elif observation is None:
            raise ValueError(
                "evidence-bearing regulatory state "
                "requires an observation"
            )

        object.__setattr__(
            self,
            "observation",
            observation,
        )
        object.__setattr__(
            self,
            "jurisdiction",
            jurisdiction,
        )
        object.__setattr__(
            self,
            "regulatory_reference",
            regulatory_reference,
        )

    @property
    def has_observation(self) -> bool:
        return self.observation is not None
