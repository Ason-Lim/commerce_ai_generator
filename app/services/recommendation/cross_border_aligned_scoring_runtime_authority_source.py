from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.services.recommendation.cross_border_aligned_scoring_policy_fallback import (
    AlignedCrossBorderScoringFallback,
    AlignedCrossBorderScoringFallbackState,
)


class RuntimeAuthoritySourceState(
    str,
    Enum,
):
    AVAILABLE = "available"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class RuntimeAuthoritySource:
    """
    Fail-closed runtime source contract for an already-established
    aligned Cross-Border scoring authority.

    AVAILABLE means an existing provenance-preserving aligned
    fallback authority was supplied and may be forwarded unchanged
    to a later runtime composition boundary.

    AVAILABLE does not mean candidate scoring is authorized or will
    execute. The nested canonical fallback contract retains ownership
    of BASELINE / CANDIDATE semantics.

    BLOCKED means no usable aligned runtime authority was supplied.

    This contract does not:

    - create adoption or activation authority;
    - record governance decisions;
    - evaluate adoption or activation readiness;
    - evaluate activation boundaries;
    - synthesize fallback authority;
    - reinterpret BASELINE / CANDIDATE;
    - load authority from environment, request, file, or database;
    - enable production scoring;
    - start rollout;
    - route traffic;
    - create a candidate scorer;
    - mutate scoring or ranking;
    - produce recommendations;
    - execute transactions.
    """

    state: RuntimeAuthoritySourceState
    authority: AlignedCrossBorderScoringFallback | None
    reasons: tuple[str, ...]

    @property
    def is_available(self) -> bool:
        return self.state is RuntimeAuthoritySourceState.AVAILABLE


def resolve_runtime_authority_source(
    authority: AlignedCrossBorderScoringFallback | None,
) -> RuntimeAuthoritySource:
    """
    Resolve an already-established aligned fallback authority for
    later runtime composition.

    Missing or BLOCKED aligned authority fails closed.

    AVAILABLE authority is preserved by exact object identity.
    Nested canonical fallback semantics are not re-evaluated here.
    """

    if authority is None:
        return RuntimeAuthoritySource(
            state=RuntimeAuthoritySourceState.BLOCKED,
            authority=None,
            reasons=("runtime_authority_unavailable",),
        )

    if (
        authority.state
        is not AlignedCrossBorderScoringFallbackState.AVAILABLE
    ):
        return RuntimeAuthoritySource(
            state=RuntimeAuthoritySourceState.BLOCKED,
            authority=None,
            reasons=("aligned_runtime_authority_blocked",),
        )

    if authority.fallback is None:
        return RuntimeAuthoritySource(
            state=RuntimeAuthoritySourceState.BLOCKED,
            authority=None,
            reasons=("canonical_fallback_unavailable",),
        )

    return RuntimeAuthoritySource(
        state=RuntimeAuthoritySourceState.AVAILABLE,
        authority=authority,
        reasons=(),
    )
