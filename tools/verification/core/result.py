from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterable, Mapping

from tools.verification.core.evidence import (
    VerificationEvidence,
)


class VerificationStatus(str, Enum):
    PASS = "PASS"
    WARNING = "WARNING"
    FAIL = "FAIL"
    ERROR = "ERROR"
    SKIPPED = "SKIPPED"


_STATUS_PRIORITY: dict[VerificationStatus, int] = {
    VerificationStatus.PASS: 0,
    VerificationStatus.SKIPPED: 1,
    VerificationStatus.WARNING: 2,
    VerificationStatus.FAIL: 3,
    VerificationStatus.ERROR: 4,
}


@dataclass(frozen=True, kw_only=True)
class VerificationCheck:
    check_id: str
    title: str
    status: VerificationStatus
    summary: str
    details: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        check_id = self.check_id.strip()
        title = self.title.strip()
        summary = self.summary.strip()

        if not check_id:
            raise ValueError(
                "check_id must not be empty"
            )

        if not title:
            raise ValueError(
                "title must not be empty"
            )

        if not summary:
            raise ValueError(
                "summary must not be empty"
            )

        object.__setattr__(
            self,
            "check_id",
            check_id,
        )
        object.__setattr__(
            self,
            "title",
            title,
        )
        object.__setattr__(
            self,
            "summary",
            summary,
        )
        object.__setattr__(
            self,
            "details",
            tuple(self.details),
        )
        object.__setattr__(
            self,
            "evidence_ids",
            tuple(self.evidence_ids),
        )
        object.__setattr__(
            self,
            "metadata",
            dict(self.metadata),
        )

    @property
    def passed(self) -> bool:
        return self.status is VerificationStatus.PASS

    def to_dict(self) -> dict[str, Any]:
        return {
            "check_id": self.check_id,
            "title": self.title,
            "status": self.status.value,
            "summary": self.summary,
            "details": list(self.details),
            "evidence_ids": list(
                self.evidence_ids
            ),
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, kw_only=True)
class VerificationResult:
    verifier_id: str
    verifier_name: str
    target: str
    status: VerificationStatus
    summary: str
    checks: tuple[VerificationCheck, ...] = ()
    evidence: tuple[
        VerificationEvidence,
        ...
    ] = ()
    warnings: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        verifier_id = self.verifier_id.strip()
        verifier_name = self.verifier_name.strip()
        target = self.target.strip()
        summary = self.summary.strip()

        if not verifier_id:
            raise ValueError(
                "verifier_id must not be empty"
            )

        if not verifier_name:
            raise ValueError(
                "verifier_name must not be empty"
            )

        if not target:
            raise ValueError(
                "target must not be empty"
            )

        if not summary:
            raise ValueError(
                "summary must not be empty"
            )

        object.__setattr__(
            self,
            "verifier_id",
            verifier_id,
        )
        object.__setattr__(
            self,
            "verifier_name",
            verifier_name,
        )
        object.__setattr__(
            self,
            "target",
            target,
        )
        object.__setattr__(
            self,
            "summary",
            summary,
        )
        object.__setattr__(
            self,
            "checks",
            tuple(self.checks),
        )
        object.__setattr__(
            self,
            "evidence",
            tuple(self.evidence),
        )
        object.__setattr__(
            self,
            "warnings",
            tuple(self.warnings),
        )
        object.__setattr__(
            self,
            "errors",
            tuple(self.errors),
        )
        object.__setattr__(
            self,
            "metadata",
            dict(self.metadata),
        )

    @classmethod
    def from_checks(
        cls,
        *,
        verifier_id: str,
        verifier_name: str,
        target: str,
        summary: str,
        checks: Iterable[VerificationCheck],
        evidence: Iterable[
            VerificationEvidence
        ] = (),
        warnings: Iterable[str] = (),
        errors: Iterable[str] = (),
        metadata: Mapping[str, Any] | None = None,
    ) -> VerificationResult:
        check_tuple = tuple(checks)

        status = aggregate_status(
            check.status
            for check in check_tuple
        )

        error_tuple = tuple(errors)
        warning_tuple = tuple(warnings)

        if error_tuple:
            status = VerificationStatus.ERROR
        elif (
            warning_tuple
            and _STATUS_PRIORITY[status]
            < _STATUS_PRIORITY[
                VerificationStatus.WARNING
            ]
        ):
            status = VerificationStatus.WARNING

        return cls(
            verifier_id=verifier_id,
            verifier_name=verifier_name,
            target=target,
            status=status,
            summary=summary,
            checks=check_tuple,
            evidence=tuple(evidence),
            warnings=warning_tuple,
            errors=error_tuple,
            metadata=dict(metadata or {}),
        )

    @property
    def passed(self) -> bool:
        return self.status is VerificationStatus.PASS

    @property
    def successful(self) -> bool:
        return self.status in {
            VerificationStatus.PASS,
            VerificationStatus.WARNING,
        }

    @property
    def failed_checks(
        self,
    ) -> tuple[VerificationCheck, ...]:
        return tuple(
            check
            for check in self.checks
            if check.status
            in {
                VerificationStatus.FAIL,
                VerificationStatus.ERROR,
            }
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "verifier_id": self.verifier_id,
            "verifier_name": (
                self.verifier_name
            ),
            "target": self.target,
            "status": self.status.value,
            "summary": self.summary,
            "checks": [
                check.to_dict()
                for check in self.checks
            ],
            "evidence": [
                item.to_dict()
                for item in self.evidence
            ],
            "warnings": list(self.warnings),
            "errors": list(self.errors),
            "metadata": dict(self.metadata),
        }


def aggregate_status(
    statuses: Iterable[VerificationStatus],
) -> VerificationStatus:
    status_list = list(statuses)

    if not status_list:
        return VerificationStatus.SKIPPED

    return max(
        status_list,
        key=lambda status: (
            _STATUS_PRIORITY[status]
        ),
    )


__all__ = [
    "VerificationStatus",
    "VerificationCheck",
    "VerificationResult",
    "aggregate_status",
]
