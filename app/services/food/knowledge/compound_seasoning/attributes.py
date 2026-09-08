"""Immutable normalized attributes for Compound Seasoning evidence."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class AttributeValidationError(ValueError):
    """Raised when an attribute would violate the fail-closed contract."""


class EvidenceStatus(Enum):
    VERIFIED = "VERIFIED"
    PARTIALLY_VERIFIED = "PARTIALLY_VERIFIED"
    REPORTED = "REPORTED"
    MISSING = "MISSING"
    CONFLICTING = "CONFLICTING"


@dataclass(frozen=True)
class AttributeEvidence:
    value: Optional[str]
    status: EvidenceStatus
    unresolved: bool


@dataclass(frozen=True)
class CompoundSeasoningAttributes:
    form: AttributeEvidence
    composition: AttributeEvidence
    usage: AttributeEvidence


def _status(value: EvidenceStatus | str) -> EvidenceStatus:
    if isinstance(value, EvidenceStatus):
        return value
    try:
        return EvidenceStatus(value)
    except (TypeError, ValueError) as exc:
        raise AttributeValidationError(f"unsupported evidence status: {value!r}") from exc


def _normalize(value: object) -> Optional[str]:
    if value is None:
        return None
    if not isinstance(value, str):
        raise AttributeValidationError("evidence value must be a string or None")
    normalized = " ".join(value.casefold().strip().split())
    return normalized or None


def normalize_evidence(
    value: object, status: EvidenceStatus | str
) -> AttributeEvidence:
    normalized_status = _status(status)
    normalized_value = _normalize(value)
    if normalized_status is EvidenceStatus.VERIFIED and normalized_value is None:
        raise AttributeValidationError("verified evidence must have a value")
    return AttributeEvidence(
        value=normalized_value,
        status=normalized_status,
        unresolved=normalized_status is not EvidenceStatus.VERIFIED,
    )


def _coerce(value: AttributeEvidence | tuple[object, EvidenceStatus | str]) -> AttributeEvidence:
    if isinstance(value, AttributeEvidence):
        return value
    if not isinstance(value, tuple) or len(value) != 2:
        raise AttributeValidationError("attribute input must be evidence or a value/status pair")
    return normalize_evidence(value[0], value[1])


def project_attributes(
    *,
    form: AttributeEvidence | tuple[object, EvidenceStatus | str],
    composition: AttributeEvidence | tuple[object, EvidenceStatus | str],
    usage: AttributeEvidence | tuple[object, EvidenceStatus | str],
) -> CompoundSeasoningAttributes:
    return CompoundSeasoningAttributes(
        form=_coerce(form),
        composition=_coerce(composition),
        usage=_coerce(usage),
    )
