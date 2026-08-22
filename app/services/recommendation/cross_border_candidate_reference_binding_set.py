from __future__ import annotations

from dataclasses import dataclass

from app.services.recommendation.cross_border_candidate_reference_binding import (
    CrossBorderCandidateReferenceBinding,
)


@dataclass(frozen=True)
class CrossBorderCandidateReferenceBindingSet:
    """
    Validated Recommendation-side binding set for the current
    two-candidate Cross-Border comparison handoff.

    This contract owns set-level structural validation only.

    A valid set:
    - contains exactly two explicit bindings;
    - contains two distinct candidate references;
    - contains two distinct candidate positions;
    - covers Recommendation candidate positions 1 and 2.

    Input order is preserved. Tuple order does not define candidate
    position; each binding's explicit candidate_position does.

    This contract does not infer product identity from candidate_ref.
    It also does not score, rank, select, recommend, route traffic,
    activate policy behavior, or execute a transaction.
    """

    bindings: tuple[
        CrossBorderCandidateReferenceBinding,
        ...,
    ]

    def __post_init__(self) -> None:
        bindings = tuple(self.bindings)

        if len(bindings) != 2:
            raise ValueError(
                "binding set must contain exactly two bindings"
            )

        candidate_refs = tuple(
            binding.candidate_ref
            for binding in bindings
        )

        if len(set(candidate_refs)) != 2:
            raise ValueError(
                "candidate_ref values must be unique"
            )

        candidate_positions = tuple(
            binding.candidate_position
            for binding in bindings
        )

        if len(set(candidate_positions)) != 2:
            raise ValueError(
                "candidate_position values must be unique"
            )

        if set(candidate_positions) != {1, 2}:
            raise ValueError(
                "candidate_position values must cover positions 1 and 2"
            )

        object.__setattr__(
            self,
            "bindings",
            bindings,
        )


def validate_cross_border_candidate_reference_bindings(
    bindings: tuple[
        CrossBorderCandidateReferenceBinding,
        ...,
    ],
) -> CrossBorderCandidateReferenceBindingSet:
    """
    Validate one explicit two-binding Cross-Border reference set.

    No binding is synthesized, reordered, matched by product identity,
    or inferred from Recommendation or marketplace fields.
    """

    return CrossBorderCandidateReferenceBindingSet(
        bindings=tuple(bindings),
    )
