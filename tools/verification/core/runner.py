from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from tools.verification.core.result import (
    VerificationCheck,
    VerificationResult,
    VerificationStatus,
)
from tools.verification.core.verifier import (
    BaseVerifier,
    VerificationRequest,
)


@dataclass(frozen=True, kw_only=True)
class VerificationRun:
    request: VerificationRequest
    results: tuple[VerificationResult, ...]

    @property
    def successful(self) -> bool:
        return all(
            result.successful
            for result in self.results
        )


class VerificationRunner:
    def __init__(
        self,
        *,
        capture_exceptions: bool = True,
        fail_fast: bool = False,
    ) -> None:
        self.capture_exceptions = (
            capture_exceptions
        )
        self.fail_fast = fail_fast

    def run(
        self,
        verifier: BaseVerifier,
        request: VerificationRequest,
    ) -> VerificationResult:
        try:
            result = verifier.verify(request)
        except Exception as exc:
            if not self.capture_exceptions:
                raise

            return self._exception_result(
                verifier=verifier,
                request=request,
                exc=exc,
            )

        if not isinstance(
            result,
            VerificationResult,
        ):
            raise TypeError(
                "Verifier.verify() must return "
                "VerificationResult"
            )

        return result

    def run_many(
        self,
        verifiers: Iterable[BaseVerifier],
        request: VerificationRequest,
    ) -> VerificationRun:
        results: list[VerificationResult] = []

        for verifier in verifiers:
            result = self.run(
                verifier,
                request,
            )
            results.append(result)

            if (
                self.fail_fast
                and result.status
                in {
                    VerificationStatus.FAIL,
                    VerificationStatus.ERROR,
                }
            ):
                break

        return VerificationRun(
            request=request,
            results=tuple(results),
        )

    @staticmethod
    def _exception_result(
        *,
        verifier: BaseVerifier,
        request: VerificationRequest,
        exc: Exception,
    ) -> VerificationResult:
        message = (
            f"{exc.__class__.__name__}: {exc}"
        )

        return VerificationResult(
            verifier_id=verifier.verifier_id,
            verifier_name=(
                verifier.verifier_name
            ),
            target=request.target,
            status=VerificationStatus.ERROR,
            summary=(
                "Verifier execution raised "
                "an exception."
            ),
            checks=(
                VerificationCheck(
                    check_id=(
                        f"{verifier.verifier_id}"
                        ".execution"
                    ),
                    title="Verifier execution",
                    status=(
                        VerificationStatus.ERROR
                    ),
                    summary=message,
                ),
            ),
            errors=(message,),
            metadata={
                "verifier_version": (
                    verifier.version
                ),
            },
        )


__all__ = [
    "VerificationRun",
    "VerificationRunner",
]
