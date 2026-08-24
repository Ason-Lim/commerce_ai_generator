from __future__ import annotations

from dataclasses import dataclass

from app.services.recommendation.cross_border_provider_adjacent_result_orchestration import (
    compose_cross_border_provider_adjacent_result,
)
from app.services.recommendation.models import (
    RecommendationContext,
    RecommendationPriority,
)


@dataclass(frozen=True)
class SentinelResult:
    value: str


def _context() -> RecommendationContext:
    return RecommendationContext(
        query="한국 사과",
        priority=RecommendationPriority.PRICE,
        limit=2,
    )


def test_orchestration_binds_original_candidates_first(
    monkeypatch,
):
    calls = []

    reference_binding_set = object()
    candidates = (
        object(),
        object(),
    )
    original_bindings = object()
    ranked_candidates = (
        object(),
        object(),
    )
    ranked_pair = object()
    expected_result = SentinelResult(
        "result"
    )

    def fake_bind(
        *,
        reference_binding_set,
        candidates,
    ):
        calls.append("bind")
        assert (
            reference_binding_set
            is reference_binding_set_value
        )
        assert candidates is candidates_value
        return original_bindings

    def fake_rank(**kwargs):
        calls.append("rank")
        return ranked_candidates

    def fake_reconcile(**kwargs):
        calls.append("reconcile")
        return ranked_pair

    def fake_result(**kwargs):
        calls.append("result")
        return expected_result

    reference_binding_set_value = (
        reference_binding_set
    )
    candidates_value = candidates

    monkeypatch.setattr(
        "app.services.recommendation."
        "cross_border_provider_adjacent_result_orchestration."
        "bind_cross_border_original_candidate_set",
        fake_bind,
    )
    monkeypatch.setattr(
        "app.services.recommendation."
        "cross_border_provider_adjacent_result_orchestration."
        "rank_cross_border_candidate_pair",
        fake_rank,
    )
    monkeypatch.setattr(
        "app.services.recommendation."
        "cross_border_provider_adjacent_result_orchestration."
        "reconcile_cross_border_ranked_original_candidates",
        fake_reconcile,
    )
    monkeypatch.setattr(
        "app.services.recommendation."
        "cross_border_provider_adjacent_result_orchestration."
        "compose_cross_border_canonical_result",
        fake_result,
    )

    result = compose_cross_border_provider_adjacent_result(
        context=_context(),
        reference_binding_set=reference_binding_set,
        candidates=candidates,
        scores=object(),
        price_signals=object(),
        aligned_components=object(),
    )

    assert result is expected_result
    assert calls == [
        "bind",
        "rank",
        "reconcile",
        "result",
    ]


def test_context_priority_is_the_only_ranking_priority(
    monkeypatch,
):
    context = _context()
    captured = {}

    monkeypatch.setattr(
        "app.services.recommendation."
        "cross_border_provider_adjacent_result_orchestration."
        "bind_cross_border_original_candidate_set",
        lambda **kwargs: object(),
    )

    def fake_rank(
        *,
        scores,
        price_signals,
        aligned_components,
        priority,
    ):
        captured["priority"] = priority
        return (
            object(),
            object(),
        )

    monkeypatch.setattr(
        "app.services.recommendation."
        "cross_border_provider_adjacent_result_orchestration."
        "rank_cross_border_candidate_pair",
        fake_rank,
    )

    monkeypatch.setattr(
        "app.services.recommendation."
        "cross_border_provider_adjacent_result_orchestration."
        "reconcile_cross_border_ranked_original_candidates",
        lambda **kwargs: object(),
    )

    monkeypatch.setattr(
        "app.services.recommendation."
        "cross_border_provider_adjacent_result_orchestration."
        "compose_cross_border_canonical_result",
        lambda **kwargs: SentinelResult(
            "result"
        ),
    )

    compose_cross_border_provider_adjacent_result(
        context=context,
        reference_binding_set=object(),
        candidates=(
            object(),
            object(),
        ),
        scores=object(),
        price_signals=object(),
        aligned_components=object(),
    )

    assert (
        captured["priority"]
        is context.priority
    )


