from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.services.food.knowledge.base import (
    FoodKnowledgeProvider,
)
from app.services.food.knowledge.models import (
    FoodKnowledgeContext,
    FoodKnowledgeResult,
)
from app.services.food.knowledge.vegetable.attributes import (
    build_vegetable_attributes,
    extract_vegetable_product_name,
)
from app.services.food.knowledge.vegetable.parser import (
    parse_vegetable,
)
from app.services.food.knowledge.vegetable.rules import (
    build_vegetable_rules,
)
from app.services.food.knowledge.vegetable.scoring import (
    calculate_vegetable_final_score,
    calculate_vegetable_scores,
)


class VegetableKnowledgeProvider(
    FoodKnowledgeProvider
):
    """
    Vegetable Knowledge Provider.

    Provider는 orchestration만 담당한다.
    """

    category_id = "vegetable"
    category_name = "채소"

    aliases = (
        "vegetable",
        "채소",
        "야채",
        "상추",
        "깻잎",
        "시금치",
        "배추",
        "양배추",
        "당근",
        "감자",
        "고구마",
        "양파",
        "마늘",
        "오이",
        "애호박",
        "토마토",
        "파프리카",
        "브로콜리",
    )

    def supports(
        self,
        category_id: str | None = None,
        product_name: str | None = None,
    ) -> bool:
        alias_set = {
            alias.strip().lower()
            for alias in self.aliases
        }

        if category_id:
            normalized_category_id = (
                category_id.strip().lower()
            )

            if (
                normalized_category_id
                == self.category_id
            ):
                return True

            if normalized_category_id in alias_set:
                return True

        if product_name:
            normalized_name = (
                product_name.strip().lower()
            )

            return any(
                alias in normalized_name
                for alias in alias_set
            )

        return False

    def analyze(
        self,
        product: Mapping[str, Any],
        context: FoodKnowledgeContext | None = None,
    ) -> FoodKnowledgeResult:
        if not isinstance(product, Mapping):
            raise TypeError(
                "product must be a Mapping"
            )

        product_data = dict(product)

        parse_result = parse_vegetable(
            product_data
        )

        attributes = (
            build_vegetable_attributes(
                product=product_data,
                parse_result=parse_result,
            )
        )

        scores = calculate_vegetable_scores(
            product_data,
            attributes,
            context,
        )

        (
            rule_results,
            reasons,
            warnings,
        ) = build_vegetable_rules(
            attributes,
            scores,
        )

        final_score = (
            calculate_vegetable_final_score(
                scores,
                context,
            )
        )

        return FoodKnowledgeResult(
            category_id=self.category_id,
            category_name=self.category_name,
            product_name=(
                extract_vegetable_product_name(
                    product_data
                )
                or None
            ),
            attributes=attributes,
            scores=scores,
            rules=rule_results,
            reasons=reasons,
            warnings=warnings,
            final_score=final_score,
            confidence=float(
                parse_result.confidence
            ),
            metadata={
                "provider": (
                    self.__class__.__name__
                ),
                "provider_version": "1.0",
                "priority": (
                    context.priority
                    if context
                    else None
                ),
            },
            raw_product=product_data,
        )


__all__ = [
    "VegetableKnowledgeProvider",
]
