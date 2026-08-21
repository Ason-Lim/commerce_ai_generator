from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

from app.services.cross_border.context import (
    CrossBorderEvaluationContext,
)
from app.services.cross_border.provenance import (
    EvidenceProvenance,
)


class EvidenceFreshnessState(str, Enum):
    """
    Canonical freshness-state vocabulary.

    UNKNOWN means freshness cannot be determined from the
    available temporal evidence. It is not equivalent to stale.
    """

    FRESH = "fresh"
    STALE = "stale"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class EvidenceFreshness:
    """
    Immutable result of bounded evidence freshness evaluation.

    evidence_at records the provenance time actually used:
    effective_at when available, otherwise retrieved_at.

    age is populated only when freshness can be determined.

    This contract does not decide regulatory permission,
    landed cost, route validity, recommendation eligibility,
    or transaction executability.
    """

    state: EvidenceFreshnessState
    evidence_at: str | None = None
    age: timedelta | None = None


def _parse_aware_datetime(
    name: str,
    value: str,
) -> datetime:
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(
            f"{name} must be a valid ISO-8601 datetime"
        ) from exc

    if (
        parsed.tzinfo is None
        or parsed.utcoffset() is None
    ):
        raise ValueError(
            f"{name} must include timezone information"
        )

    return parsed


def _require_non_negative_max_age(
    max_age: timedelta,
) -> timedelta:
    if max_age < timedelta(0):
        raise ValueError(
            "max_age must not be negative"
        )
    return max_age


def evaluate_evidence_freshness(
    provenance: EvidenceProvenance,
    context: CrossBorderEvaluationContext,
    max_age: timedelta,
) -> EvidenceFreshness:
    """
    Evaluate provenance freshness at the context evaluation time.

    Time selection:
        effective_at
        -> retrieved_at fallback
        -> UNKNOWN when neither exists

    Evaluation requires context.evaluated_at. Missing evaluation
    time produces UNKNOWN because age cannot be established.

    A provenance time later than evaluated_at produces UNKNOWN.
    Evidence exactly max_age old remains FRESH.
    Evidence older than max_age is STALE.

    No transaction execution is performed or authorized here.
    """

    _require_non_negative_max_age(max_age)

    evidence_at = (
        provenance.effective_at
        or provenance.retrieved_at
    )

    if evidence_at is None:
        return EvidenceFreshness(
            state=EvidenceFreshnessState.UNKNOWN,
        )

    if context.evaluated_at is None:
        return EvidenceFreshness(
            state=EvidenceFreshnessState.UNKNOWN,
            evidence_at=evidence_at,
        )

    evidence_time = _parse_aware_datetime(
        "evidence_at",
        evidence_at,
    )
    evaluation_time = _parse_aware_datetime(
        "evaluated_at",
        context.evaluated_at,
    )

    if evidence_time > evaluation_time:
        return EvidenceFreshness(
            state=EvidenceFreshnessState.UNKNOWN,
            evidence_at=evidence_at,
        )

    age = evaluation_time - evidence_time

    if age <= max_age:
        state = EvidenceFreshnessState.FRESH
    else:
        state = EvidenceFreshnessState.STALE

    return EvidenceFreshness(
        state=state,
        evidence_at=evidence_at,
        age=age,
    )
