from __future__ import annotations

from dataclasses import dataclass
import re

from app.services.cross_border.recommendation_handoff import (
    RecommendationHandoffEvidence,
)


RECOMMENDATION_HANDOFF_SCHEMA_ID = (
    "commerce_ai.cross_border.recommendation_handoff"
)

RECOMMENDATION_HANDOFF_SCHEMA_VERSION = "1.0"


_VERSION_PATTERN = re.compile(
    r"^(?P<major>0|[1-9][0-9]*)\."
    r"(?P<minor>0|[1-9][0-9]*)$"
)


def _parse_schema_version(
    version: str,
) -> tuple[int, int]:
    normalized = version.strip()

    match = _VERSION_PATTERN.fullmatch(
        normalized
    )

    if match is None:
        raise ValueError(
            "schema_version must use '<major>.<minor>' format"
        )

    return (
        int(match.group("major")),
        int(match.group("minor")),
    )


@dataclass(frozen=True)
class RecommendationHandoffContractIdentity:
    """
    Immutable identity metadata for the Cross-Border outbound
    recommendation handoff contract.

    Identity and compatibility metadata do not grant ranking,
    recommendation, selection, or transaction authority.
    """

    schema_id: str = RECOMMENDATION_HANDOFF_SCHEMA_ID
    schema_version: str = (
        RECOMMENDATION_HANDOFF_SCHEMA_VERSION
    )

    def __post_init__(self) -> None:
        schema_id = self.schema_id.strip()
        schema_version = self.schema_version.strip()

        if not schema_id:
            raise ValueError(
                "schema_id must be non-empty"
            )

        _parse_schema_version(
            schema_version
        )

        object.__setattr__(
            self,
            "schema_id",
            schema_id,
        )

        object.__setattr__(
            self,
            "schema_version",
            schema_version,
        )

    @property
    def major_version(self) -> int:
        major, _ = _parse_schema_version(
            self.schema_version
        )

        return major

    @property
    def minor_version(self) -> int:
        _, minor = _parse_schema_version(
            self.schema_version
        )

        return minor

    def is_compatible_with(
        self,
        other: RecommendationHandoffContractIdentity,
    ) -> bool:
        """
        Compatibility is intentionally bounded:

        - schema IDs must match exactly;
        - major versions must match.

        Minor-version evolution is therefore allowed within the same
        schema family.

        This method does not validate consumer behavior.
        """

        return (
            self.schema_id
            == other.schema_id
            and self.major_version
            == other.major_version
        )


@dataclass(frozen=True)
class VersionedRecommendationHandoff:
    """
    Phase 10A handoff evidence paired with explicit contract identity.

    This envelope contains evidence and schema metadata only.
    """

    contract: RecommendationHandoffContractIdentity
    evidence: RecommendationHandoffEvidence


def version_recommendation_handoff(
    evidence: RecommendationHandoffEvidence,
    *,
    contract: (
        RecommendationHandoffContractIdentity
        | None
    ) = None,
) -> VersionedRecommendationHandoff:
    """
    Attach explicit contract identity to outbound handoff evidence.

    No ranking, recommendation, candidate selection, user-preference
    weighting, or downstream invocation is performed.
    """

    identity = (
        contract
        if contract is not None
        else RecommendationHandoffContractIdentity()
    )

    return VersionedRecommendationHandoff(
        contract=identity,
        evidence=evidence,
    )