def test_reconciliation_receives_bound_originals_and_ranked_candidates(
    monkeypatch,
):
    original_bindings = object()
    ranked_candidates = (
        object(),
        object(),
    )
    captured = {}

    monkeypatch.setattr(
        "app.services.recommendation."
        "cross_border_provider_adjacent_result_orchestration."
        "bind_cross_border_original_candidate_set",
        lambda **kwargs: original_bindings,
    )

    monkeypatch.setattr(
        "app.services.recommendation."
        "cross_border_provider_adjacent_result_orchestration."
        "rank_cross_border_candidate_pair",
        lambda **kwargs: ranked_candidates,
    )

    def fake_reconcile(
        *,
        original_bindings,
        ranked_candidates,
    ):
        captured["original_bindings"] = (
            original_bindings
        )
        captured["ranked_candidates"] = (
            ranked_candidates
        )
        return object()

    monkeypatch.setattr(
        "app.services.recommendation."
        "cross_border_provider_adjacent_result_orchestration."
        "reconcile_cross_border_ranked_original_candidates",
        fake_reconcile,
    )

    monkeypatch.setattr(
        "app.services.recommendation."
        "cross_border_provider_adjacent_result_orchestration."
        "compose_cross_border_canonical_result",
        lambda **kwargs: SentinelResult(
            "result"
        ),
    )

    compose_cross_border_provider_adjacent_result(
        context=_context(),
        reference_binding_set=object(),
        candidates=(
            object(),
            object(),
        ),
        scores=object(),
        price_signals=object(),
        aligned_components=object(),
    )

    assert (
        captured["original_bindings"]
        is original_bindings
    )
    assert (
        captured["ranked_candidates"]
        is ranked_candidates
    )


def test_canonical_result_composition_receives_same_context(
    monkeypatch,
):
    context = _context()
    ranked_pair = object()
    captured = {}

    monkeypatch.setattr(
        "app.services.recommendation."
        "cross_border_provider_adjacent_result_orchestration."
        "bind_cross_border_original_candidate_set",
        lambda **kwargs: object(),
    )

    monkeypatch.setattr(
        "app.services.recommendation."
        "cross_border_provider_adjacent_result_orchestration."
        "rank_cross_border_candidate_pair",
        lambda **kwargs: (
            object(),
            object(),
        ),
    )

    monkeypatch.setattr(
        "app.services.recommendation."
        "cross_border_provider_adjacent_result_orchestration."
        "reconcile_cross_border_ranked_original_candidates",
        lambda **kwargs: ranked_pair,
    )

    def fake_result(
        *,
        context,
        ranked_pair,
    ):
        captured["context"] = context
        captured["ranked_pair"] = ranked_pair
        return SentinelResult(
            "result"
        )

    monkeypatch.setattr(
        "app.services.recommendation."
        "cross_border_provider_adjacent_result_orchestration."
        "compose_cross_border_canonical_result",
        fake_result,
    )

    result = compose_cross_border_provider_adjacent_result(
        context=context,
        reference_binding_set=object(),
        candidates=(
            object(),
            object(),
        ),
        scores=object(),
        price_signals=object(),
        aligned_components=object(),
    )

    assert result == SentinelResult(
        "result"
    )
    assert captured["context"] is context
    assert captured["ranked_pair"] is ranked_pair


def test_orchestration_does_not_create_parallel_priority_argument():
    import inspect

    signature = inspect.signature(
        compose_cross_border_provider_adjacent_result
    )

    assert "context" in signature.parameters
    assert "priority" not in signature.parameters


def test_orchestration_exposes_no_winner_or_production_authority():
    forbidden = {
        "winner",
        "selected_candidate",
        "best_candidate",
        "route_traffic",
        "production_enabled",
        "checkout",
        "payment",
        "purchase",
        "dispatch",
    }

    public_names = {
        name.lower()
        for name in dir(
            compose_cross_border_provider_adjacent_result
        )
        if not name.startswith("_")
    }

    assert forbidden.isdisjoint(
        public_names
    )
