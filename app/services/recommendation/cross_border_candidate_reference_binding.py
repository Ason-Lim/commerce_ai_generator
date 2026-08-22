from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CrossBorderCandidateReferenceBinding:
    """
    Explicit Recommendation-side binding for one opaque
    Cross-Border candidate reference.

    ``candidate_ref`` is owned by the Cross-Border handoff boundary.
    ``candidate_position`` identifies only an explicitly supplied
    Recommendation candidate sequence position.

    This contract does not claim or infer:

    - canonical product identity;
    - Recommendation product_id identity;
    - product_identity_key identity;
    - marketplace listing identity;
    - offer identity;
    - product URL identity;
    - ranking identity.

    It also does not score, rank, select, recommend, route traffic,
    activate policy behavior, or execute a transaction.

    This object represents exactly one explicit binding. It does not
    validate uniqueness, completeness, or conflicts across multiple
    bindings. Those concerns belong to a higher-level binding-set
    contract.
    """

    candidate_ref: str
    candidate_position: int
    binding_source: str

    def __post_init__(self) -> None:
        candidate_ref = self.candidate_ref.strip()
        binding_source = self.binding_source.strip()

        if not candidate_ref:
            raise ValueError(
                "candidate_ref must be non-empty"
            )

        if self.candidate_position <= 0:
            raise ValueError(
                "candidate_position must be greater than zero"
            )

        if not binding_source:
            raise ValueError(
                "binding_source must be non-empty"
            )

        object.__setattr__(
            self,
            "candidate_ref",
            candidate_ref,
        )
        object.__setattr__(
            self,
            "binding_source",
            binding_source,
        )


def bind_cross_border_candidate_reference(
    *,
    candidate_ref: str,
    candidate_position: int,
    binding_source: str,
) -> CrossBorderCandidateReferenceBinding:
    """
    Create one explicit opaque-reference binding.

    The caller must already know the relationship between the
    Cross-Border reference and the Recommendation candidate sequence
    position.

    No relationship is inferred from product_id, identity keys,
    URLs, marketplace fields, offer fields, or ranking state.
    """

    return CrossBorderCandidateReferenceBinding(
        candidate_ref=candidate_ref,
        candidate_position=candidate_position,
        binding_source=binding_source,
    )
