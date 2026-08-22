from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.services.recommendation.cross_border_landed_cost_signal import (
    CrossBorderLandedCostAdvantage,
    CrossBorderLandedCostSignal,
    CrossBorderLandedCostSignalState,
)


class CrossBorderScoringReadinessState(
    str,
    Enum,
):
    READY = "ready"
    NOT_READY = "not_ready"


@dataclass(frozen=True)
class CrossBorderScoringReadiness:
    """
    Recommendation-side readiness assessment for a bounded
    Cross-Border landed-cost signal.

    READY means only that the signal is structurally suitable for a
    future scoring-binding layer to consider.

    This contract does not calculate scores, assign weights, modify
    ranking, select a candidate, or produce a recommendation.
    """

    state: CrossBorderScoringReadinessState

    signal_available: bool
    comparison_direction_ready: bool
    candidate_identity_ready: bool
    landed_cost_values_ready: bool
    currency_ready: bool
    evidence_quality_ready: bool
    source_contract_ready: bool

    reasons: tuple[str, ...]


_SCORING_DIRECTIONAL_ADVANTAGES = {
    CrossBorderLandedCostAdvantage.FIRST,
    CrossBorderLandedCostAdvantage.SECOND,
    CrossBorderLandedCostAdvantage.EQUAL,
}

_ACCEPTABLE_EVIDENCE_QUALITIES = {
    "known",
    "estimated",
}


def evaluate_cross_border_scoring_readiness(
    signal: CrossBorderLandedCostSignal,
) -> CrossBorderScoringReadiness:
    """
    Determine whether an R1D landed-cost signal may cross into a
    future scoring-binding layer.

    This function performs readiness evaluation only.

    It does not:
    - calculate any score;
    - define a scoring weight;
    - modify price priority;
    - rank candidates;
    - choose a winner;
    - generate a recommendation.
    """

    signal_available = (
        signal.state
        is CrossBorderLandedCostSignalState.AVAILABLE
    )

    comparison_direction_ready = (
        signal_available
        and signal.advantage
        in _SCORING_DIRECTIONAL_ADVANTAGES
    )

    candidate_identity_ready = (
        bool(signal.first_candidate_ref)
        and bool(signal.second_candidate_ref)
        and (
            signal.first_candidate_ref
            != signal.second_candidate_ref
        )
    )

    landed_cost_values_ready = (
        signal.first_landed_cost >= 0
        and signal.second_landed_cost >= 0
    )

    currency_ready = (
        len(signal.currency) == 3
        and signal.currency.isalpha()
        and signal.currency.isupper()
    )

    evidence_quality_ready = (
        signal.first_evidence_quality
        in _ACCEPTABLE_EVIDENCE_QUALITIES
        and signal.second_evidence_quality
        in _ACCEPTABLE_EVIDENCE_QUALITIES
    )

    source_contract_ready = (
        bool(signal.source_schema_id)
        and bool(signal.source_schema_version)
    )

    checks = {
        "signal_available": signal_available,
        "comparison_direction": (
            comparison_direction_ready
        ),
        "candidate_identity": candidate_identity_ready,
        "landed_cost_values": landed_cost_values_ready,
        "currency": currency_ready,
        "evidence_quality": evidence_quality_ready,
        "source_contract": source_contract_ready,
    }

    reasons = tuple(
        name
        for name, ready in checks.items()
        if not ready
    )

    state = (
        CrossBorderScoringReadinessState.READY
        if not reasons
        else CrossBorderScoringReadinessState.NOT_READY
    )

    return CrossBorderScoringReadiness(
        state=state,
        signal_available=signal_available,
        comparison_direction_ready=(
            comparison_direction_ready
        ),
        candidate_identity_ready=candidate_identity_ready,
        landed_cost_values_ready=landed_cost_values_ready,
        currency_ready=currency_ready,
        evidence_quality_ready=evidence_quality_ready,
        source_contract_ready=source_contract_ready,
        reasons=reasons,
    )
