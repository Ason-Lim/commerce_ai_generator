from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from tools.verification.core import (
    BaseVerifier,
    EvidenceKind,
    VerificationCheck,
    VerificationEvidence,
    VerificationReport,
    VerificationRequest,
    VerificationResult,
    VerificationRunner,
    VerificationStatus,
    aggregate_status,
)


class PassingVerifier(BaseVerifier):
    verifier_id = "test.passing"
    verifier_name = "Passing Verifier"

    def verify(
        self,
        request: VerificationRequest,
    ) -> VerificationResult:
        evidence = VerificationEvidence(
            evidence_id="test-evidence",
            kind=EvidenceKind.TEST,
            title="Test evidence",
            location="tests/example.txt",
        )

        check = VerificationCheck(
            check_id="test.pass",
            title="Passing check",
            status=VerificationStatus.PASS,
            summary="The check passed.",
            evidence_ids=(
                evidence.evidence_id,
            ),
        )

        return VerificationResult.from_checks(
            verifier_id=self.verifier_id,
            verifier_name=self.verifier_name,
            target=request.target,
            summary="Verification passed.",
            checks=(check,),
            evidence=(evidence,),
        )


class FailingVerifier(BaseVerifier):
    verifier_id = "test.failing"
    verifier_name = "Failing Verifier"

    def verify(
        self,
        request: VerificationRequest,
    ) -> VerificationResult:
        return VerificationResult.from_checks(
            verifier_id=self.verifier_id,
            verifier_name=self.verifier_name,
            target=request.target,
            summary="Verification failed.",
            checks=(
                VerificationCheck(
                    check_id="test.fail",
                    title="Failing check",
                    status=(
                        VerificationStatus.FAIL
                    ),
                    summary="The check failed.",
                ),
            ),
        )


class ErrorVerifier(BaseVerifier):
    verifier_id = "test.error"
    verifier_name = "Error Verifier"

    def verify(
        self,
        request: VerificationRequest,
    ) -> VerificationResult:
        raise RuntimeError("verification exploded")


def test_verification_request() -> None:
    request = VerificationRequest(
        target=" app/example ",
        domain_id="cheese",
        architecture_id="MA-2026-012",
        metadata={
            "phase": "10.1",
        },
    )

    assert request.target == "app/example"
    assert request.target_path.as_posix() == (
        "app/example"
    )
    assert request.metadata == {
        "phase": "10.1",
    }


def test_request_rejects_empty_target() -> None:
    with pytest.raises(
        ValueError,
        match="target must not be empty",
    ):
        VerificationRequest(target=" ")


def test_evidence_serialization() -> None:
    evidence = VerificationEvidence(
        evidence_id="evidence-1",
        kind=EvidenceKind.COMPILATION,
        title="Compilation evidence",
        location="evidence/compile.txt",
        metadata={"passed": True},
    )

    payload = evidence.to_dict()

    assert payload["kind"] == "compilation"
    assert payload["metadata"]["passed"] is True
    assert evidence.path is not None


def test_evidence_is_frozen() -> None:
    evidence = VerificationEvidence(
        evidence_id="evidence-1",
        kind=EvidenceKind.TEST,
        title="Evidence",
    )

    with pytest.raises(FrozenInstanceError):
        evidence.title = "Changed"  # type: ignore[misc]


def test_check_serialization() -> None:
    check = VerificationCheck(
        check_id="check-1",
        title="Check",
        status=VerificationStatus.PASS,
        summary="Passed.",
        details=("Detail",),
        evidence_ids=("evidence-1",),
    )

    assert check.passed is True
    assert check.to_dict()["status"] == "PASS"


