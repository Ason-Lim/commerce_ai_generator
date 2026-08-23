from __future__ import annotations

from decimal import Decimal

import pytest

import app.services.recommendation.cross_border_aligned_scoring_policy_adoption_readiness as module
from app.services.recommendation.cross_border_aligned_scoring_policy_adoption_readiness import (
    AlignedCrossBorderPolicyAdoptionReadiness,
    AlignedCrossBorderPolicyAdoptionReadinessState,
    evaluate_aligned_cross_border_policy_adoption_readiness,
)
from app.services.recommendation.cross_border_aligned_scoring_policy_comparison import (
    AlignedCrossBorderScoringPolicyComparison,
    AlignedCrossBorderScoringPolicyComparisonState,
)
from app.services.recommendation.cross_border_scoring_policy_adoption_readiness import (
    CrossBorderPolicyAdoptionReadiness,
    CrossBorderPolicyAdoptionReadinessState,
)
from app.services.recommendation.cross_border_scoring_policy_comparison import (
    CrossBorderPolicyComparisonState,
    CrossBorderScoringPolicyComparison,
)


def _comparison() -> CrossBorderScoringPolicyComparison:
    return CrossBorderScoringPolicyComparison(
        state=CrossBorderPolicyComparisonState.COMPARABLE,
        baseline_policy_id="baseline-v1",
        candidate_policy_id="candidate-v2",
        first_candidate_ref="candidate-a",
        second_candidate_ref="candidate-b",
        first_delta_difference=Decimal("1.25"),
        second_delta_difference=Decimal("2.50"),
        candidate_identity_aligned=True,
        direction_aligned=True,
        shadow_mode_aligned=True,
        policy_roles_valid=True,
        reasons=(),
    )


def _aligned(
    *,
    state: AlignedCrossBorderScoringPolicyComparisonState,
    comparison: CrossBorderScoringPolicyComparison | None,
) -> AlignedCrossBorderScoringPolicyComparison:
    # Upstream aligned evaluation objects are deliberately irrelevant
    # to this enforcement boundary after C4S has produced its result.
    return AlignedCrossBorderScoringPolicyComparison(
        state=state,
        baseline=None,  # type: ignore[arg-type]
        candidate=None,  # type: ignore[arg-type]
        comparison=comparison,
        reasons=(
            ()
            if state
            is AlignedCrossBorderScoringPolicyComparisonState.AVAILABLE
            else ("blocked_for_test",)
        ),
    )


def test_available_aligned_comparison_delegates_exact_nested_comparison(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    canonical = _comparison()
    aligned = _aligned(
        state=AlignedCrossBorderScoringPolicyComparisonState.AVAILABLE,
        comparison=canonical,
    )
    captured: list[CrossBorderScoringPolicyComparison] = []

    expected = CrossBorderPolicyAdoptionReadiness(
        state=CrossBorderPolicyAdoptionReadinessState.READY,
        baseline_policy_id="baseline-v1",
        candidate_policy_id="candidate-v2",
        comparison_ready=True,
        policy_identity_ready=True,
        delta_evidence_ready=True,
        candidate_identity_ready=True,
        direction_ready=True,
        shadow_evidence_ready=True,
        policy_roles_ready=True,
        reasons=(),
    )

    def fake_authority(
        comparison: CrossBorderScoringPolicyComparison,
    ) -> CrossBorderPolicyAdoptionReadiness:
        captured.append(comparison)
        return expected

    monkeypatch.setattr(
        module,
        "evaluate_cross_border_policy_adoption_readiness",
        fake_authority,
    )

    result = evaluate_aligned_cross_border_policy_adoption_readiness(
        aligned
    )

    assert captured == [canonical]
    assert captured[0] is canonical
    assert result.state is (
        AlignedCrossBorderPolicyAdoptionReadinessState.AVAILABLE
    )
    assert result.aligned_comparison is aligned
    assert result.readiness is expected
    assert result.reasons == ()


def test_blocked_aligned_comparison_does_not_invoke_readiness_authority(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    aligned = _aligned(
        state=AlignedCrossBorderScoringPolicyComparisonState.BLOCKED,
        comparison=None,
    )

    def forbidden(*args: object, **kwargs: object) -> object:
        raise AssertionError(
            "canonical adoption-readiness authority was invoked"
        )

    monkeypatch.setattr(
        module,
        "evaluate_cross_border_policy_adoption_readiness",
        forbidden,
    )

    result = evaluate_aligned_cross_border_policy_adoption_readiness(
        aligned
    )

    assert result.state is (
        AlignedCrossBorderPolicyAdoptionReadinessState.BLOCKED
    )
    assert result.readiness is None
    assert result.reasons == (
        "aligned_policy_comparison_not_available",
    )


def test_available_without_nested_comparison_fails_closed() -> None:
    aligned = _aligned(
        state=AlignedCrossBorderScoringPolicyComparisonState.AVAILABLE,
        comparison=None,
    )

    with pytest.raises(
        ValueError,
        match="must contain comparison",
    ):
        evaluate_aligned_cross_border_policy_adoption_readiness(
            aligned
        )


def test_result_contract_is_frozen() -> None:
    result = evaluate_aligned_cross_border_policy_adoption_readiness(
        _aligned(
            state=AlignedCrossBorderScoringPolicyComparisonState.AVAILABLE,
            comparison=_comparison(),
        )
    )

    with pytest.raises(Exception):
        result.reasons = ("mutated",)  # type: ignore[misc]


def test_available_property_true_for_available() -> None:
    result = evaluate_aligned_cross_border_policy_adoption_readiness(
        _aligned(
            state=AlignedCrossBorderScoringPolicyComparisonState.AVAILABLE,
            comparison=_comparison(),
        )
    )

    assert result.is_available is True


def test_available_property_false_for_blocked() -> None:
    result = evaluate_aligned_cross_border_policy_adoption_readiness(
        _aligned(
            state=AlignedCrossBorderScoringPolicyComparisonState.BLOCKED,
            comparison=None,
        )
    )

    assert result.is_available is False


def test_real_canonical_ready_result_is_preserved() -> None:
    result = evaluate_aligned_cross_border_policy_adoption_readiness(
        _aligned(
            state=AlignedCrossBorderScoringPolicyComparisonState.AVAILABLE,
            comparison=_comparison(),
        )
    )

    assert result.readiness is not None
    assert result.readiness.state is (
        CrossBorderPolicyAdoptionReadinessState.READY
    )
    assert result.readiness.baseline_policy_id == "baseline-v1"
    assert result.readiness.candidate_policy_id == "candidate-v2"


def test_blocked_result_preserves_exact_aligned_input() -> None:
    aligned = _aligned(
        state=AlignedCrossBorderScoringPolicyComparisonState.BLOCKED,
        comparison=None,
    )

    result = evaluate_aligned_cross_border_policy_adoption_readiness(
        aligned
    )

    assert result.aligned_comparison is aligned


def test_result_type_is_explicit() -> None:
    result = evaluate_aligned_cross_border_policy_adoption_readiness(
        _aligned(
            state=AlignedCrossBorderScoringPolicyComparisonState.AVAILABLE,
            comparison=_comparison(),
        )
    )

    assert isinstance(
        result,
        AlignedCrossBorderPolicyAdoptionReadiness,
    )
