from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.services.recommendation.cross_border_scoring_policy_activation_boundary import (
    CrossBorderActivationBoundaryState,
    CrossBorderScoringActivationBoundary,
)


class CrossBorderScoringFallbackTarget(
    str,
    Enum,
):
    CANDIDATE = "candidate"
    BASELINE = "baseline"


@dataclass(frozen=True)
class CrossBorderScoringFallbackDecision:
    """
    Canonical fallback decision for Cross-Border scoring.

    CANDIDATE means only that a later controlled binding stage may
    consider the candidate policy.

    BASELINE means existing production scoring must remain in use.

    This contract does not execute scoring, mutate ranking,
    activate runtime policy behavior, route traffic, or produce
    recommendations.
    """

    target: CrossBorderScoringFallbackTarget

    baseline_policy_id: str
    candidate_policy_id: str

    fallback_required: bool
    activation_allowed: bool

    boundary_eligible: bool
    policy_identity_ready: bool
    authority_identity_ready: bool
    activation_state_safe: bool

    fallback_reason: str | None


def evaluate_cross_border_scoring_fallback(
    boundary: CrossBorderScoringActivationBoundary,
) -> CrossBorderScoringFallbackDecision:
    """
    Convert the R1M-A activation boundary into a deterministic,
    fail-closed fallback decision.

    Any invalid or incomplete state falls back to baseline.
    """

    baseline_policy_id = (
        boundary.baseline_policy_id.strip()
    )

    candidate_policy_id = (
        boundary.candidate_policy_id.strip()
    )

    boundary_eligible = (
        boundary.state
        is CrossBorderActivationBoundaryState.ELIGIBLE
    )

    policy_identity_ready = (
        boundary.policy_identity_ready is True
        and bool(baseline_policy_id)
        and bool(candidate_policy_id)
        and baseline_policy_id != candidate_policy_id
    )

    authority_identity_ready = (
        boundary.authority_identity_ready is True
        and bool(boundary.activation_authority_id.strip())
        and bool(boundary.activation_authority_role.strip())
    )

    activation_state_safe = (
        boundary.activation_state_safe is True
    )

    checks = {
        "boundary": boundary_eligible,
        "policy_identity": policy_identity_ready,
        "authority_identity": authority_identity_ready,
        "activation_state": activation_state_safe,
    }

    failed = tuple(
        name
        for name, ready in checks.items()
        if not ready
    )

    if failed:
        return CrossBorderScoringFallbackDecision(
            target=CrossBorderScoringFallbackTarget.BASELINE,
            baseline_policy_id=baseline_policy_id,
            candidate_policy_id=candidate_policy_id,
            fallback_required=True,
            activation_allowed=False,
            boundary_eligible=boundary_eligible,
            policy_identity_ready=policy_identity_ready,
            authority_identity_ready=authority_identity_ready,
            activation_state_safe=activation_state_safe,
            fallback_reason=",".join(failed),
        )

    return CrossBorderScoringFallbackDecision(
        target=CrossBorderScoringFallbackTarget.CANDIDATE,
        baseline_policy_id=baseline_policy_id,
        candidate_policy_id=candidate_policy_id,
        fallback_required=False,
        activation_allowed=True,
        boundary_eligible=True,
        policy_identity_ready=True,
        authority_identity_ready=True,
        activation_state_safe=True,
        fallback_reason=None,
    )
