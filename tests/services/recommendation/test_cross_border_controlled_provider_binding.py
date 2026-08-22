from __future__ import annotations

from copy import deepcopy

from app.services.recommendation.context import (
    build_recommendation_context,
)
from app.services.recommendation.cross_border_controlled_scoring import (
    ControlledScoringPath,
    calculate_controlled_recommendation_score,
)
from app.services.recommendation.cross_border_scoring_policy_fallback import (
    CrossBorderScoringFallbackDecision,
    CrossBorderScoringFallbackTarget,
)
from app.services.recommendation.models import (
    RecommendationScoreResult,
)
from app.services.recommendation.parser import (
    parse_recommendation_query,
)
from app.services.recommendation.policy import (
    resolve_recommendation_policy,
)
from app.services.recommendation.provider import (
    RecommendationProvider,
)
from app.services.recommendation.scoring import (
    calculate_recommendation_score,
)


def _items() -> list[dict[str, object]]:
    return [
        {
            "name": "A",
            "price": 10000,
            "fruit_quality_score": 80.0,
        },
        {
            "name": "B",
            "price": 12000,
            "fruit_quality_score": 70.0,
        },
    ]


def _passthrough(
    items: list[dict[str, object]],
) -> list[dict[str, object]]:
    return list(items)


def _context():
    return build_recommendation_context(
        parse_recommendation_query(
            "사과"
        ),
        resolve_recommendation_policy(
            "quality"
        ),
    )


def _provider(
    *,
    scorer=calculate_recommendation_score,
) -> RecommendationProvider:
    return RecommendationProvider(
        collector=lambda query, limit: deepcopy(
            _items()
        ),
        deduplicator=_passthrough,
        normalizer=_passthrough,
        food_enricher=_passthrough,
        scorer=scorer,
    )


def _candidate_decision(
) -> CrossBorderScoringFallbackDecision:
    return CrossBorderScoringFallbackDecision(
        target=(
            CrossBorderScoringFallbackTarget.CANDIDATE
        ),
        baseline_policy_id="canonical-v8",
        candidate_policy_id="cross-border-candidate-v1",
        fallback_required=False,
        activation_allowed=True,
        boundary_eligible=True,
        policy_identity_ready=True,
        authority_identity_ready=True,
        activation_state_safe=True,
        fallback_reason=None,
    )


def _baseline_decision(
) -> CrossBorderScoringFallbackDecision:
    return CrossBorderScoringFallbackDecision(
        target=(
            CrossBorderScoringFallbackTarget.BASELINE
        ),
        baseline_policy_id="canonical-v8",
        candidate_policy_id="cross-border-candidate-v1",
        fallback_required=True,
        activation_allowed=False,
        boundary_eligible=False,
        policy_identity_ready=True,
        authority_identity_ready=True,
        activation_state_safe=True,
        fallback_reason="boundary",
    )


def test_default_provider_preserves_canonical_scoring(
) -> None:
    baseline = _provider().recommend(
        _context()
    )

    explicit = _provider(
        scorer=calculate_recommendation_score
    ).recommend(
        _context()
    )

    assert baseline == explicit


def test_provider_invokes_injected_scorer(
) -> None:
    calls: list[object] = []

    def scorer(
        components,
        priority,
    ) -> RecommendationScoreResult:
        calls.append(
            (
                components,
                priority,
            )
        )
        return calculate_recommendation_score(
            components,
            priority,
        )

    result = _provider(
        scorer=scorer
    ).recommend(
        _context()
    )

    assert len(calls) == 2
    assert len(result.candidates) == 2


def test_controlled_baseline_binding_preserves_result(
) -> None:
    baseline = _provider().recommend(
        _context()
    )

    decision = _baseline_decision()

    def controlled(
        components,
        priority,
    ) -> RecommendationScoreResult:
        return (
            calculate_controlled_recommendation_score(
                components,
                priority,
                fallback=decision,
            ).score
        )

    controlled_result = _provider(
        scorer=controlled
    ).recommend(
        _context()
    )

    assert controlled_result == baseline


def test_controlled_candidate_binding_reaches_candidate_path(
) -> None:
    observed_paths: list[
        ControlledScoringPath
    ] = []

    decision = _candidate_decision()

    def candidate(
        components,
        priority,
    ) -> RecommendationScoreResult:
        return calculate_recommendation_score(
            components,
            priority,
        )

    def controlled(
        components,
        priority,
    ) -> RecommendationScoreResult:
        result = (
            calculate_controlled_recommendation_score(
                components,
                priority,
                fallback=decision,
                candidate_scorer=candidate,
            )
        )

        observed_paths.append(
            result.path
        )

        return result.score

    result = _provider(
        scorer=controlled
    ).recommend(
        _context()
    )

    assert len(result.candidates) == 2
    assert observed_paths == [
        ControlledScoringPath.CANDIDATE,
        ControlledScoringPath.CANDIDATE,
    ]


def test_controlled_candidate_failure_falls_back(
) -> None:
    baseline = _provider().recommend(
        _context()
    )

    decision = _candidate_decision()

    def broken_candidate(
        components,
        priority,
    ) -> RecommendationScoreResult:
        raise RuntimeError(
            "candidate failure"
        )

    observed_paths: list[
        ControlledScoringPath
    ] = []

    def controlled(
        components,
        priority,
    ) -> RecommendationScoreResult:
        result = (
            calculate_controlled_recommendation_score(
                components,
                priority,
                fallback=decision,
                candidate_scorer=broken_candidate,
            )
        )

        observed_paths.append(
            result.path
        )

        return result.score

    controlled_result = _provider(
        scorer=controlled
    ).recommend(
        _context()
    )

    assert controlled_result == baseline

    assert observed_paths == [
        ControlledScoringPath.BASELINE,
        ControlledScoringPath.BASELINE,
    ]
