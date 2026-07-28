from __future__ import annotations

from typing import Any, Mapping

from app.services.food.knowledge.base import (
    FoodKnowledgeProvider,
)
from app.services.food.knowledge.meat.beef.attributes import (
    build_beef_attributes,
    extract_beef_product_name,
)
from app.services.food.knowledge.meat.beef.parser import (
    BeefParser,
)
from app.services.food.knowledge.meat.beef.rules import (
    apply_beef_rules,
)
from app.services.food.knowledge.meat.beef.scoring import (
    calculate_beef_final_score,
    calculate_beef_scores,
)
from app.services.food.knowledge.models import (
    FoodKnowledgeContext,
    FoodKnowledgeResult,
)


class BeefKnowledgeProvider(
    FoodKnowledgeProvider
):
    """
    쇠고기 Knowledge Provider.

    역할:
    - BeefParser를 통한 상품 속성 분석
    - Registry 정보를 기반으로 지식 점수 구성
    - 분석 결과에 따른 이유와 경고 생성
    - FoodKnowledgeResult 반환

    담당하지 않는 역할:
    - 상품명 문자열 직접 파싱
    - 품종, 등급, 부위 별칭 관리
    - 등급별 점수 하드코딩
    """

    category_id = "beef"
    category_name = "소고기"

    aliases = (
        "소고기",
        "쇠고기",
        "한우",
        "육우",
        "와규",
        "beef",
        "우육",
        "등심",
        "안심",
        "채끝",
        "갈비",
        "부채살",
        "살치살",
        "토시살",
        "우삼겹",
    )

    def __init__(
        self,
        *,
        parser: BeefParser | None = None,
    ) -> None:
        """
        Parser 생성자 주입을 지원한다.

        테스트에서는 별도 Registry를 사용하는 BeefParser를
        전달할 수 있다.
        """
        self.parser = (
            parser
            if parser is not None
            else BeefParser()
        )

    # ==================================================================
    # Provider selection
    # ==================================================================

    def supports(
        self,
        category_id: str | None = None,
        product_name: str | None = None,
    ) -> bool:
        alias_set = {
            alias.strip().casefold()
            for alias in self.aliases
        }

        if category_id:
            normalized_category_id = (
                category_id.strip().casefold()
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
                product_name.strip().casefold()
            )

            return any(
                alias in normalized_name
                for alias in alias_set
            )

        return False

    # ==================================================================
    # Public API
    # ==================================================================

    def analyze(
        self,
        product: Mapping[str, Any],
        context: (
            FoodKnowledgeContext | None
        ) = None,
    ) -> FoodKnowledgeResult:
        if not isinstance(
            product,
            Mapping,
        ):
            raise TypeError(
                "product must be a Mapping"
            )

        product_data = dict(product)

        product_name = extract_beef_product_name(
            product_data
        )

        parse_result = (
            self.parser.parse_product(
                product_data
            )
        )

        attributes = build_beef_attributes(
            product=product_data,
            parse_result=parse_result,
        )

        scores = calculate_beef_scores(
            product=product_data,
            parse_result=parse_result,
            context=context,
        )

        reasons, warnings = apply_beef_rules(
            attributes=attributes,
            scores=scores,
            parse_result=parse_result,
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
            final_score=(
                calculate_beef_final_score(
                    scores
                )
            ),
            confidence=parse_result.confidence,
            metadata={
                "provider": (
                    self.__class__.__name__
                ),
                "parser": (
                    self.parser.__class__.__name__
                ),
                "priority": (
                    context.priority
                    if context
                    else None
                ),
                "country_code": (
                    parse_result.metadata.get(
                        "country_code"
                    )
                ),
                "matched_field_count": (
                    parse_result.metadata.get(
                        "matched_field_count",
                        0,
                    )
                ),
                "is_complete": (
                    parse_result.is_complete
                ),
            },
            raw_product=product_data,
        )


__all__ = [
    "BeefKnowledgeProvider",
]
