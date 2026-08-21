from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable

from app.services.cross_border.context import (
    CrossBorderEvaluationContext,
)
from app.services.cross_border.landed_cost import (
    LandedCostComponentEvidence,
    LandedCostComponentState,
)


class LandedCostAggregationReadinessState(str, Enum):
    """
    Canonical readiness state for bounded landed-cost aggregation.

    READY:
        applicable monetary component evidence is complete enough
        for a later arithmetic aggregation step.

    UNKNOWN:
        evidence is insufficient to decide readiness safely.

    NOT_READY:
        evidence is present but structurally incompatible with
        bounded aggregation.
    """

    READY = "ready"
    UNKNOWN = "unknown"
    NOT_READY = "not_ready"


@dataclass(frozen=True)
class LandedCostAggregationReadiness:
    """
    Immutable landed-cost aggregation-readiness result.

    This result does not calculate landed cost, convert currency,
    calculate duty/tax, rank purchase routes, recommend a path,
    or execute a transaction.
    """

    state: LandedCostAggregationReadinessState

    applicable_component_count: int
    arithmetic_component_count: int

    currency: str | None
    context: CrossBorderEvaluationContext | None

    reason: str


def evaluate_landed_cost_aggregation_readiness(
    components: Iterable[LandedCostComponentEvidence],
) -> LandedCostAggregationReadiness:
    """
    Determine whether landed-cost component evidence can proceed
    to a later bounded arithmetic aggregation stage.

    Rules:

    - NOT_APPLICABLE components are excluded from arithmetic.
    - UNKNOWN makes readiness UNKNOWN.
    - UNAVAILABLE makes readiness NOT_READY.
    - KNOWN / ESTIMATED / DERIVED are arithmetic-bearing states.
    - arithmetic-bearing components must share one currency.
    - explicit contexts must not conflict.
    - if arithmetic-bearing evidence has no usable context at all,
      readiness remains UNKNOWN.
    - zero is a valid arithmetic value and is never UNKNOWN.
    """

    component_list = tuple(components)

    if not component_list:
        return LandedCostAggregationReadiness(
            state=(
                LandedCostAggregationReadinessState.NOT_READY
            ),
            applicable_component_count=0,
            arithmetic_component_count=0,
            currency=None,
            context=None,
            reason=(
                "at least one landed-cost component is required"
            ),
        )

    applicable_components = [
        component
        for component in component_list
        if (
            component.state
            is not LandedCostComponentState.NOT_APPLICABLE
        )
    ]

    if not applicable_components:
        return LandedCostAggregationReadiness(
            state=(
                LandedCostAggregationReadinessState.NOT_READY
            ),
            applicable_component_count=0,
            arithmetic_component_count=0,
            currency=None,
            context=None,
            reason=(
                "no applicable landed-cost components remain"
            ),
        )

    unavailable_components = [
        component
        for component in applicable_components
        if (
            component.state
            is LandedCostComponentState.UNAVAILABLE
        )
    ]

    if unavailable_components:
        return LandedCostAggregationReadiness(
            state=(
                LandedCostAggregationReadinessState.NOT_READY
            ),
            applicable_component_count=len(
                applicable_components
            ),
            arithmetic_component_count=0,
            currency=None,
            context=None,
            reason=(
                "one or more landed-cost components are "
                "UNAVAILABLE"
            ),
        )

    unknown_components = [
        component
        for component in applicable_components
        if (
            component.state
            is LandedCostComponentState.UNKNOWN
        )
    ]

    if unknown_components:
        return LandedCostAggregationReadiness(
            state=(
                LandedCostAggregationReadinessState.UNKNOWN
            ),
            applicable_component_count=len(
                applicable_components
            ),
            arithmetic_component_count=0,
            currency=None,
            context=None,
            reason=(
                "one or more landed-cost components are UNKNOWN"
            ),
        )

    arithmetic_states = {
        LandedCostComponentState.KNOWN,
        LandedCostComponentState.ESTIMATED,
        LandedCostComponentState.DERIVED,
    }

    arithmetic_components = [
        component
        for component in applicable_components
        if component.state in arithmetic_states
    ]

    if not arithmetic_components:
        return LandedCostAggregationReadiness(
            state=(
                LandedCostAggregationReadinessState.NOT_READY
            ),
            applicable_component_count=len(
                applicable_components
            ),
            arithmetic_component_count=0,
            currency=None,
            context=None,
            reason=(
                "no arithmetic-bearing landed-cost components"
            ),
        )

    currencies = {
        component.currency
        for component in arithmetic_components
        if component.currency is not None
    }

    if len(currencies) != 1:
        return LandedCostAggregationReadiness(
            state=(
                LandedCostAggregationReadinessState.NOT_READY
            ),
            applicable_component_count=len(
                applicable_components
            ),
            arithmetic_component_count=len(
                arithmetic_components
            ),
            currency=None,
            context=None,
            reason=(
                "landed-cost component currencies are incompatible"
            ),
        )

    currency = next(iter(currencies))

    explicit_contexts = [
        component.context
        for component in arithmetic_components
        if component.context is not None
    ]

    if not explicit_contexts:
        return LandedCostAggregationReadiness(
            state=(
                LandedCostAggregationReadinessState.UNKNOWN
            ),
            applicable_component_count=len(
                applicable_components
            ),
            arithmetic_component_count=len(
                arithmetic_components
            ),
            currency=currency,
            context=None,
            reason=(
                "landed-cost evaluation context is unavailable"
            ),
        )

    canonical_context = explicit_contexts[0]

    for context in explicit_contexts[1:]:
        if context != canonical_context:
            return LandedCostAggregationReadiness(
                state=(
                    LandedCostAggregationReadinessState.NOT_READY
                ),
                applicable_component_count=len(
                    applicable_components
                ),
                arithmetic_component_count=len(
                    arithmetic_components
                ),
                currency=currency,
                context=None,
                reason=(
                    "landed-cost component evaluation contexts "
                    "are incompatible"
                ),
            )

    missing_context = any(
        component.context is None
        for component in arithmetic_components
    )

    if missing_context:
        return LandedCostAggregationReadiness(
            state=(
                LandedCostAggregationReadinessState.UNKNOWN
            ),
            applicable_component_count=len(
                applicable_components
            ),
            arithmetic_component_count=len(
                arithmetic_components
            ),
            currency=currency,
            context=canonical_context,
            reason=(
                "one or more landed-cost component contexts "
                "are unavailable"
            ),
        )

    return LandedCostAggregationReadiness(
        state=LandedCostAggregationReadinessState.READY,
        applicable_component_count=len(
            applicable_components
        ),
        arithmetic_component_count=len(
            arithmetic_components
        ),
        currency=currency,
        context=canonical_context,
        reason=(
            "landed-cost components are ready for bounded "
            "aggregation"
        ),
    )
