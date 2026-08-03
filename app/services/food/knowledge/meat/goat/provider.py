from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.services.food.knowledge.base import (
    FoodKnowledgeProvider,
)
from app.services.food.knowledge.meat.goat.attributes import (
    build_goat_attributes,
    extract_goat_product_name,
)
from app.services.food.knowledge.meat.goat.parser import (
    GoatParser,
)
from app.services.food.knowledge.meat.goat.rules import (
    apply_goat_rules,
)
from app.services.food.knowledge.meat.goat.scoring import (
    calculate_goat_final_score,
    calculate_goat_scores,
)
from app.services.food.knowledge.models import (
    FoodKnowledgeContext,
    FoodKnowledgeResult,
)


class GoatKnowledgeProvider(
    FoodKnowledgeProvider
):
    """
    Goat Knowledge Provider.

    Parser → Attributes → Scoring → Rules 순서로
    Goat 분석 파이프라인을 오케스트레이션한다.
    """

    category_id = "goat"
    category_name = "염소고기"
    parent_category_id = "meat"
    provider_id = "goat"

    aliases = (
        "염소고기",
        "염소 고기",
        "염소육",
        "염소 육",
        "흑염소",
        "흑 염소",
        "어린염소",
        "어린 염소",
        "보어염소",
        "보어 염소",
        "키코염소",
        "키코 염소",
        "토종흑염소",
        "토종 흑염소",
        "한국흑염소",
        "한국 흑염소",
        "goat meat",
        "kid goat",
        "young goat",
        "black goat",
        "boer goat",
        "kiko goat",
        "korean black goat",
        "chevon",
        "cabrito",
        "염소안심",
        "염소 안심",
        "goat tenderloin",
        "goat fillet",
        "염소등심",
        "염소 등심",
        "goat loin",
        "goat backstrap",
        "염소갈비",
        "염소 갈비",
        "goat rack",
        "goat ribs",
        "염소다리",
        "염소 다리",
        "염소다리살",
        "염소 다리살",
        "goat leg",
        "염소앞다리",
        "염소 앞다리",
        "염소어깨",
        "염소 어깨",
        "goat shoulder",
        "염소목살",
        "염소 목살",
        "goat neck",
        "염소사태",
        "염소 사태",
        "goat shank",
        "염소가슴살",
        "염소 가슴살",
        "goat breast",
        "통염소",
        "통 염소",
        "whole goat",
    )

    def __init__(
        self,
        *,
        parser: GoatParser | None = None,
    ) -> None:
        self.parser = (
            parser
            if parser is not None
            else GoatParser()
        )

    def supports(
        self,
        category_id: str | None = None,
        product_name: str | None = None,
    ) -> bool:
        alias_set = {
            alias.strip().casefold()
            for alias in self.aliases
            if alias.strip()
        }

        if category_id:
            normalized_category_id = (
                str(category_id)
                .strip()
                .casefold()
            )

            if normalized_category_id in {
                self.category_id,
                self.provider_id,
            }:
                return True

            if normalized_category_id in alias_set:
                return True

        if product_name:
            normalized_name = (
                str(product_name)
                .strip()
                .casefold()
            )

            if not normalized_name:
                return False

            return any(
                alias in normalized_name
                for alias in alias_set
            )

        return False

    def analyze(
        self,
        product: Mapping[str, Any],
        context: (
            FoodKnowledgeContext | None
        ) = None,
    ) -> FoodKnowledgeResult:
        if not isinstance(product, Mapping):
            raise TypeError(
                "product must be a Mapping"
            )

        if not product:
            raise ValueError(
                "product must not be empty"
            )

        product_data = dict(product)

        product_name = (
            extract_goat_product_name(
                product_data
            )
        )

        parse_result = (
            self.parser.parse_product(
                product_data
            )
        )

        attributes = build_goat_attributes(
            product=product_data,
            parse_result=parse_result,
        )

        scores = calculate_goat_scores(
            product=product_data,
            parse_result=parse_result,
            context=context,
        )

        reasons, warnings = (
            apply_goat_rules(
                attributes=attributes,
                scores=scores,
                parse_result=parse_result,
            )
        )

        final_score = (
            calculate_goat_final_score(
                scores
            )
        )

        return FoodKnowledgeResult(
            category_id=self.category_id,
            category_name=self.category_name,
            product_name=product_name or None,
            attributes=dict(attributes),
            scores=dict(scores),
            reasons=list(reasons),
            warnings=list(warnings),
            final_score=final_score,
            confidence=parse_result.confidence,
            metadata={
                "provider_id": self.provider_id,
                "provider": (
                    self.__class__.__name__
                ),
                "category_id": self.category_id,
                "parent_category_id": (
                    self.parent_category_id
                ),
                "parser": (
                    self.parser.__class__.__name__
                ),
                "priority": (
                    context.priority
                    if context is not None
                    else None
                ),
                "matched_field_count": (
                    parse_result.metadata.get(
                        "matched_field_count",
                        0,
                    )
                ),
                "expected_field_count": (
                    parse_result.metadata.get(
                        "expected_field_count",
                        3,
                    )
                ),
                "is_complete": (
                    parse_result.is_complete
                ),
                "is_usable": (
                    parse_result.is_usable
                ),
                "source_type": (
                    parse_result.metadata.get(
                        "source_type"
                    )
                ),
                "source_fields": list(
                    parse_result.metadata.get(
                        "source_fields",
                        [],
                    )
                ),
            },
            raw_product=dict(product_data),
        )


__all__ = [
    "GoatKnowledgeProvider",
]
