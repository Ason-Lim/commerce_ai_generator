from __future__ import annotations

from collections.abc import Mapping
import re
from typing import Any

from app.services.food.knowledge.base import (
    FoodKnowledgeProvider,
)
from app.services.food.knowledge.models import (
    FoodKnowledgeContext,
    FoodKnowledgeResult,
)
from app.services.food.knowledge.olive_oil.attributes import (
    build_olive_oil_attributes,
    extract_olive_oil_product_name,
)
from app.services.food.knowledge.olive_oil.parser import (
    OliveOilParser,
)
from app.services.food.knowledge.olive_oil.rules import (
    apply_olive_oil_rules,
)
from app.services.food.knowledge.olive_oil.scoring import (
    calculate_olive_oil_final_score,
    calculate_olive_oil_scores,
)


class OliveOilKnowledgeProvider(
    FoodKnowledgeProvider
):
    """
    Olive Oil Knowledge Provider.

    역할:
    - OliveOilParser 실행
    - Olive Oil attributes 구성
    - Olive Oil scoring 실행
    - Olive Oil rules 실행
    - final score 계산
    - FoodKnowledgeResult 생성

    담당하지 않는 역할:
    - 상품명 직접 파싱
    - Registry 직접 조회 또는 수정
    - Attribute 로직 재구현
    - 점수 공식 재구현
    - Rule 조건 재구현
    - 공유 Provider Registry 변경
    - Category Registry 변경
    - Alias Resolution Layer 구현
    """

    category_id = "olive_oil"
    category_name = "올리브오일"

    # Sprint 3의 현재 Provider.aliases Runtime Contract를 유지한다.
    aliases = (
        "olive_oil",
        "olive oil",
        "oliveoil",
        "올리브오일",
        "올리브 오일",
        "올리브유",
        "extra virgin olive oil",
        "extra virgin",
        "evoo",
        "엑스트라 버진 올리브오일",
        "엑스트라버진 올리브오일",
        "엑스트라 버진",
        "엑스트라버진",
        "virgin olive oil",
        "버진 올리브오일",
        "버진 올리브유",
        "olive pomace oil",
        "pomace olive oil",
        "포마스 올리브유",
        "올리브 포마스 오일",
        "cold pressed olive oil",
        "냉압착 올리브오일",
        "저온 압착 올리브오일",
    )

    product_name_aliases = (
        "olive oil",
        "oliveoil",
        "extra virgin olive oil",
        "extra virgin",
        "evoo",
        "virgin olive oil",
        "olive pomace oil",
        "pomace olive oil",
        "cold pressed olive oil",
        "올리브오일",
        "올리브 오일",
        "올리브유",
        "엑스트라 버진 올리브오일",
        "엑스트라버진 올리브오일",
        "엑스트라 버진",
        "엑스트라버진",
        "버진 올리브오일",
        "버진 올리브유",
        "포마스 올리브유",
        "올리브 포마스 오일",
        "냉압착 올리브오일",
        "저온 압착 올리브오일",
    )

    def __init__(
        self,
        *,
        parser: OliveOilParser | None = None,
    ) -> None:
        """
        Parser 생성자 주입을 지원한다.

        테스트 또는 독립 검증 시 별도의
        OliveOilParser 인스턴스를 전달할 수 있다.
        """
        self.parser = (
            parser
            if parser is not None
            else OliveOilParser()
        )

    def supports(
        self,
        category_id: str | None = None,
        product_name: str | None = None,
    ) -> bool:
        """
        category_id 또는 상품명 alias를 기준으로
        Olive Oil Provider 지원 여부를 반환한다.
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

        product_alias_set = {
            alias.strip().casefold()
            for alias in self.product_name_aliases
            if alias.strip()
        }

        aliases_by_length = sorted(
            product_alias_set,
            key=len,
            reverse=True,
        )

        return any(
            self._alias_matches_product_name(
                alias=alias,
                normalized_name=normalized_name,
            )
            for alias in aliases_by_length
        )

    @staticmethod
    def _alias_matches_product_name(
        *,
        alias: str,
        normalized_name: str,
    ) -> bool:
        """
        Provider alias를 상품명과 비교한다.

        영문과 숫자로만 구성된 단일 alias는 다른 단어 내부에서
        오탐되지 않도록 Unicode word boundary를 적용한다.
        한글 또는 공백이 포함된 alias는 구문 검색을 유지한다.
        """
        if not alias:
            return False

        if re.fullmatch(
            r"[a-z0-9]+(?:[-'][a-z0-9]+)*",
            alias,
        ):
            pattern = (
                r"(?<!\w)"
                + re.escape(alias)
                + r"(?!\w)"
            )

            return (
                re.search(
                    pattern,
                    normalized_name,
                )
                is not None
            )

        return alias in normalized_name

    def analyze(
        self,
        product: Mapping[str, Any],
        context: FoodKnowledgeContext | None = None,
    ) -> FoodKnowledgeResult:
        """
        Olive Oil 상품 분석 Pipeline을 실행하여
        공통 FoodKnowledgeResult를 반환한다.
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
            extract_olive_oil_product_name(
                product_data
            )
        )

        parse_result = (
            self.parser.parse_product(
                product_data
            )
        )

        attributes = build_olive_oil_attributes(
            product=product_data,
            parse_result=parse_result,
        )

        scores = calculate_olive_oil_scores(
            product=product_data,
            parse_result=parse_result,
        )

        reasons, warnings = apply_olive_oil_rules(
            attributes=attributes,
            scores=scores,
            parse_result=parse_result,
        )

        final_score = (
            calculate_olive_oil_final_score(
                scores
            )
        )

        return FoodKnowledgeResult(
            category_id=self.category_id,
            category_name=self.category_name,
            product_name=(
                product_name or None
            ),
            attributes=dict(attributes),
            scores=dict(scores),
            reasons=list(reasons),
            warnings=list(warnings),
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
                "expected_field_count": 5,
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
    "OliveOilKnowledgeProvider",
]
