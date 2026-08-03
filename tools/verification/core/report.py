from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping

from tools.verification.core.result import (
    VerificationResult,
    VerificationStatus,
    aggregate_status,
)


@dataclass(frozen=True, kw_only=True)
class VerificationReport:
    report_id: str
    title: str
    target: str
    status: VerificationStatus
    results: tuple[VerificationResult, ...]
    generated_at: str
    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )

    @classmethod
    def from_results(
        cls,
        *,
        report_id: str,
        title: str,
        target: str,
        results: Iterable[
            VerificationResult
        ],
        metadata: Mapping[str, Any] | None = None,
    ) -> VerificationReport:
        result_tuple = tuple(results)

        return cls(
            report_id=report_id,
            title=title,
            target=target,
            status=aggregate_status(
                result.status
                for result in result_tuple
            ),
            results=result_tuple,
            generated_at=(
                datetime.now(timezone.utc)
                .isoformat()
            ),
            metadata=dict(metadata or {}),
        )

    @property
    def counts(
        self,
    ) -> dict[str, int]:
        counts = {
            status.value: 0
            for status in VerificationStatus
        }

        for result in self.results:
            counts[result.status.value] += 1

        return counts

    @property
    def successful(self) -> bool:
        return self.status in {
            VerificationStatus.PASS,
            VerificationStatus.WARNING,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "report_id": self.report_id,
            "title": self.title,
            "target": self.target,
            "status": self.status.value,
            "generated_at": self.generated_at,
            "counts": self.counts,
            "results": [
                result.to_dict()
                for result in self.results
            ],
            "metadata": dict(self.metadata),
        }


__all__ = [
    "VerificationReport",
]
