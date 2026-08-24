from unittest.mock import patch

from app.services.recommendation.cross_border_aligned_scoring_policy_fallback import (
    AlignedCrossBorderScoringFallback,
    AlignedCrossBorderScoringFallbackState,
)
from app.services.recommendation.cross_border_aligned_scoring_runtime_authority_source import (
    RuntimeAuthoritySource,
    RuntimeAuthoritySourceState,
)
from app.services.recommendation.cross_border_production_provider_composition import (
    compose_production_recommendation_provider,
)


def _blocked_source():
    return RuntimeAuthoritySource(
        state=RuntimeAuthoritySourceState.BLOCKED,
        authority=None,
        reasons=("blocked",),
    )


def _available_source():
    authority = AlignedCrossBorderScoringFallback(
        state=AlignedCrossBorderScoringFallbackState.AVAILABLE,
        aligned_boundary=None,
        fallback=object(),
        reasons=(),
    )
    return RuntimeAuthoritySource(
        state=RuntimeAuthoritySourceState.AVAILABLE,
        authority=authority,
        reasons=(),
    )


def test_missing_authority_preserves_default_provider_construction():
    with patch(
        "app.services.recommendation."
        "cross_border_production_provider_composition."
        "RecommendationProvider"
    ) as provider_cls:
        provider = compose_production_recommendation_provider()

    provider_cls.assert_called_once_with()
    assert provider is provider_cls.return_value


def test_blocked_authority_preserves_default_provider_construction():
    with patch(
        "app.services.recommendation."
        "cross_border_production_provider_composition."
        "RecommendationProvider"
    ) as provider_cls:
        provider = compose_production_recommendation_provider(
            _blocked_source()
        )

    provider_cls.assert_called_once_with()
    assert provider is provider_cls.return_value


def test_available_authority_uses_existing_runtime_scorer_composition():
    expected_scorer = object()

    with patch(
        "app.services.recommendation."
        "cross_border_production_provider_composition."
        "compose_aligned_cross_border_runtime_scorer",
        return_value=expected_scorer,
    ) as compose_scorer, patch(
        "app.services.recommendation."
        "cross_border_production_provider_composition."
        "RecommendationProvider"
    ) as provider_cls:
        source = _available_source()

        provider = compose_production_recommendation_provider(
            source
        )

    compose_scorer.assert_called_once_with(
        source.authority,
        candidate_scorer=None,
    )
    provider_cls.assert_called_once_with(
        scorer=expected_scorer
    )
    assert provider is provider_cls.return_value


def test_candidate_scorer_is_only_forwarded_to_existing_composition():
    candidate_scorer = object()
    expected_scorer = object()

    with patch(
        "app.services.recommendation."
        "cross_border_production_provider_composition."
        "compose_aligned_cross_border_runtime_scorer",
        return_value=expected_scorer,
    ) as compose_scorer, patch(
        "app.services.recommendation."
        "cross_border_production_provider_composition."
        "RecommendationProvider"
    ):
        source = _available_source()

        compose_production_recommendation_provider(
            source,
            candidate_scorer=candidate_scorer,
        )

    compose_scorer.assert_called_once_with(
        source.authority,
        candidate_scorer=candidate_scorer,
    )


def test_blocked_authority_never_calls_runtime_scorer_composition():
    with patch(
        "app.services.recommendation."
        "cross_border_production_provider_composition."
        "compose_aligned_cross_border_runtime_scorer"
    ) as compose_scorer:
        compose_production_recommendation_provider(
            _blocked_source()
        )

    compose_scorer.assert_not_called()
