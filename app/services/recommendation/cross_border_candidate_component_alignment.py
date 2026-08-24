from __future__ import annotations

from dataclasses import dataclass

from app.services.recommendation.cross_border_bound_price_signal_composition import (
    BoundCrossBorderPriceSignals,
)
from app.services.recommendation.scoring import (
    RecommendationScoreComponents,
)


@dataclass(frozen=True)
class CrossBorderCandidateComponentBinding:
    """
    Explicit Recommendation-owned alignment between a Cross-Border
    candidate reference and that candidate's canonical base scoring
    components.

    candidate_ref remains a Cross-Border handoff identity. This
    contract does not reinterpret it as canonical product identity.
    """

    candidate_ref: str
    base_components: RecommendationScoreComponents

    def __post_init__(self) -> None:
        candidate_ref = self.candidate_ref.strip()
        if not candidate_ref:
            raise ValueError(
                "candidate_ref must be non-empty"
            )

        object.__setattr__(
            self,
            "candidate_ref",
            candidate_ref,
        )


@dataclass(frozen=True)
class AlignedCrossBorderCandidateComponents:
    """
    Pairwise candidate-component alignment for bounded Cross-Border
    price evidence.

    The derived components preserve every canonical non-price axis
    from each candidate and replace only the price axis with the
    aligned Cross-Border price utility.

    This contract does not score, rank, select, activate production
    traffic, infer product identity, or mutate base components.
    """

    first_candidate_ref: str
    second_candidate_ref: str
    first_base_components: RecommendationScoreComponents
    second_base_components: RecommendationScoreComponents
    first_components: RecommendationScoreComponents
    second_components: RecommendationScoreComponents


def _derive_price_components(
    *,
    base: RecommendationScoreComponents,
    price: float,
) -> RecommendationScoreComponents:
    available = set(base.available)
    available.add("price")

    return RecommendationScoreComponents(
        quality=base.quality,
        price=price,
        trust=base.trust,
        popularity=base.popularity,
        market=base.market,
        identity=base.identity,
        available=frozenset(available),
    )


def align_cross_border_candidate_components(
    *,
    price_signals: BoundCrossBorderPriceSignals,
    first_binding: CrossBorderCandidateComponentBinding,
    second_binding: CrossBorderCandidateComponentBinding,
) -> AlignedCrossBorderCandidateComponents:
    scoring_input = price_signals.scoring_input

    if (
        first_binding.candidate_ref
        != scoring_input.first_candidate_ref
    ):
        raise ValueError(
            "first candidate_ref does not match bound scoring input"
        )

    if (
        second_binding.candidate_ref
        != scoring_input.second_candidate_ref
    ):
        raise ValueError(
            "second candidate_ref does not match bound scoring input"
        )

    if (
        first_binding.candidate_ref
        == second_binding.candidate_ref
    ):
        raise ValueError(
            "candidate_ref values must be unique"
        )

    first_components = _derive_price_components(
        base=first_binding.base_components,
        price=price_signals.first_price.utility,
    )
    second_components = _derive_price_components(
        base=second_binding.base_components,
        price=price_signals.second_price.utility,
    )

    return AlignedCrossBorderCandidateComponents(
        first_candidate_ref=first_binding.candidate_ref,
        second_candidate_ref=second_binding.candidate_ref,
        first_base_components=first_binding.base_components,
        second_base_components=second_binding.base_components,
        first_components=first_components,
        second_components=second_components,
    )
