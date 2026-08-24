from __future__ import annotations

import inspect
from dataclasses import dataclass

from app.services.recommendation.cross_border_upstream_result_composition import (
    compose_cross_border_upstream_result,
)
from app.services.recommendation.models import (
    RecommendationContext,
    RecommendationPriority,
)


@dataclass(frozen=True)
class ReferenceBinding:
    candidate_position: int


@dataclass(frozen=True)
class ReferenceBindingSet:
    bindings: tuple[ReferenceBinding, ReferenceBinding]


@dataclass(frozen=True)
class SentinelResult:
    value: str


def _context() -> RecommendationContext:
    return RecommendationContext(
        query="한국 사과",
        priority=RecommendationPriority.PRICE,
        limit=2,
    )


def test_composes_existing_surfaces_in_authority_order(
    monkeypatch,
):
    calls = []

    context = _context()
    candidates = (
        object(),
        object(),
    )
    scoring_input = object()

    position_two_reference = ReferenceBinding(
        candidate_position=2
    )
    position_one_reference = ReferenceBinding(
        candidate_position=1
    )

    reference_binding_set = ReferenceBindingSet(
        bindings=(
            position_two_reference,
            position_one_reference,
        )
    )

    position_two_components = object()
    position_one_components = object()
    price_signals = object()
    aligned_components = object()
    scores = object()
    expected_result = SentinelResult("result")

    def fake_bind(
        *,
        reference_bindings,
        candidates,
    ):
        calls.append("bind_components")
        assert reference_bindings is reference_binding_set
        assert candidates is candidate_pair
        return (
            position_two_components,
            position_one_components,
        )

    def fake_price(scoring_input):
        calls.append("compose_price_signals")
        assert scoring_input is scoring_input_value
        return price_signals

    def fake_align(
        *,
        price_signals,
        first_binding,
        second_binding,
    ):
        calls.append("align_components")
        assert price_signals is price_signals_value
        assert first_binding is position_one_components
        assert second_binding is position_two_components
        return aligned_components

    def fake_scores(
        *,
        aligned_components,
        priority,
    ):
        calls.append("compose_scores")
        assert aligned_components is aligned_components_value
        assert priority is context.priority
        return scores

    def fake_result(
        *,
        context,
        reference_binding_set,
        candidates,
        scores,
        price_signals,
        aligned_components,
    ):
        calls.append("compose_result")
        assert context is context_value
        assert reference_binding_set is reference_binding_set_value
        assert candidates is candidate_pair
        assert scores is scores_value
        assert price_signals is price_signals_value
        assert aligned_components is aligned_components_value
        return expected_result

    candidate_pair = candidates
    scoring_input_value = scoring_input
    price_signals_value = price_signals
    aligned_components_value = aligned_components
    scores_value = scores
    context_value = context
    reference_binding_set_value = reference_binding_set

    module = (
        "app.services.recommendation."
        "cross_border_upstream_result_composition."
    )

    monkeypatch.setattr(
        module + "bind_cross_border_candidate_components",
        fake_bind,
    )
    monkeypatch.setattr(
        module + "compose_bound_cross_border_price_signals",
        fake_price,
    )
    monkeypatch.setattr(
        module + "align_cross_border_candidate_components",
        fake_align,
    )
    monkeypatch.setattr(
        module + "compose_cross_border_candidate_scores",
        fake_scores,
    )
    monkeypatch.setattr(
        module + "compose_cross_border_provider_adjacent_result",
        fake_result,
    )

    result = compose_cross_border_upstream_result(
        context=context,
        reference_binding_set=reference_binding_set,
        candidates=candidates,
        scoring_input=scoring_input,
    )

    assert result is expected_result
    assert calls == [
        "bind_components",
        "compose_price_signals",
        "align_components",
        "compose_scores",
        "compose_result",
    ]


def test_context_priority_is_the_only_scoring_priority(
    monkeypatch,
):
    context = _context()
    captured = {}

    reference_binding_set = ReferenceBindingSet(
        bindings=(
            ReferenceBinding(candidate_position=1),
            ReferenceBinding(candidate_position=2),
        )
    )

    module = (
        "app.services.recommendation."
        "cross_border_upstream_result_composition."
    )

    monkeypatch.setattr(
        module + "bind_cross_border_candidate_components",
        lambda **kwargs: (
            object(),
            object(),
        ),
    )
    monkeypatch.setattr(
        module + "compose_bound_cross_border_price_signals",
        lambda scoring_input: object(),
    )
    monkeypatch.setattr(
        module + "align_cross_border_candidate_components",
        lambda **kwargs: object(),
    )

    def fake_scores(
        *,
        aligned_components,
        priority,
    ):
        captured["priority"] = priority
        return object()

    monkeypatch.setattr(
        module + "compose_cross_border_candidate_scores",
        fake_scores,
    )
    monkeypatch.setattr(
        module + "compose_cross_border_provider_adjacent_result",
        lambda **kwargs: SentinelResult("result"),
    )

    compose_cross_border_upstream_result(
        context=context,
        reference_binding_set=reference_binding_set,
        candidates=(
            object(),
            object(),
        ),
        scoring_input=object(),
    )

    assert captured["priority"] is context.priority


def test_signature_requires_established_inputs_only():
    signature = inspect.signature(
        compose_cross_border_upstream_result
    )

    assert tuple(signature.parameters) == (
        "context",
        "reference_binding_set",
        "candidates",
        "scoring_input",
    )

    forbidden = {
        "handoff",
        "raw_handoff",
        "product_identity",
        "priority",
        "winner",
        "selected_candidate",
        "provider",
        "production_enabled",
        "route_traffic",
        "checkout",
        "payment",
        "purchase",
        "dispatch",
    }

    assert forbidden.isdisjoint(
        signature.parameters
    )
