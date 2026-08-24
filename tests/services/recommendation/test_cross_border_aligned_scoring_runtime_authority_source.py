from app.services.recommendation.cross_border_aligned_scoring_policy_fallback import (
    AlignedCrossBorderScoringFallback,
    AlignedCrossBorderScoringFallbackState,
)
from app.services.recommendation.cross_border_aligned_scoring_runtime_authority_source import (
    RuntimeAuthoritySourceState,
    resolve_runtime_authority_source,
)
from app.services.recommendation.cross_border_scoring_policy_fallback import (
    CrossBorderScoringFallbackDecision,
    CrossBorderScoringFallbackTarget,
)


def _fallback(
    target=CrossBorderScoringFallbackTarget.BASELINE,
):
    return CrossBorderScoringFallbackDecision(
        target=target,
        baseline_policy_id="baseline-v1",
        candidate_policy_id="candidate-v1",
        fallback_required=(
            target is CrossBorderScoringFallbackTarget.BASELINE
        ),
        activation_allowed=(
            target is CrossBorderScoringFallbackTarget.CANDIDATE
        ),
        boundary_eligible=(
            target is CrossBorderScoringFallbackTarget.CANDIDATE
        ),
        policy_identity_ready=True,
        authority_identity_ready=True,
        activation_state_safe=True,
        fallback_reason=(
            "boundary"
            if target is CrossBorderScoringFallbackTarget.BASELINE
            else None
        ),
    )


def _aligned(
    *,
    state=AlignedCrossBorderScoringFallbackState.AVAILABLE,
    fallback=None,
):
    return AlignedCrossBorderScoringFallback(
        state=state,
        aligned_boundary=object(),
        fallback=fallback,
        reasons=(
            ()
            if state is AlignedCrossBorderScoringFallbackState.AVAILABLE
            else ("blocked",)
        ),
    )


def test_missing_runtime_authority_fails_closed():
    result = resolve_runtime_authority_source(None)

    assert result.state is RuntimeAuthoritySourceState.BLOCKED
    assert result.authority is None
    assert result.reasons == ("runtime_authority_unavailable",)


def test_blocked_aligned_authority_fails_closed():
    authority = _aligned(
        state=AlignedCrossBorderScoringFallbackState.BLOCKED,
        fallback=None,
    )

    result = resolve_runtime_authority_source(authority)

    assert result.state is RuntimeAuthoritySourceState.BLOCKED
    assert result.authority is None
    assert result.reasons == ("aligned_runtime_authority_blocked",)


def test_available_without_canonical_fallback_fails_closed():
    authority = _aligned(
        fallback=None,
    )

    result = resolve_runtime_authority_source(authority)

    assert result.state is RuntimeAuthoritySourceState.BLOCKED
    assert result.authority is None
    assert result.reasons == ("canonical_fallback_unavailable",)


def test_available_baseline_authority_is_preserved_unchanged():
    authority = _aligned(
        fallback=_fallback(
            CrossBorderScoringFallbackTarget.BASELINE
        ),
    )

    result = resolve_runtime_authority_source(authority)

    assert result.state is RuntimeAuthoritySourceState.AVAILABLE
    assert result.authority is authority
    assert result.authority.fallback is authority.fallback
    assert (
        result.authority.fallback.target
        is CrossBorderScoringFallbackTarget.BASELINE
    )
    assert result.reasons == ()


def test_available_candidate_authority_is_preserved_unchanged():
    authority = _aligned(
        fallback=_fallback(
            CrossBorderScoringFallbackTarget.CANDIDATE
        ),
    )

    result = resolve_runtime_authority_source(authority)

    assert result.state is RuntimeAuthoritySourceState.AVAILABLE
    assert result.authority is authority
    assert result.authority.fallback is authority.fallback
    assert (
        result.authority.fallback.target
        is CrossBorderScoringFallbackTarget.CANDIDATE
    )
    assert result.reasons == ()
