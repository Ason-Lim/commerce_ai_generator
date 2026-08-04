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
from app.services.food.knowledge.wine.attributes import (
    build_wine_attributes,
    extract_wine_product_name,
)
from app.services.food.knowledge.wine.parser import (
    WineParser,
)
from app.services.food.knowledge.wine.rules import (
    apply_wine_rules,
)
from app.services.food.knowledge.wine.scoring import (
    calculate_wine_final_score,
    calculate_wine_scores,
)


class WineKnowledgeProvider(
    FoodKnowledgeProvider
):
    """
    Wine Knowledge Provider.

    역할:
    - WineParser 실행
    - Wine attributes 구성
    - Wine scoring 실행
    - Wine rules 실행
    - 최종 점수 계산
    - FoodKnowledgeResult 생성

    담당하지 않는 역할:
    - 상품명 직접 파싱
    - Registry 데이터 관리
    - 점수 공식 구현
    - Rule 조건 구현
    - 공통 Provider Registry 변경
    """

    category_id = "wine"
    category_name = "와인"

    aliases = (
        "와인",
        "wine",
        "레드 와인",
        "레드와인",
        "red wine",
        "화이트 와인",
        "화이트와인",
        "white wine",
        "스파클링 와인",
        "스파클링와인",
        "sparkling wine",
        "보르도",
        "bordeaux",
        "부르고뉴",
        "burgundy",
        "bourgogne",
        "나파 밸리",
        "나파밸리",
        "napa valley",
        "카베르네 소비뇽",
        "까베르네 소비뇽",
        "cabernet sauvignon",
        "샤르도네",
        "chardonnay",
        "리슬링",
        "riesling",
        "메를로",
        "merlot",
        "피노 누아",
        "피노누아",
        "pinot noir",
        "샴페인",
        "champagne",
    )

    def __init__(
        self,
        *,
        parser: WineParser | None = None,
    ) -> None:
        self.parser = (
            parser
            if parser is not None
            else WineParser()
        )

    def supports(
        self,
        category_id: str | None = None,
        product_name: str | None = None,
    ) -> bool:
        """
        현재 공유 Runtime Contract에 따라
        category alias와 상품명 alias를 지원한다.
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

            if normalized_category_id in alias_set:
                return True

        if not product_name:
            return False

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

    def analyze(
        self,
        product: Mapping[str, Any],
        context: FoodKnowledgeContext | None = None,
    ) -> FoodKnowledgeResult:
        """
        Wine 상품을 분석해 공통 FoodKnowledgeResult를 반환한다.
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
            extract_wine_product_name(
                product_data
            )
        )

        parse_result = (
            self.parser.parse_product(
                product_data
            )
        )

        attributes = build_wine_attributes(
            product=product_data,
            parse_result=parse_result,
        )

        scores = calculate_wine_scores(
            product=product_data,
            parse_result=parse_result,
        )

        reasons, warnings = apply_wine_rules(
            attributes=attributes,
            scores=scores,
            parse_result=parse_result,
        )

        final_score = (
            calculate_wine_final_score(
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
                "expected_field_count": 6,
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
    "WineKnowledgeProvider",
]
