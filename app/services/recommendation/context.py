from __future__ import annotations

from types import MappingProxyType
from typing import Any, Mapping

from .models import RecommendationContext
from .parser import RecommendationQuery
from .policy import RecommendationPolicy


_CONTEXT_METADATA_KEYS = frozenset(
    {
        "raw_query",
        "priority_hint",
        "gift_target",
        "occasion",
        "gift_intent",
        "requested_priority",
    }
)


def build_recommendation_context(
    query: RecommendationQuery,
    policy: RecommendationPolicy,
    *,
    session_id: str | None = None,
    marketplace_id: str | None = None,
    category_id: str | None = None,
    limit: int = 10,
    metadata: Mapping[str, Any] | None = None,
) -> RecommendationContext:
    """
    Bind already-parsed query semantics and already-resolved policy
    into the canonical RecommendationContext.

    Responsibilities:
    - combine parser output;
    - combine policy output;
    - carry execution-scoped identifiers and limit;
    - preserve a controlled set of semantic metadata.

    Non-responsibilities:
    - query parsing;
    - policy resolution;
    - preference persistence;
    - session persistence;
    - scoring;
    - ranking;
    - marketplace lookup;
    - market intelligence lookup;
    - API/UI response construction.
    """

    context_metadata: dict[str, Any] = {
        "raw_query": query.raw_query,
        "priority_hint": query.priority_hint,
        "gift_target": query.gift_target,
        "occasion": query.occasion,
        "gift_intent": query.gift_intent,
        "requested_priority": policy.requested_priority,
    }

    if metadata:
        reserved = (
            set(metadata)
            & _CONTEXT_METADATA_KEYS
        )

        if reserved:
            raise ValueError(
                "metadata may not override canonical context keys: "
                + ", ".join(
                    sorted(reserved)
                )
            )

        context_metadata.update(
            dict(metadata)
        )

    return RecommendationContext(
        query=query.search_query,
        priority=policy.priority,
        session_id=session_id,
        marketplace_id=marketplace_id,
        category_id=category_id,
        limit=limit,
        adaptive=policy.adaptive,
        metadata=MappingProxyType(
            context_metadata
        ),
    )
