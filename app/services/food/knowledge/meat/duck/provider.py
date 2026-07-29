from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.services.food.knowledge.base import (
    FoodKnowledgeProvider,
)
from app.services.food.knowledge.meat.duck.attributes import (
    build_duck_attributes,
    extract_duck_product_name,
)
from app.services.food.knowledge.meat.duck.parser import (
    DuckParser,
)
from app.services.food.knowledge.meat.duck.rules import (
    apply_duck_rules,
)
from app.services.food.knowledge.meat.duck.scoring import (
    calculate_duck_final_score,
    calculate_duck_scores,
)
from app.services.food.knowledge.models import (
    FoodKnowledgeContext,
    FoodKnowledgeResult,
)


class DuckKnowledgeProvider(
    FoodKnowledgeProvider
):
    """
    오리고기 Knowledge Provider.

    역할:
    - DuckParser 실행
    - Duck attributes 구성
    - Duck scoring 실행
    - Duck rules 실행
    - 최종 점수 계산
    - FoodKnowledgeResult 생성

    담당하지 않는 역할:
    - 상품명 직접 파싱
    - Registry 데이터 관리
    - Registry 점수 하드코딩
    - 공통 Provider 등록 정책 변경
    """

    category_id = "duck"
    category_name = "오리고기"

    aliases = (
        "오리고기",
        "오리 고기",
        "오리육",
        "duck",
        "훈제오리",
        "훈제 오리",
        "백숙오리",
        "백숙 오리",
        "생오리",
        "생 오리",
        "통오리",
        "통 오리",
        "오리가슴살",
        "오리 가슴살",
        "오리안심",
        "오리 안심",
        "오리다리",
        "오리 다리",
        "오리다리살",
        "오리 다리살",
        "오리날개",
        "오리 날개",
        "오리목",
        "오리 목",
        "오리로스",
        "오리 로스",
    )

    def __init__(
        self,
        *,
        parser: DuckParser | None = None,
    ) -> None:
        """
        Parser 생성자 주입을 지원한다.
        """
        self.parser = (
            parser
            if parser is not None
            else DuckParser()
        )

    def supports(
        self,
        category_id: str | None = None,
        product_name: str | None = None,
    ) -> bool:
        """
        category_id 또는 상품명을 기준으로
        Duck Provider 지원 여부를 반환한다.
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
        Duck 분석 파이프라인을 순서대로 실행한다.
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
            extract_duck_product_name(
                product_data
            )
        )

        parse_result = (
            self.parser.parse_product(
                product_data
            )
        )

        attributes = build_duck_attributes(
            product=product_data,
            parse_result=parse_result,
        )

        scores = calculate_duck_scores(
            product=product_data,
            parse_result=parse_result,
            context=context,
        )

        reasons, warnings = (
            apply_duck_rules(
                attributes=attributes,
                scores=scores,
                parse_result=parse_result,
            )
        )

        final_score = (
            calculate_duck_final_score(
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
            confidence=(
                parse_result.confidence
            ),
            metadata={
                "provider_id": (
                    self.category_id
                ),
                "provider": (
                    self.__class__.__name__
                ),
                "parser": (
                    self.parser.__class__.__name__
                ),
                "parent_category_id": "meat",
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
                "source_fields": (
                    parse_result.metadata.get(
                        "source_fields",
                        [],
                    )
                ),
            },
            raw_product=product_data,
        )


__all__ = [
    "DuckKnowledgeProvider",
]
