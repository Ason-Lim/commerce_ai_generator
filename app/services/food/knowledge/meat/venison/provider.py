from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.services.food.knowledge.base import (
    FoodKnowledgeProvider,
)
from app.services.food.knowledge.meat.venison.attributes import (
    build_venison_attributes,
    extract_venison_product_name,
)
from app.services.food.knowledge.meat.venison.parser import (
    VenisonParser,
)
from app.services.food.knowledge.meat.venison.rules import (
    apply_venison_rules,
)
from app.services.food.knowledge.meat.venison.scoring import (
    calculate_venison_final_score,
    calculate_venison_scores,
)
from app.services.food.knowledge.models import (
    FoodKnowledgeContext,
    FoodKnowledgeResult,
)


class VenisonKnowledgeProvider(
    FoodKnowledgeProvider
):
    """
    Venison Knowledge Provider.

    기존 Venison Parser, Attributes, Scoring, Rules를
    순서대로 오케스트레이션하고 FoodKnowledgeResult를 생성한다.
    """

    category_id = "venison"
    category_name = "사슴고기"
    parent_category_id = "meat"
    provider_id = "venison"

    aliases = (
        "사슴고기",
        "사슴 고기",
        "사슴육",
        "사슴 육",
        "녹육",
        "venison",
        "deer meat",
        "deer",
        "엘크고기",
        "엘크 고기",
        "elk meat",
        "레드디어",
        "red deer",
        "어린사슴",
        "어린 사슴",
        "송아지사슴",
        "사슴안심",
        "사슴 안심",
        "venison tenderloin",
        "deer tenderloin",
        "사슴등심",
        "사슴 등심",
        "venison loin",
        "사슴가슴살",
        "사슴 가슴살",
        "venison breast",
        "deer breast",
        "사슴다리",
        "사슴 다리",
        "사슴다리살",
        "사슴 다리살",
        "venison leg",
        "사슴어깨",
        "사슴 어깨",
        "venison shoulder",
        "사슴목살",
        "사슴 목살",
        "venison neck",
        "사슴갈비",
        "사슴 갈비",
        "venison ribs",
        "사슴로스",
        "사슴 로스",
    )

    def __init__(
        self,
        *,
        parser: VenisonParser | None = None,
    ) -> None:
        self.parser = (
            parser
            if parser is not None
            else VenisonParser()
        )

    def supports(
        self,
        category_id: str | None = None,
        product_name: str | None = None,
    ) -> bool:
        """
        category_id 또는 상품명을 기준으로 지원 여부를 반환한다.
        """
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
        """
        Venison 분석 파이프라인을 실행한다.
        """
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
            extract_venison_product_name(
                product_data
            )
        )

        parse_result = (
            self.parser.parse_product(
                product_data
            )
        )

        attributes = build_venison_attributes(
            product=product_data,
            parse_result=parse_result,
        )

        scores = calculate_venison_scores(
            product=product_data,
            parse_result=parse_result,
            context=context,
        )

        reasons, warnings = (
            apply_venison_rules(
                attributes=attributes,
                scores=scores,
                parse_result=parse_result,
            )
        )

        final_score = (
            calculate_venison_final_score(
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
    "VenisonKnowledgeProvider",
]
