from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.services.food.knowledge.base import (
    FoodKnowledgeProvider,
)
from app.services.food.knowledge.coffee.attributes import (
    build_coffee_attributes,
    extract_coffee_product_name,
)
from app.services.food.knowledge.coffee.parser import (
    CoffeeParser,
)
from app.services.food.knowledge.coffee.rules import (
    apply_coffee_rules,
)
from app.services.food.knowledge.coffee.scoring import (
    calculate_coffee_final_score,
    calculate_coffee_scores,
)
from app.services.food.knowledge.models import (
    FoodKnowledgeContext,
    FoodKnowledgeResult,
)


class CoffeeKnowledgeProvider(
    FoodKnowledgeProvider
):
    """
    Coffee Knowledge Provider.

    역할:
    - CoffeeParser 실행
    - Coffee attributes 구성
    - Coffee scoring 실행
    - Coffee rules 실행
    - 최종 점수 계산
    - FoodKnowledgeResult 생성

    담당하지 않는 역할:
    - 상품명 직접 파싱
    - Registry 데이터 관리
    - 점수 공식 재구현
    - 공통 Provider Registry 변경
    - Category Registry 변경
    """

    category_id = "coffee"
    category_name = "커피"

    aliases = (
        "coffee",
        "커피",
        "원두",
        "커피 원두",
        "아라비카",
        "arabica",
        "로부스타",
        "robusta",
        "에스프레소",
        "espresso",
        "드립커피",
        "드립 커피",
        "핸드드립",
        "핸드 드립",
        "콜드브루",
        "콜드 브루",
        "cold brew",
        "디카페인 커피",
        "decaf coffee",
    )

    def __init__(
        self,
        *,
        parser: CoffeeParser | None = None,
    ) -> None:
        """
        Parser 생성자 주입을 지원한다.
        """
        self.parser = (
            parser
            if parser is not None
            else CoffeeParser()
        )

    def supports(
        self,
        category_id: str | None = None,
        product_name: str | None = None,
    ) -> bool:
        """
        category_id 또는 상품명을 기준으로
        Coffee Provider 지원 여부를 반환한다.
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

            if (
                normalized_category_id
                == self.category_id
            ):
                return True

            if (
                normalized_category_id
                in alias_set
            ):
                return True

        if product_name:
            normalized_name = (
                str(product_name)
                .strip()
                .casefold()
            )

            if not normalized_name:
                return False

            aliases_by_length = sorted(
                alias_set,
                key=len,
                reverse=True,
            )

            return any(
                alias in normalized_name
                for alias in aliases_by_length
            )

        return False

    def analyze(
        self,
        product: Mapping[str, Any],
        context: FoodKnowledgeContext | None = None,
    ) -> FoodKnowledgeResult:
        """
        Coffee 상품을 분석하여 공통
        FoodKnowledgeResult를 반환한다.
        """
        if not isinstance(
            product,
            Mapping,
        ):
            raise TypeError(
                "product must be a Mapping"
            )

        product_data = dict(product)

        product_name = (
            extract_coffee_product_name(
                product_data
            )
        )

        parse_result = (
            self.parser.parse_product(
                product_data
            )
        )

        attributes = build_coffee_attributes(
            product=product_data,
            parse_result=parse_result,
        )

        scores = calculate_coffee_scores(
            product=product_data,
            parse_result=parse_result,
        )

        reasons, warnings = apply_coffee_rules(
            attributes=attributes,
            scores=scores,
            parse_result=parse_result,
        )

        final_score = (
            calculate_coffee_final_score(
                scores
            )
        )

        return FoodKnowledgeResult(
            category_id=self.category_id,
            category_name=self.category_name,
            product_name=(
                product_name or None
            ),
            attributes=attributes,
            scores=scores,
            reasons=reasons,
            warnings=warnings,
            final_score=final_score,
            confidence=parse_result.confidence,
            metadata={
                "provider_id": self.category_id,
                "provider": (
                    self.__class__.__name__
                ),
                "parser": (
                    self.parser.__class__.__name__
                ),
                "priority": (
                    context.priority
                    if context is not None
                    else None
                ),
                "query": (
                    context.query
                    if context is not None
                    else None
                ),
                "user_mode": (
                    context.user_mode
                    if context is not None
                    else None
                ),
                "season": (
                    context.season
                    if context is not None
                    else None
                ),
                "region": (
                    context.region
                    if context is not None
                    else None
                ),
                "matched_field_count": (
                    parse_result
                    .matched_field_count
                ),
                "expected_field_count": 4,
                "is_complete": (
                    parse_result.is_complete
                ),
                "is_usable": (
                    parse_result.is_usable
                ),
            },
            raw_product=product_data,
        )


__all__ = [
    "CoffeeKnowledgeProvider",
]
