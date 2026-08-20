from __future__ import annotations

from collections.abc import Callable
from typing import Any

from app.services.recommendation.models import (
    RecommendationCandidate,
    RecommendationResult,
)


def candidate_to_legacy_product(
    candidate: RecommendationCandidate,
) -> dict[str, Any]:
    """
    Convert a canonical RecommendationCandidate into
    a legacy-compatible product mapping.

    Canonical candidate.item remains the source of
    product identity and product attributes.

    Compatibility score fields are added without
    modifying the canonical Recommendation model.
    """
    product = dict(candidate.item)

    product["score"] = candidate.score.final_score
    product["final_score"] = candidate.score.final_score
    product["rank"] = candidate.rank

    product["quality_score"] = (
        candidate.score.components.quality
    )
    product["price_score"] = (
        candidate.score.components.price
    )
    product["trust_score"] = (
        candidate.score.components.trust
    )

    return product


def legacy_products_from_result(
    result: RecommendationResult,
) -> list[dict[str, Any]]:
    """
    Produce legacy-compatible products in canonical
    recommendation rank order.
    """
    candidates = sorted(
        result.candidates,
        key=lambda candidate: candidate.rank,
    )

    return [
        candidate_to_legacy_product(candidate)
        for candidate in candidates
    ]


def legacy_top3_from_result(
    result: RecommendationResult,
) -> list[dict[str, Any]]:
    return legacy_products_from_result(
        result
    )[:3]


def legacy_best_price_from_result(
    result: RecommendationResult,
) -> dict[str, Any] | None:
    products = legacy_products_from_result(
        result
    )

    valid_products = [
        product
        for product in products
        if isinstance(
            product.get("price"),
            (int, float),
        )
    ]

    if not valid_products:
        return None

    return min(
        valid_products,
        key=lambda product: product["price"],
    )


def legacy_best_quality_from_result(
    result: RecommendationResult,
) -> dict[str, Any] | None:
    if not result.candidates:
        return None

    candidate = max(
        result.candidates,
        key=lambda item: (
            item.score.components.quality,
            -item.rank,
        ),
    )

    return candidate_to_legacy_product(
        candidate
    )


def apply_legacy_b2b_strategy(
    products: list[dict[str, Any]],
    *,
    quantity: int | None,
    strategy_builder: (
        Callable[[dict[str, Any], int | None], Any]
        | None
    ) = None,
) -> list[dict[str, Any]]:
    """
    Attach legacy B2B strategy data outside the
    canonical RecommendationResult responsibility.

    A strategy_builder is injected so this adapter
    does not take ownership of B2B business policy.
    """
    if strategy_builder is None:
        return products

    enriched: list[dict[str, Any]] = []

    for product in products:
        item = dict(product)
        item["b2b_strategy"] = strategy_builder(
            item,
            quantity,
        )
        enriched.append(item)

    return enriched


def build_legacy_response_components(
    result: RecommendationResult,
    *,
    mode: str,
    quantity: int | None = None,
    strategy_builder: (
        Callable[[dict[str, Any], int | None], Any]
        | None
    ) = None,
) -> dict[str, Any]:
    """
    Translate canonical recommendation output into
    the compatibility-owned portion of the legacy
    generator response.

    Request-owned fields such as query, intent,
    search_keyword and priority remain the caller's
    responsibility.
    """
    products = legacy_products_from_result(
        result
    )

    top3 = products[:3]

    if (
        str(mode).upper() == "B2B"
        and strategy_builder is not None
    ):
        top3 = apply_legacy_b2b_strategy(
            top3,
            quantity=quantity,
            strategy_builder=strategy_builder,
        )

    return {
        "summary": result.summary,
        "top3": top3,
        "best_price": (
            legacy_best_price_from_result(
                result
            )
        ),
        "best_quality": (
            legacy_best_quality_from_result(
                result
            )
        ),
        "products": products,
    }
