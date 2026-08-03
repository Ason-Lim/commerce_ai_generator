from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import Any

from tools.verification.boundary.ast_scanner import (
    AstScanResult,
    CallReference,
    ImportReference,
    scan_python_file,
)
from tools.verification.boundary.layer_rules import (
    DEFAULT_LAYER_POLICIES,
    EXTERNAL_FORBIDDEN_ROOTS,
    LayerPolicy,
)
from tools.verification.core import (
    BaseVerifier,
    EvidenceKind,
    VerificationCheck,
    VerificationEvidence,
    VerificationRequest,
    VerificationResult,
    VerificationStatus,
)


class ArchitectureBoundaryVerifier(
    BaseVerifier
):
    verifier_id = "architecture.boundary"
    verifier_name = (
        "Architecture Boundary Verifier"
    )
    version = "1.0.0"

    def __init__(
        self,
        *,
        policies: Iterable[
            LayerPolicy
        ] = DEFAULT_LAYER_POLICIES,
        external_forbidden_roots: Iterable[
            str
        ] = EXTERNAL_FORBIDDEN_ROOTS,
    ) -> None:
        self.policies = tuple(policies)
        self.external_forbidden_roots = tuple(
            external_forbidden_roots
        )

    def verify(
        self,
        request: VerificationRequest,
    ) -> VerificationResult:
        target_path = request.target_path

        if not target_path.exists():
            return self._target_error(
                request=request,
                message=(
                    "Verification target does "
                    "not exist."
                ),
            )

        if not target_path.is_dir():
            return self._target_error(
                request=request,
                message=(
                    "Verification target must "
                    "be a directory."
                ),
            )

        checks: list[VerificationCheck] = []
        evidence: list[
            VerificationEvidence
        ] = []

        scans: dict[str, AstScanResult] = {}

        for policy in self.policies:
            for filename in policy.filenames:
                path = target_path / filename

                if not path.exists():
                    continue

                scan = scan_python_file(path)
                scans[filename] = scan

                evidence.append(
                    self._scan_evidence(
                        policy=policy,
                        scan=scan,
                    )
                )

                checks.append(
                    self._syntax_check(
                        policy=policy,
                        scan=scan,
                    )
                )

                if scan.successful:
                    checks.extend(
                        self._layer_checks(
                            policy=policy,
                            scan=scan,
                        )
                    )

        checks.append(
            self._required_files_check(
                target_path=target_path,
            )
        )

        provider_scan = scans.get(
            "provider.py"
        )

        if provider_scan is not None:
            checks.extend(
                self._provider_checks(
                    provider_scan
                )
            )

        failed_count = sum(
            check.status
            in {
                VerificationStatus.FAIL,
                VerificationStatus.ERROR,
            }
            for check in checks
        )

        summary = (
            "Architecture boundary "
            "verification passed."
            if failed_count == 0
            else (
                "Architecture boundary "
                f"verification found "
                f"{failed_count} failure(s)."
            )
        )

        return VerificationResult.from_checks(
            verifier_id=self.verifier_id,
            verifier_name=self.verifier_name,
            target=request.target,
            summary=summary,
            checks=checks,
            evidence=evidence,
            metadata={
                "verifier_version": self.version,
                "domain_id": request.domain_id,
                "architecture_id": (
                    request.architecture_id
                ),
                "scanned_files": sorted(
                    scans
                ),
            },
        )

    def _layer_checks(
        self,
        *,
        policy: LayerPolicy,
        scan: AstScanResult,
    ) -> list[VerificationCheck]:
        return [
            self._forbidden_import_check(
                policy=policy,
                scan=scan,
            ),
            self._forbidden_call_check(
                policy=policy,
                scan=scan,
            ),
            self._external_dependency_check(
                policy=policy,
                scan=scan,
            ),
        ]

    def _syntax_check(
        self,
        *,
        policy: LayerPolicy,
        scan: AstScanResult,
    ) -> VerificationCheck:
        if scan.syntax_error is None:
            return VerificationCheck(
                check_id=(
                    f"boundary."
                    f"{policy.layer_id}."
                    f"{scan.path.name}.syntax"
                ),
                title=(
                    f"{policy.title} syntax"
                ),
                status=VerificationStatus.PASS,
                summary=(
                    f"{scan.path.name} parsed "
                    "successfully."
                ),
            )

        return VerificationCheck(
            check_id=(
                f"boundary."
                f"{policy.layer_id}."
                f"{scan.path.name}.syntax"
            ),
            title=f"{policy.title} syntax",
            status=VerificationStatus.ERROR,
            summary=scan.syntax_error,
        )

    def _forbidden_import_check(
        self,
        *,
        policy: LayerPolicy,
        scan: AstScanResult,
    ) -> VerificationCheck:
        violations: list[str] = []

        for reference in scan.imports:
            if self._has_forbidden_segment(
                reference,
                policy.forbidden_module_segments,
            ):
                violations.append(
                    self._format_import(
                        reference
                    )
                )
                continue

            if (
                reference.name
                in policy
                .forbidden_import_symbols
            ):
                violations.append(
                    self._format_import(
                        reference
                    )
                )

        return self._violation_check(
            check_id=(
                f"boundary."
                f"{policy.layer_id}."
                f"{scan.path.name}.imports"
            ),
            title=(
                f"{policy.title} imports"
            ),
            pass_summary=(
                "No forbidden layer imports "
                "were found."
            ),
            fail_summary=(
                "Forbidden layer imports "
                "were found."
            ),
            violations=violations,
        )

    def _forbidden_call_check(
        self,
        *,
        policy: LayerPolicy,
        scan: AstScanResult,
    ) -> VerificationCheck:
        violations: list[str] = []

        for call in scan.calls:
            if (
                call.leaf_name
                in policy.forbidden_call_names
            ):
                violations.append(
                    self._format_call(call)
                )
                continue

            if any(
                call.leaf_name.startswith(
                    prefix
                )
                for prefix in (
                    policy
                    .forbidden_call_prefixes
                )
            ):
                violations.append(
                    self._format_call(call)
                )

        return self._violation_check(
            check_id=(
                f"boundary."
                f"{policy.layer_id}."
                f"{scan.path.name}.calls"
            ),
            title=f"{policy.title} calls",
            pass_summary=(
                "No forbidden layer calls "
                "were found."
            ),
            fail_summary=(
                "Forbidden layer calls "
                "were found."
            ),
            violations=violations,
        )

    def _external_dependency_check(
        self,
        *,
        policy: LayerPolicy,
        scan: AstScanResult,
    ) -> VerificationCheck:
        violations: list[str] = []

        for reference in scan.imports:
            root = (
                reference.module
                .lstrip(".")
                .split(".", 1)[0]
            )

            if (
                root
                in self.external_forbidden_roots
            ):
                violations.append(
                    self._format_import(
                        reference
                    )
                )

        return self._violation_check(
            check_id=(
                f"boundary."
                f"{policy.layer_id}."
                f"{scan.path.name}."
                "external_dependencies"
            ),
            title=(
                f"{policy.title} external "
                "dependencies"
            ),
            pass_summary=(
                "No forbidden external "
                "dependencies were found."
            ),
            fail_summary=(
                "Forbidden external "
                "dependencies were found."
            ),
            violations=violations,
        )

    def _provider_checks(
        self,
        scan: AstScanResult,
    ) -> list[VerificationCheck]:
        policy = next(
            item
            for item in self.policies
            if item.layer_id == "provider"
        )

        return [
            self._provider_base_check(
                policy=policy,
                scan=scan,
            ),
            self._provider_flow_check(
                policy=policy,
                scan=scan,
            ),
        ]

    def _provider_base_check(
        self,
        *,
        policy: LayerPolicy,
        scan: AstScanResult,
    ) -> VerificationCheck:
        required_base = (
            policy.required_class_base
        )

        matched = any(
            required_base
            in {
                base.rsplit(".", 1)[-1]
                for base in class_ref.bases
            }
            for class_ref in scan.classes
        )

        if matched:
            return VerificationCheck(
                check_id=(
                    "boundary.provider."
                    "inheritance"
                ),
                title="Provider inheritance",
                status=VerificationStatus.PASS,
                summary=(
                    "Provider inherits from "
                    f"{required_base}."
                ),
            )

        return VerificationCheck(
            check_id=(
                "boundary.provider."
                "inheritance"
            ),
            title="Provider inheritance",
            status=VerificationStatus.FAIL,
            summary=(
                "Provider does not inherit "
                f"from {required_base}."
            ),
        )

    def _provider_flow_check(
        self,
        *,
        policy: LayerPolicy,
        scan: AstScanResult,
    ) -> VerificationCheck:
        function_name = (
            policy.required_function
        )

        calls = scan.calls_in_function(
            function_name
        )

        actual = tuple(
            call.leaf_name
            for call in calls
        )

        required = (
            policy.required_call_sequence
        )

        matched = is_subsequence(
            required,
            actual,
        )

        details = (
            "Required: "
            + " -> ".join(required),
            "Observed: "
            + " -> ".join(actual),
        )

        if matched:
            return VerificationCheck(
                check_id=(
                    "boundary.provider.flow"
                ),
                title=(
                    "Provider orchestration "
                    "flow"
                ),
                status=VerificationStatus.PASS,
                summary=(
                    "Required Provider call "
                    "sequence was found."
                ),
                details=details,
            )

        return VerificationCheck(
            check_id=(
                "boundary.provider.flow"
            ),
            title=(
                "Provider orchestration flow"
            ),
            status=VerificationStatus.FAIL,
            summary=(
                "Required Provider call "
                "sequence was not found."
            ),
            details=details,
        )

    def _required_files_check(
        self,
        *,
        target_path: Path,
    ) -> VerificationCheck:
        required = (
            "parser.py",
            "parser_models.py",
            "attributes.py",
            "scoring.py",
            "rules.py",
            "provider.py",
        )

        missing = tuple(
            filename
            for filename in required
            if not (
                target_path / filename
            ).is_file()
        )

        if not missing:
            return VerificationCheck(
                check_id=(
                    "boundary.domain."
                    "required_files"
                ),
                title=(
                    "Required domain files"
                ),
                status=VerificationStatus.PASS,
                summary=(
                    "All required domain "
                    "files are present."
                ),
            )

        return VerificationCheck(
            check_id=(
                "boundary.domain."
                "required_files"
            ),
            title="Required domain files",
            status=VerificationStatus.FAIL,
            summary=(
                "Required domain files are "
                "missing."
            ),
            details=missing,
        )

    def _scan_evidence(
        self,
        *,
        policy: LayerPolicy,
        scan: AstScanResult,
    ) -> VerificationEvidence:
        return VerificationEvidence(
            evidence_id=(
                f"boundary-source-"
                f"{policy.layer_id}-"
                f"{scan.path.name}"
            ),
            kind=EvidenceKind.BOUNDARY,
            title=(
                f"{policy.title}: "
                f"{scan.path.name}"
            ),
            location=str(scan.path),
            summary=(
                "AST source scan result."
            ),
            metadata={
                "imports": len(scan.imports),
                "calls": len(scan.calls),
                "classes": len(
                    scan.classes
                ),
                "functions": list(
                    scan.functions
                ),
                "syntax_error": (
                    scan.syntax_error
                ),
            },
        )

    def _target_error(
        self,
        *,
        request: VerificationRequest,
        message: str,
    ) -> VerificationResult:
        return VerificationResult(
            verifier_id=self.verifier_id,
            verifier_name=self.verifier_name,
            target=request.target,
            status=VerificationStatus.ERROR,
            summary=message,
            checks=(
                VerificationCheck(
                    check_id=(
                        "boundary.target"
                    ),
                    title=(
                        "Verification target"
                    ),
                    status=(
                        VerificationStatus.ERROR
                    ),
                    summary=message,
                ),
            ),
            errors=(message,),
            metadata={
                "verifier_version": (
                    self.version
                ),
            },
        )

    @staticmethod
    def _has_forbidden_segment(
        reference: ImportReference,
        forbidden_segments: tuple[
            str,
            ...
        ],
    ) -> bool:
        module = reference.module.lstrip(
            "."
        )

        segments = {
            segment
            for segment in module.split(".")
            if segment
        }

        return bool(
            segments.intersection(
                forbidden_segments
            )
        )

    @staticmethod
    def _format_import(
        reference: ImportReference,
    ) -> str:
        return (
            f"line {reference.line}: "
            f"{reference.qualified_name}"
        )

    @staticmethod
    def _format_call(
        call: CallReference,
    ) -> str:
        return (
            f"line {call.line}: "
            f"{call.qualified_name}"
        )

    @staticmethod
    def _violation_check(
        *,
        check_id: str,
        title: str,
        pass_summary: str,
        fail_summary: str,
        violations: list[str],
    ) -> VerificationCheck:
        if not violations:
            return VerificationCheck(
                check_id=check_id,
                title=title,
                status=VerificationStatus.PASS,
                summary=pass_summary,
            )

        return VerificationCheck(
            check_id=check_id,
            title=title,
            status=VerificationStatus.FAIL,
            summary=fail_summary,
            details=tuple(violations),
        )


def is_subsequence(
    required: Iterable[str],
    actual: Iterable[str],
) -> bool:
    required_values = tuple(required)

    if not required_values:
        return True

    index = 0

    for value in actual:
        if value == required_values[index]:
            index += 1

            if index == len(
                required_values
            ):
                return True

    return False


__all__ = [
    "ArchitectureBoundaryVerifier",
    "is_subsequence",
]
