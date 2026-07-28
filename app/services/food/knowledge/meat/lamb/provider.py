from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.services.food.knowledge.base import (
    FoodKnowledgeProvider,
)
from app.services.food.knowledge.meat.lamb.attributes import (
    build_lamb_attributes,
    extract_lamb_product_name,
)
from app.services.food.knowledge.meat.lamb.parser import (
    LambParser,
)
from app.services.food.knowledge.meat.lamb.rules import (
    apply_lamb_rules,
)
from app.services.food.knowledge.meat.lamb.scoring import (
    calculate_lamb_final_score,
    calculate_lamb_scores,
)
from app.services.food.knowledge.models import (
    FoodKnowledgeContext,
    FoodKnowledgeResult,
)


class LambKnowledgeProvider(
    FoodKnowledgeProvider
):
    """
    양고기 Knowledge Provider.

    역할:
    - LambParser 실행
    - Lamb attributes 구성
    - Lamb scoring 실행
    - Lamb rules 실행
    - 최종 점수 계산
    - FoodKnowledgeResult 생성

    담당하지 않는 역할:
    - 상품명 직접 파싱
    - Registry 데이터 관리
    - Registry 점수 하드코딩
    - 공통 Provider 등록 정책 변경
    """

    category_id = "lamb"
    category_name = "양고기"

    aliases = (
        "양고기",
        "양 고기",
        "램",
        "램고기",
        "램 고기",
        "어린양",
        "어린 양",
        "호깃",
        "호겟",
        "머튼",
        "lamb",
        "hogget",
        "mutton",
        "양갈비",
        "양 갈비",
        "램랙",
        "램 랙",
        "프렌치랙",
        "프렌치 랙",
        "양등심",
        "양 등심",
        "램로인",
        "램 로인",
        "램숄더",
        "램 숄더",
        "램생크",
        "램 생크",
    )

    def __init__(
        self,
        *,
        parser: LambParser | None = None,
    ) -> None:
        """
        Parser 생성자 주입을 지원한다.

        테스트에서는 별도 Registry를 사용하는
        LambParser를 전달할 수 있다.
        """
        self.parser = (
            parser
            if parser is not None
            else LambParser()
        )

    def supports(
        self,
        category_id: str | None = None,
        product_name: str | None = None,
    ) -> bool:
        """
        category_id 또는 상품명을 기준으로
        Lamb Provider 지원 여부를 반환한다.
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
        """
        양고기 상품을 분석하고 표준 결과를 반환한다.
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
            extract_lamb_product_name(
                product_data
            )
        )

        parse_result = (
            self.parser.parse_product(
                product_data
            )
        )

        attributes = build_lamb_attributes(
            product=product_data,
            parse_result=parse_result,
        )

        scores = calculate_lamb_scores(
            product=product_data,
            parse_result=parse_result,
            context=context,
        )

        reasons, warnings = apply_lamb_rules(
            attributes=attributes,
            scores=scores,
            parse_result=parse_result,
        )

        final_score = (
            calculate_lamb_final_score(
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
    "LambKnowledgeProvider",
]
