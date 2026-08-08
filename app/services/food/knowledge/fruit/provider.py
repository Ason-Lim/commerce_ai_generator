from __future__ import annotations

from typing import Any, Mapping

from app.services.food.knowledge.base import (
    FoodKnowledgeProvider,
)
from app.services.food.knowledge.fruit.attributes import (
    build_fruit_attributes,
    extract_fruit_product_name,
)
from app.services.food.knowledge.fruit.parser import (
    parse_fruit,
)
from app.services.food.knowledge.fruit.rules import (
    build_fruit_rules,
)
from app.services.food.knowledge.fruit.scoring import (
    calculate_fruit_final_score,
    calculate_fruit_scores,
)
from app.services.food.knowledge.models import (
    FoodKnowledgeContext,
    FoodKnowledgeResult,
)


class FruitKnowledgeProvider(
    FoodKnowledgeProvider
):
    category_id = "fruit"
    category_name = "과일"

    aliases = (
        "과일",
        "fruit",
        "사과",
        "배",
        "감귤",
        "귤",
        "오렌지",
        "포도",
        "복숭아",
        "수박",
        "참외",
        "딸기",
        "블루베리",
        "바나나",
        "망고",
        "키위",
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

            for alias in alias_set:
                if alias == "배":
                    if alias in normalized_name.split():
                        return True

                    continue

                if alias in normalized_name:
                    return True

            return False

        return False

    def analyze(
        self,
        product: Mapping[str, Any],
        context: FoodKnowledgeContext | None = None,
    ) -> FoodKnowledgeResult:
        product_data = dict(product)

        parse_result = parse_fruit(
            product_data
        )

        attributes = build_fruit_attributes(
            product=product_data,
            parse_result=parse_result,
        )

        scores = calculate_fruit_scores(
            product_data,
            attributes,
            context,
        )

        (
            rule_results,
            reasons,
            warnings,
        ) = build_fruit_rules(
            attributes,
            scores,
        )

        final_score = (
            calculate_fruit_final_score(
                scores,
                context,
            )
        )

        return FoodKnowledgeResult(
            category_id=self.category_id,
            category_name=self.category_name,
            product_name=(
                extract_fruit_product_name(
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
                "provider_version": "2.2",
                "priority": (
                    context.priority
                    if context
                    else None
                ),
            },
            raw_product=product_data,
        )
