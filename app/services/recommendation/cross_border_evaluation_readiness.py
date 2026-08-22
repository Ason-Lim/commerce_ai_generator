from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.services.recommendation.cross_border_evidence import (
    CanonicalCrossBorderRecommendationEvidence,
)


class CrossBorderEvaluationReadinessState(
    str,
    Enum,
):
    READY = "ready"
    NOT_READY = "not_ready"


@dataclass(frozen=True)
class CrossBorderEvaluationReadiness:
    """
    Recommendation-side readiness result for canonical Cross-Border
    evidence.

    READY means only that the evidence contains the minimum bounded
    information required for a future Recommendation evaluation
    stage.

    READY does not rank, score, recommend, select, or prefer either
    candidate.
    """

    state: CrossBorderEvaluationReadinessState

    candidate_identity_ready: bool
    landed_cost_ready: bool
    currency_ready: bool
    route_context_ready: bool
    evidence_quality_ready: bool
    source_contract_ready: bool

    reasons: tuple[str, ...]


_SUPPORTED_RELATIONS = {
    "first_less",
    "second_less",
    "equal",
    "not_comparable",
}

_ACCEPTABLE_EVIDENCE_QUALITIES = {
    "known",
    "estimated",
}


def evaluate_cross_border_readiness(
    evidence: CanonicalCrossBorderRecommendationEvidence,
) -> CrossBorderEvaluationReadiness:
    """
    Evaluate whether canonical Cross-Border evidence is structurally
    ready for a later Recommendation evaluation stage.

    This function does not calculate a recommendation score and does
    not express candidate preference.
    """

    candidate_identity_ready = (
        bool(evidence.first_candidate_ref)
        and bool(evidence.second_candidate_ref)
        and (
            evidence.first_candidate_ref
            != evidence.second_candidate_ref
        )
    )

    landed_cost_ready = (
        evidence.first_landed_cost >= 0
        and evidence.second_landed_cost >= 0
        and evidence.landed_cost_relation
        in _SUPPORTED_RELATIONS
    )

    currency_ready = (
        len(evidence.currency) == 3
        and evidence.currency.isalpha()
        and evidence.currency.isupper()
    )

    route_context_ready = (
        len(evidence.origin_country) == 2
        and len(evidence.destination_country) == 2
        and evidence.origin_country.isalpha()
        and evidence.destination_country.isalpha()
        and evidence.origin_country.isupper()
        and evidence.destination_country.isupper()
        and (
            evidence.origin_country
            != evidence.destination_country
        )
    )

    evidence_quality_ready = (
        evidence.first_evidence_quality
        in _ACCEPTABLE_EVIDENCE_QUALITIES
        and evidence.second_evidence_quality
        in _ACCEPTABLE_EVIDENCE_QUALITIES
    )

    source_contract_ready = (
        bool(evidence.source_schema_id)
        and bool(evidence.source_schema_version)
    )

    checks = {
        "candidate_identity": candidate_identity_ready,
        "landed_cost": landed_cost_ready,
        "currency": currency_ready,
        "route_context": route_context_ready,
        "evidence_quality": evidence_quality_ready,
        "source_contract": source_contract_ready,
    }

    reasons = tuple(
        name
        for name, ready in checks.items()
        if not ready
    )

    state = (
        CrossBorderEvaluationReadinessState.READY
        if not reasons
        else CrossBorderEvaluationReadinessState.NOT_READY
    )

    return CrossBorderEvaluationReadiness(
        state=state,
        candidate_identity_ready=candidate_identity_ready,
        landed_cost_ready=landed_cost_ready,
        currency_ready=currency_ready,
        route_context_ready=route_context_ready,
        evidence_quality_ready=evidence_quality_ready,
        source_contract_ready=source_contract_ready,
        reasons=reasons,
    )
