from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping


class EvidenceState(str, Enum):
    """
    Canonical Cross-Border evidence-state vocabulary.

    UNKNOWN is an explicit evidence state. It must not be interpreted
    as numeric zero, False, an empty string, or verified absence.
    """

    VERIFIED = "verified"
    OBSERVED = "observed"
    ESTIMATED = "estimated"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class CrossBorderEvidence:
    """
    Immutable canonical evidence observation.

    The evidence state is independent from the observed value.
    A value of 0, 0.0, False, or "" may therefore remain a real
    observation when the evidence state says that evidence exists.

    UNKNOWN expresses unavailable or unresolved evidence and does
    not manufacture a replacement value.

    Freshness thresholds are intentionally not defined here.
    Transaction execution is outside this contract.
    """

    state: EvidenceState
    value: Any = None
    source: str | None = None
    observed_at: str | None = None
    provenance: Mapping[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "provenance",
            MappingProxyType(
                dict(self.provenance)
            ),
        )