@pytest.mark.parametrize(
    ("statuses", "expected"),
    [
        (
            [VerificationStatus.PASS],
            VerificationStatus.PASS,
        ),
        (
            [
                VerificationStatus.PASS,
                VerificationStatus.WARNING,
            ],
            VerificationStatus.WARNING,
        ),
        (
            [
                VerificationStatus.WARNING,
                VerificationStatus.FAIL,
            ],
            VerificationStatus.FAIL,
        ),
        (
            [
                VerificationStatus.FAIL,
                VerificationStatus.ERROR,
            ],
            VerificationStatus.ERROR,
        ),
        (
            [],
            VerificationStatus.SKIPPED,
        ),
    ],
)
def test_aggregate_status(
    statuses: list[VerificationStatus],
    expected: VerificationStatus,
) -> None:
    assert aggregate_status(statuses) is expected


def test_result_from_checks() -> None:
    result = VerificationResult.from_checks(
        verifier_id="test",
        verifier_name="Test Verifier",
        target="target",
        summary="Summary",
        checks=(
            VerificationCheck(
                check_id="pass",
                title="Pass",
                status=VerificationStatus.PASS,
                summary="Passed.",
            ),
            VerificationCheck(
                check_id="warning",
                title="Warning",
                status=(
                    VerificationStatus.WARNING
                ),
                summary="Warning.",
            ),
        ),
    )

    assert result.status is (
        VerificationStatus.WARNING
    )
    assert result.successful is True
    assert result.passed is False


def test_result_errors_force_error_status() -> None:
    result = VerificationResult.from_checks(
        verifier_id="test",
        verifier_name="Test",
        target="target",
        summary="Summary",
        checks=(),
        errors=("Failure",),
    )

    assert result.status is VerificationStatus.ERROR
    assert result.successful is False


def test_runner_runs_verifier() -> None:
    request = VerificationRequest(
        target="app/example"
    )

    result = VerificationRunner().run(
        PassingVerifier(),
        request,
    )

    assert result.status is VerificationStatus.PASS
    assert result.verifier_id == "test.passing"
    assert len(result.evidence) == 1


def test_runner_captures_exception() -> None:
    request = VerificationRequest(
        target="app/example"
    )

    result = VerificationRunner().run(
        ErrorVerifier(),
        request,
    )

    assert result.status is VerificationStatus.ERROR
    assert result.errors
    assert "RuntimeError" in result.errors[0]


def test_runner_can_propagate_exception() -> None:
    request = VerificationRequest(
        target="app/example"
    )

    runner = VerificationRunner(
        capture_exceptions=False
    )

    with pytest.raises(
        RuntimeError,
        match="verification exploded",
    ):
        runner.run(
            ErrorVerifier(),
            request,
        )


def test_runner_run_many() -> None:
    request = VerificationRequest(
        target="app/example"
    )

    run = VerificationRunner().run_many(
        [
            PassingVerifier(),
            FailingVerifier(),
        ],
        request,
    )

    assert len(run.results) == 2
    assert run.successful is False


def test_runner_fail_fast() -> None:
    request = VerificationRequest(
        target="app/example"
    )

    run = VerificationRunner(
        fail_fast=True
    ).run_many(
        [
            FailingVerifier(),
            PassingVerifier(),
        ],
        request,
    )

    assert len(run.results) == 1
    assert run.results[0].status is (
        VerificationStatus.FAIL
    )


def test_report_from_results() -> None:
    request = VerificationRequest(
        target="app/example"
    )

    run = VerificationRunner().run_many(
        [
            PassingVerifier(),
            FailingVerifier(),
        ],
        request,
    )

    report = VerificationReport.from_results(
        report_id="VR-001",
        title="Verification Report",
        target=request.target,
        results=run.results,
    )

    assert report.status is VerificationStatus.FAIL
    assert report.successful is False
    assert report.counts["PASS"] == 1
    assert report.counts["FAIL"] == 1

    payload = report.to_dict()

    assert payload["report_id"] == "VR-001"
    assert len(payload["results"]) == 2


def test_invalid_verifier_subclass_is_rejected() -> None:
    with pytest.raises(
        TypeError,
        match="verifier_id",
    ):

        class InvalidVerifier(BaseVerifier):
            verifier_name = "Invalid"

            def verify(
                self,
                request: VerificationRequest,
            ) -> VerificationResult:
                raise NotImplementedError
