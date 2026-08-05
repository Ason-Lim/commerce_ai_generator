from __future__ import annotations

import subprocess
from collections.abc import Iterable
from typing import Any

from app.services.food.knowledge.base import (
    FoodKnowledgeProvider,
)
from app.services.food.knowledge.models import (
    FoodKnowledgeResult,
)
from app.services.food.knowledge.registry import (
    FOOD_KNOWLEDGE_REGISTRY,
    get_food_provider,
    list_food_providers,
    require_food_provider,
    resolve_food_provider,
)
from app.services.food.resolver import (
    resolve_food_knowledge,
    resolve_knowledge_provider,
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
from tools.verification.integration.profiles import (
    IntegrationProfile,
    RoutingCase,
    get_integration_profile,
)


SUPPORTED_PHASES = {
    "registration",
    "selection",
    "contract",
    "routing",
    "regression",
    "all",
}


class IntegrationVerificationTool(
    BaseVerifier
):
    verifier_id = "integration.project"
    verifier_name = (
        "Project Integration Verification Tool"
    )
    version = "1.0.0"

    def __init__(
        self,
        *,
        profile: IntegrationProfile,
        phase: str = "all",
    ) -> None:
        normalized_phase = (
            phase.strip().casefold()
        )

        if normalized_phase not in SUPPORTED_PHASES:
            raise ValueError(
                "Unsupported integration phase: "
                f"{phase}"
            )

        self.profile = profile
        self.phase = normalized_phase

    @classmethod
    def from_profile_id(
        cls,
        profile_id: str,
        *,
        phase: str = "all",
    ) -> IntegrationVerificationTool:
        return cls(
            profile=get_integration_profile(
                profile_id
            ),
            phase=phase,
        )

    def verify(
        self,
        request: VerificationRequest,
    ) -> VerificationResult:
        checks: list[VerificationCheck] = []
        evidence: list[
            VerificationEvidence
        ] = []

        phases = (
            (
                "registration",
                "selection",
                "contract",
                "routing",
                "regression",
            )
            if self.phase == "all"
            else (self.phase,)
        )

        for phase in phases:
            phase_checks, phase_evidence = (
                self._run_phase(phase)
            )
            checks.extend(phase_checks)
            evidence.extend(phase_evidence)

        failure_count = sum(
            check.status
            in {
                VerificationStatus.FAIL,
                VerificationStatus.ERROR,
            }
            for check in checks
        )

        summary = (
            "Project integration verification "
            "passed."
            if failure_count == 0
            else (
                "Project integration verification "
                f"found {failure_count} "
                "failure(s)."
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
                "profile_id": (
                    self.profile.profile_id
                ),
                "domain_id": (
                    self.profile.domain_id
                ),
                "architecture_id": (
                    self.profile.architecture_id
                ),
                "category_id": (
                    self.profile.category_id
                ),
                "phase": self.phase,
                "executed_phases": list(phases),
            },
        )

    def _run_phase(
        self,
        phase: str,
    ) -> tuple[
        list[VerificationCheck],
        list[VerificationEvidence],
    ]:
        handlers = {
            "registration": (
                self._verify_registration
            ),
            "selection": self._verify_selection,
            "contract": self._verify_contract,
            "routing": self._verify_routing,
            "regression": (
                self._verify_regression
            ),
        }

        return handlers[phase]()

    def _verify_registration(
        self,
    ) -> tuple[
        list[VerificationCheck],
        list[VerificationEvidence],
    ]:
        profile = self.profile
        provider = get_food_provider(
            profile.category_id
        )

        providers = list_food_providers()
        category_ids = (
            FOOD_KNOWLEDGE_REGISTRY
            .list_category_ids()
        )

        matching = [
            item
            for item in providers
            if item.category_id
            == profile.category_id
        ]

        checks = [
            self._boolean_check(
                check_id=(
                    "integration.registration."
                    "registry_contains"
                ),
                title="Registry membership",
                passed=(
                    profile.category_id
                    in FOOD_KNOWLEDGE_REGISTRY
                ),
                pass_summary=(
                    "Provider category is present "
                    "in the shared Registry."
                ),
                fail_summary=(
                    "Provider category is missing "
                    "from the shared Registry."
                ),
            ),
            self._boolean_check(
                check_id=(
                    "integration.registration."
                    "provider_retrieval"
                ),
                title="Provider retrieval",
                passed=(
                    provider is not None
                    and provider.__class__.__name__
                    == profile.provider_class_name
                ),
                pass_summary=(
                    "get_food_provider returned "
                    "the expected Provider."
                ),
                fail_summary=(
                    "get_food_provider did not "
                    "return the expected Provider."
                ),
            ),
            self._required_provider_check(),
            self._boolean_check(
                check_id=(
                    "integration.registration."
                    "provider_contract"
                ),
                title="Provider base contract",
                passed=isinstance(
                    provider,
                    FoodKnowledgeProvider,
                ),
                pass_summary=(
                    "Provider satisfies "
                    "FoodKnowledgeProvider."
                ),
                fail_summary=(
                    "Provider does not satisfy "
                    "FoodKnowledgeProvider."
                ),
            ),
            self._boolean_check(
                check_id=(
                    "integration.registration."
                    "provider_identity"
                ),
                title="Provider identity",
                passed=(
                    provider is not None
                    and provider.category_id
                    == profile.category_id
                    and provider.category_name
                    == profile.category_name
                ),
                pass_summary=(
                    "Provider category identity "
                    "matches the profile."
                ),
                fail_summary=(
                    "Provider category identity "
                    "does not match the profile."
                ),
            ),
            self._boolean_check(
                check_id=(
                    "integration.registration."
                    "single_registration"
                ),
                title="Single registration",
                passed=len(matching) == 1,
                pass_summary=(
                    "Provider is registered "
                    "exactly once."
                ),
                fail_summary=(
                    "Provider registration count "
                    "is not exactly one."
                ),
                details=(
                    f"Observed count: "
                    f"{len(matching)}",
                ),
            ),
            self._boolean_check(
                check_id=(
                    "integration.registration."
                    "category_uniqueness"
                ),
                title="Category uniqueness",
                passed=(
                    len(category_ids)
                    == len(set(category_ids))
                ),
                pass_summary=(
                    "Provider category identifiers "
                    "are unique."
                ),
                fail_summary=(
                    "Duplicate Provider category "
                    "identifiers were found."
                ),
            ),
        ]

        evidence = [
            VerificationEvidence(
                evidence_id=(
                    "integration-registration-"
                    f"{profile.category_id}"
                ),
                kind=EvidenceKind.REGISTRY,
                title=(
                    f"{profile.category_name} "
                    "Provider registration"
                ),
                summary=(
                    "Current shared Registry "
                    "registration snapshot."
                ),
                metadata={
                    "provider_class": (
                        provider.__class__.__name__
                        if provider is not None
                        else None
                    ),
                    "category_id": (
                        provider.category_id
                        if provider is not None
                        else None
                    ),
                    "category_name": (
                        provider.category_name
                        if provider is not None
                        else None
                    ),
                    "registration_count": (
                        len(matching)
                    ),
                    "registry_order_snapshot": (
                        category_ids
                    ),
                },
            )
        ]

        return checks, evidence

    def _required_provider_check(
        self,
    ) -> VerificationCheck:
        try:
            provider = require_food_provider(
                self.profile.category_id
            )
        except Exception as exc:
            return VerificationCheck(
                check_id=(
                    "integration.registration."
                    "required_retrieval"
                ),
                title=(
                    "Required Provider retrieval"
                ),
                status=VerificationStatus.FAIL,
                summary=(
                    f"{exc.__class__.__name__}: "
                    f"{exc}"
                ),
            )

        passed = (
            provider.__class__.__name__
            == self.profile.provider_class_name
        )

        return self._boolean_check(
            check_id=(
                "integration.registration."
                "required_retrieval"
            ),
            title="Required Provider retrieval",
            passed=passed,
            pass_summary=(
                "require_food_provider returned "
                "the expected Provider."
            ),
            fail_summary=(
                "require_food_provider returned "
                "an unexpected Provider."
            ),
        )

    def _verify_selection(
        self,
    ) -> tuple[
        list[VerificationCheck],
        list[VerificationEvidence],
    ]:
        profile = self.profile
        checks: list[VerificationCheck] = []
        observed: list[dict[str, Any]] = []

        explicit = resolve_knowledge_provider(
            dict(profile.explicit_product),
            category_id=profile.category_id,
        )

        checks.append(
            self._boolean_check(
                check_id=(
                    "integration.selection."
                    "explicit"
                ),
                title=(
                    "Explicit Provider selection"
                ),
                passed=(
                    explicit is not None
                    and explicit.category_id
                    == profile.category_id
                ),
                pass_summary=(
                    "Explicit category selection "
                    "returned the expected Provider."
                ),
                fail_summary=(
                    "Explicit category selection "
                    "did not return the expected "
                    "Provider."
                ),
            )
        )

        for index, case in enumerate(
            profile.automatic_cases,
            start=1,
        ):
            provider = resolve_food_provider(
                product_name=case.product_name
            )

            actual = (
                provider.category_id
                if provider is not None
                else None
            )

            observed.append(
                {
                    "product_name": (
                        case.product_name
                    ),
                    "expected": (
                        case.expected_category_id
                    ),
                    "actual": actual,
                }
            )

            checks.append(
                self._boolean_check(
                    check_id=(
                        "integration.selection."
                        f"automatic.{index}"
                    ),
                    title=(
                        "Automatic Provider "
                        f"selection #{index}"
                    ),
                    passed=(
                        actual
                        == case
                        .expected_category_id
                    ),
                    pass_summary=(
                        "Automatic selection "
                        "returned the expected "
                        "Provider."
                    ),
                    fail_summary=(
                        "Automatic selection "
                        "returned an unexpected "
                        "Provider."
                    ),
                    details=(
                        f"Product: "
                        f"{case.product_name}",
                        f"Expected: "
                        f"{case.expected_category_id}",
                        f"Actual: {actual}",
                    ),
                )
            )

        evidence = [
            VerificationEvidence(
                evidence_id=(
                    "integration-selection-"
                    f"{profile.category_id}"
                ),
                kind=EvidenceKind.INTEGRATION,
                title=(
                    f"{profile.category_name} "
                    "Provider selection"
                ),
                summary=(
                    "Explicit and automatic "
                    "selection evidence."
                ),
                metadata={
                    "explicit_category": (
                        explicit.category_id
                        if explicit is not None
                        else None
                    ),
                    "automatic_cases": observed,
                },
            )
        ]

        return checks, evidence

    def _verify_contract(
        self,
    ) -> tuple[
        list[VerificationCheck],
        list[VerificationEvidence],
    ]:
        profile = self.profile

        result = resolve_food_knowledge(
            dict(profile.analysis_product),
            category_id=profile.category_id,
            strict=True,
        )

        checks = [
            self._boolean_check(
                check_id=(
                    "integration.contract."
                    "result_type"
                ),
                title="Result type",
                passed=isinstance(
                    result,
                    FoodKnowledgeResult,
                ),
                pass_summary=(
                    "Runtime returned "
                    "FoodKnowledgeResult."
                ),
                fail_summary=(
                    "Runtime did not return "
                    "FoodKnowledgeResult."
                ),
            ),
            self._boolean_check(
                check_id=(
                    "integration.contract."
                    "category_identity"
                ),
                title="Result category identity",
                passed=(
                    result is not None
                    and result.category_id
                    == profile.category_id
                    and result.category_name
                    == profile.category_name
                ),
                pass_summary=(
                    "Result category identity "
                    "matches the profile."
                ),
                fail_summary=(
                    "Result category identity "
                    "does not match the profile."
                ),
            ),
            self._boolean_check(
                check_id=(
                    "integration.contract."
                    "serialization"
                ),
                title="Result serialization",
                passed=self._is_serializable_result(
                    result
                ),
                pass_summary=(
                    "Result satisfies the "
                    "serialization contract."
                ),
                fail_summary=(
                    "Result does not satisfy the "
                    "serialization contract."
                ),
            ),
        ]

        for key, expected in (
            profile.expected_attributes.items()
        ):
            actual = (
                result.attributes.get(key)
                if result is not None
                else None
            )

            checks.append(
                self._boolean_check(
                    check_id=(
                        "integration.contract."
                        f"attribute.{key}"
                    ),
                    title=(
                        f"Result attribute: {key}"
                    ),
                    passed=actual == expected,
                    pass_summary=(
                        "Attribute matches the "
                        "expected contract value."
                    ),
                    fail_summary=(
                        "Attribute does not match "
                        "the expected contract value."
                    ),
                    details=(
                        f"Expected: {expected}",
                        f"Actual: {actual}",
                    ),
                )
            )

        for key, expected in (
            profile.expected_scores.items()
        ):
            actual = (
                result.scores.get(key)
                if result is not None
                else None
            )

            checks.append(
                self._boolean_check(
                    check_id=(
                        "integration.contract."
                        f"score.{key}"
                    ),
                    title=f"Result score: {key}",
                    passed=actual == expected,
                    pass_summary=(
                        "Score matches the expected "
                        "contract value."
                    ),
                    fail_summary=(
                        "Score does not match the "
                        "expected contract value."
                    ),
                    details=(
                        f"Expected: {expected}",
                        f"Actual: {actual}",
                    ),
                )
            )

        if (
            profile.expected_final_score
            is not None
        ):
            actual_final = (
                result.final_score
                if result is not None
                else None
            )

            checks.append(
                self._boolean_check(
                    check_id=(
                        "integration.contract."
                        "final_score"
                    ),
                    title="Result final score",
                    passed=(
                        actual_final
                        == profile
                        .expected_final_score
                    ),
                    pass_summary=(
                        "Final score matches the "
                        "expected contract value."
                    ),
                    fail_summary=(
                        "Final score does not match "
                        "the expected contract value."
                    ),
                    details=(
                        "Expected: "
                        f"{profile.expected_final_score}",
                        f"Actual: {actual_final}",
                    ),
                )
            )

        evidence = [
            VerificationEvidence(
                evidence_id=(
                    "integration-contract-"
                    f"{profile.category_id}"
                ),
                kind=EvidenceKind.CONTRACT,
                title=(
                    f"{profile.category_name} "
                    "Result contract"
                ),
                summary=(
                    "FoodKnowledgeResult contract "
                    "verification evidence."
                ),
                metadata=(
                    result.to_dict()
                    if result is not None
                    else {}
                ),
            )
        ]

        return checks, evidence

    def _verify_routing(
        self,
    ) -> tuple[
        list[VerificationCheck],
        list[VerificationEvidence],
    ]:
        profile = self.profile
        checks: list[VerificationCheck] = []
        observed: list[dict[str, Any]] = []

        all_cases: Iterable[RoutingCase] = (
            profile.automatic_cases
            + profile.preservation_cases
        )

        for index, case in enumerate(
            all_cases,
            start=1,
        ):
            provider = resolve_knowledge_provider(
                {
                    "product_name": (
                        case.product_name
                    ),
                }
            )

            actual = (
                provider.category_id
                if provider is not None
                else None
            )

            observed.append(
                {
                    "product_name": (
                        case.product_name
                    ),
                    "expected": (
                        case.expected_category_id
                    ),
                    "actual": actual,
                }
            )

            checks.append(
                self._boolean_check(
                    check_id=(
                        "integration.routing."
                        f"case.{index}"
                    ),
                    title=(
                        f"Runtime routing #{index}"
                    ),
                    passed=(
                        actual
                        == case
                        .expected_category_id
                    ),
                    pass_summary=(
                        "Runtime routing returned "
                        "the expected Provider."
                    ),
                    fail_summary=(
                        "Runtime routing returned "
                        "an unexpected Provider."
                    ),
                    details=(
                        f"Product: "
                        f"{case.product_name}",
                        f"Expected: "
                        f"{case.expected_category_id}",
                        f"Actual: {actual}",
                    ),
                )
            )

        evidence = [
            VerificationEvidence(
                evidence_id=(
                    "integration-routing-"
                    f"{profile.category_id}"
                ),
                kind=EvidenceKind.INTEGRATION,
                title=(
                    f"{profile.category_name} "
                    "runtime routing"
                ),
                summary=(
                    "Target and cross-domain "
                    "runtime routing evidence."
                ),
                metadata={
                    "routing_cases": observed,
                },
            )
        ]

        return checks, evidence

    def _verify_regression(
        self,
    ) -> tuple[
        list[VerificationCheck],
        list[VerificationEvidence],
    ]:
        command = [
            "python",
            "-m",
            "pytest",
            "-q",
            self.profile.regression_target,
            "--disable-warnings",
        ]

        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
        )

        output = (
            completed.stdout
            + completed.stderr
        ).strip()

        passed = completed.returncode == 0

        checks = [
            self._boolean_check(
                check_id=(
                    "integration.regression."
                    "food_knowledge"
                ),
                title=(
                    "Cross-domain regression"
                ),
                passed=passed,
                pass_summary=(
                    "Food Knowledge regression "
                    "completed successfully."
                ),
                fail_summary=(
                    "Food Knowledge regression "
                    "failed."
                ),
                details=(
                    f"Exit code: "
                    f"{completed.returncode}",
                    output,
                ),
            )
        ]

        evidence = [
            VerificationEvidence(
                evidence_id=(
                    "integration-regression-"
                    f"{self.profile.category_id}"
                ),
                kind=EvidenceKind.REGRESSION,
                title=(
                    "Food Knowledge regression"
                ),
                summary=(
                    "Project-level cross-domain "
                    "regression execution."
                ),
                metadata={
                    "command": command,
                    "exit_code": (
                        completed.returncode
                    ),
                    "output": output,
                },
            )
        ]

        return checks, evidence

    @staticmethod
    def _is_serializable_result(
        result: FoodKnowledgeResult | None,
    ) -> bool:
        if result is None:
            return False

        try:
            payload = result.to_dict()
        except Exception:
            return False

        required_keys = {
            "category_id",
            "category_name",
            "product_name",
            "attributes",
            "scores",
            "reasons",
            "warnings",
            "final_score",
            "confidence",
            "metadata",
        }

        return (
            isinstance(payload, dict)
            and required_keys.issubset(payload)
        )

    @staticmethod
    def _boolean_check(
        *,
        check_id: str,
        title: str,
        passed: bool,
        pass_summary: str,
        fail_summary: str,
        details: tuple[str, ...] = (),
    ) -> VerificationCheck:
        return VerificationCheck(
            check_id=check_id,
            title=title,
            status=(
                VerificationStatus.PASS
                if passed
                else VerificationStatus.FAIL
            ),
            summary=(
                pass_summary
                if passed
                else fail_summary
            ),
            details=details,
        )


__all__ = [
    "SUPPORTED_PHASES",
    "IntegrationVerificationTool",
]
