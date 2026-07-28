from __future__ import annotations

from typing import Any, Mapping

from app.services.food.category_registry import (
    FoodCategoryConfig,
    resolve_food_category as resolve_category_config,
)
from app.services.food.knowledge.models import (
    FoodKnowledgeContext,
    FoodKnowledgeResult,
)
from app.services.food.knowledge.registry import (
    get_food_provider,
    resolve_food_provider,
)


class FoodKnowledgeResolutionError(RuntimeError):
    pass


def resolve_product_category(
    product: Mapping[str, Any],
    *,
    category_id: str | None = None,
) -> FoodCategoryConfig | None:
    product_name = _extract_product_name(
        product
    )

    explicit_category_id = (
        category_id
        or _extract_category_id(product)
    )

    return resolve_category_config(
        category_id=explicit_category_id,
        product_name=product_name,
    )


def resolve_knowledge_provider(
    product: Mapping[str, Any],
    *,
    category_id: str | None = None,
):
    product_name = _extract_product_name(
        product
    )

    category_config = resolve_product_category(
        product,
        category_id=category_id,
    )

    if (
        category_config is not None
        and category_config.provider_id
    ):
        provider = get_food_provider(
            category_config.provider_id
        )

        if provider is not None:
            return provider

    resolved_category_id = (
        category_config.category_id
        if category_config is not None
        else category_id
    )

    return resolve_food_provider(
        category_id=resolved_category_id,
        product_name=product_name,
    )


def analyze_food_product(
    product: Mapping[str, Any],
    *,
    category_id: str | None = None,
    context: FoodKnowledgeContext | None = None,
    strict: bool = False,
) -> FoodKnowledgeResult | None:
    provider = resolve_knowledge_provider(
        product,
        category_id=category_id,
    )

    if provider is None:
        if strict:
            raise FoodKnowledgeResolutionError(
                "상품을 처리할 Food Knowledge Provider를 "
                "찾지 못했습니다. "
                f"category_id={category_id!r}, "
                f"product_name={_extract_product_name(product)!r}"
            )

        return None

    return provider.analyze(
        product,
        context=context,
    )


def resolve_food_knowledge(
    product: Mapping[str, Any],
    *,
    category_id: str | None = None,
    context: FoodKnowledgeContext | None = None,
    strict: bool = False,
) -> FoodKnowledgeResult | None:
    """
    Food Knowledge Engine 대표 진입점.
    """

    return analyze_food_product(
        product,
        category_id=category_id,
        context=context,
        strict=strict,
    )


def _extract_product_name(
    product: Mapping[str, Any],
) -> str:
    return str(
        product.get("product_name")
        or product.get("title")
        or product.get("name")
        or ""
    ).strip()


def _extract_category_id(
    product: Mapping[str, Any],
) -> str | None:
    value = (
        product.get("food_category_id")
        or product.get("category_id")
        or product.get("category")
        or product.get("category_name")
    )

    if value is None:
        return None

    normalized = str(value).strip()

    return normalized or None
