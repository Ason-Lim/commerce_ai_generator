from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from app.services.recommendation.cross_border_handoff import (
    CrossBorderHandoffInbound,
    CrossBorderHandoffInboundState,
)


@dataclass(frozen=True)
class CanonicalCrossBorderRecommendationEvidence:
    """
    Recommendation-owned canonical representation of accepted
    Cross-Border comparison evidence.

    Cross-Border producer objects are translated into immutable
    Recommendation-side values at this boundary.

    This evidence does not perform ranking, scoring,
    recommendation, candidate selection, preference weighting,
    or transaction execution.
    """

    first_candidate_ref: str
    second_candidate_ref: str

    landed_cost_relation: str

    first_landed_cost: Decimal
    second_landed_cost: Decimal

    currency: str

    origin_country: str
    destination_country: str

    first_evidence_quality: str
    second_evidence_quality: str

    source_schema_id: str
    source_schema_version: str

    def __post_init__(self) -> None:
        first_candidate_ref = (
            self.first_candidate_ref.strip()
        )
        second_candidate_ref = (
            self.second_candidate_ref.strip()
        )
        landed_cost_relation = (
            self.landed_cost_relation.strip()
        )
        currency = self.currency.strip().upper()
        origin_country = (
            self.origin_country.strip().upper()
        )
        destination_country = (
            self.destination_country.strip().upper()
        )
        first_evidence_quality = (
            self.first_evidence_quality.strip()
        )
        second_evidence_quality = (
            self.second_evidence_quality.strip()
        )
        source_schema_id = (
            self.source_schema_id.strip()
        )
        source_schema_version = (
            self.source_schema_version.strip()
        )

        required = {
            "first_candidate_ref": first_candidate_ref,
            "second_candidate_ref": second_candidate_ref,
            "landed_cost_relation": landed_cost_relation,
            "currency": currency,
            "origin_country": origin_country,
            "destination_country": destination_country,
            "first_evidence_quality": (
                first_evidence_quality
            ),
            "second_evidence_quality": (
                second_evidence_quality
            ),
            "source_schema_id": source_schema_id,
            "source_schema_version": (
                source_schema_version
            ),
        }

        blank = [
            name
            for name, value in required.items()
            if not value
        ]

        if blank:
            raise ValueError(
                "canonical cross-border evidence contains "
                "blank required values: "
                + ", ".join(sorted(blank))
            )

        first_landed_cost = Decimal(
            str(self.first_landed_cost)
        )
        second_landed_cost = Decimal(
            str(self.second_landed_cost)
        )

        if first_landed_cost < 0:
            raise ValueError(
                "first_landed_cost must be non-negative"
            )

        if second_landed_cost < 0:
            raise ValueError(
                "second_landed_cost must be non-negative"
            )

        object.__setattr__(
            self,
            "first_candidate_ref",
            first_candidate_ref,
        )
        object.__setattr__(
            self,
            "second_candidate_ref",
            second_candidate_ref,
        )
        object.__setattr__(
            self,
            "landed_cost_relation",
            landed_cost_relation,
        )
        object.__setattr__(
            self,
            "first_landed_cost",
            first_landed_cost,
        )
        object.__setattr__(
            self,
            "second_landed_cost",
            second_landed_cost,
        )
        object.__setattr__(
            self,
            "currency",
            currency,
        )
        object.__setattr__(
            self,
            "origin_country",
            origin_country,
        )
        object.__setattr__(
            self,
            "destination_country",
            destination_country,
        )
        object.__setattr__(
            self,
            "first_evidence_quality",
            first_evidence_quality,
        )
        object.__setattr__(
            self,
            "second_evidence_quality",
            second_evidence_quality,
        )
        object.__setattr__(
            self,
            "source_schema_id",
            source_schema_id,
        )
        object.__setattr__(
            self,
            "source_schema_version",
            source_schema_version,
        )


def build_canonical_cross_border_evidence(
    inbound: CrossBorderHandoffInbound,
) -> CanonicalCrossBorderRecommendationEvidence:
    """
    Translate an accepted R1A inbound handoff into immutable,
    Recommendation-owned canonical evidence.

    A rejected or evidence-less inbound result cannot cross this
    boundary.

    No ranking or recommendation semantics are introduced.
    """

    if (
        inbound.state
        is not CrossBorderHandoffInboundState.ACCEPTED
    ):
        raise ValueError(
            "cross-border inbound handoff is not accepted"
        )

    evidence = inbound.evidence

    if evidence is None:
        raise ValueError(
            "accepted cross-border inbound evidence is missing"
        )

    return CanonicalCrossBorderRecommendationEvidence(
        first_candidate_ref=(
            evidence.first_candidate_ref
        ),
        second_candidate_ref=(
            evidence.second_candidate_ref
        ),
        landed_cost_relation=(
            evidence.relation.value
        ),
        first_landed_cost=(
            evidence.first_total
        ),
        second_landed_cost=(
            evidence.second_total
        ),
        currency=evidence.currency,
        origin_country=(
            evidence.context.origin_country
        ),
        destination_country=(
            evidence.context.destination_country
        ),
        first_evidence_quality=(
            evidence.first_quality.value
        ),
        second_evidence_quality=(
            evidence.second_quality.value
        ),
        source_schema_id=inbound.schema_id,
        source_schema_version=(
            inbound.schema_version
        ),
    )
