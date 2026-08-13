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
from app.services.food.knowledge.seafood.attributes import (
    build_seafood_attributes,
    extract_seafood_product_name,
)
from app.services.food.knowledge.seafood.parser import (
    parse_seafood,
)
from app.services.food.knowledge.seafood.rules import (
    build_seafood_rules,
)
from app.services.food.knowledge.seafood.scoring import (
    calculate_seafood_final_score,
    calculate_seafood_scores,
)


class SeafoodKnowledgeProvider(
    FoodKnowledgeProvider
):
    """
    Seafood Knowledge Provider.

    Provider는 orchestration만 담당한다.
    """

    category_id = "seafood"
    category_name = "수산물"

    aliases = (
        "seafood",
        "수산물",
        "연어",
        "참치",
        "고등어",
        "대구",
        "명태",
        "멸치",
        "새우",
        "대하",
        "꽃게",
        "대게",
        "킹크랩",
        "랍스터",
        "굴",
        "홍합",
        "가리비",
        "전복",
        "오징어",
        "문어",
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

        parse_result = parse_seafood(
            product_data
        )

        attributes = build_seafood_attributes(
            product=product_data,
            parse_result=parse_result,
        )

        scores = calculate_seafood_scores(
            product_data,
            attributes,
            context,
        )

        (
            rule_results,
            reasons,
            warnings,
        ) = build_seafood_rules(
            attributes,
            scores,
        )

        warnings = [
            *parse_result.warnings,
            *warnings,
        ]

        final_score = (
            calculate_seafood_final_score(
                scores,
                context,
            )
        )

        return FoodKnowledgeResult(
            category_id=self.category_id,
            category_name=self.category_name,
            product_name=(
                extract_seafood_product_name(
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
    "SeafoodKnowledgeProvider",
]
