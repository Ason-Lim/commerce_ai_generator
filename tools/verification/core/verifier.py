from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

from tools.verification.core.result import (
    VerificationResult,
)


@dataclass(frozen=True, kw_only=True)
class VerificationRequest:
    target: str
    domain_id: str | None = None
    architecture_id: str | None = None
    evidence_directory: str | None = None
    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        target = self.target.strip()

        if not target:
            raise ValueError(
                "target must not be empty"
            )

        object.__setattr__(
            self,
            "target",
            target,
        )
        object.__setattr__(
            self,
            "metadata",
            dict(self.metadata),
        )

    @property
    def target_path(self) -> Path:
        return Path(self.target)

    @property
    def evidence_path(self) -> Path | None:
        if self.evidence_directory is None:
            return None

        return Path(self.evidence_directory)

    def to_dict(self) -> dict[str, Any]:
        return {
            "target": self.target,
            "domain_id": self.domain_id,
            "architecture_id": (
                self.architecture_id
            ),
            "evidence_directory": (
                self.evidence_directory
            ),
            "metadata": dict(self.metadata),
        }


class BaseVerifier(ABC):
    verifier_id: str
    verifier_name: str
    version: str = "1.0.0"

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()

        if cls is BaseVerifier:
            return

        verifier_id = getattr(
            cls,
            "verifier_id",
            "",
        )
        verifier_name = getattr(
            cls,
            "verifier_name",
            "",
        )

        if not str(verifier_id).strip():
            raise TypeError(
                "Verifier subclass must define "
                "verifier_id"
            )

        if not str(verifier_name).strip():
            raise TypeError(
                "Verifier subclass must define "
                "verifier_name"
            )

    @abstractmethod
    def verify(
        self,
        request: VerificationRequest,
    ) -> VerificationResult:
        raise NotImplementedError


__all__ = [
    "VerificationRequest",
    "BaseVerifier",
]
