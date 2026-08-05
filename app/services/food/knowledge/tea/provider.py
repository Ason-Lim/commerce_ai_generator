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
from app.services.food.knowledge.tea.attributes import (
    build_tea_attributes,
    extract_tea_product_name,
)
from app.services.food.knowledge.tea.parser import (
    TeaParser,
)
from app.services.food.knowledge.tea.rules import (
    apply_tea_rules,
)
from app.services.food.knowledge.tea.scoring import (
    calculate_tea_final_score,
    calculate_tea_scores,
)


class TeaKnowledgeProvider(
    FoodKnowledgeProvider
):
    """
    Tea Knowledge Provider.

    역할:
    - TeaParser 실행
    - Tea attributes 구성
    - Tea scoring 실행
    - Tea rules 실행
    - 최종 점수 계산
    - FoodKnowledgeResult 생성

    담당하지 않는 역할:
    - 상품명 직접 파싱
    - Registry 직접 조회
    - Registry 데이터 관리
    - 점수 공식 재구현
    - Rule 조건 재구현
    - 공유 Provider Registry 변경
    - Category Registry 변경
    - Alias Resolution Layer 구현
    """

    category_id = "tea"
    category_name = "차"

    # AD-2026-022에 따른 현재 Runtime Alias 계약을 유지한다.
    aliases = (
        "tea",
        "차",
        "티",
        "녹차",
        "green tea",
        "홍차",
        "black tea",
        "백차",
        "white tea",
        "우롱차",
        "우롱",
        "oolong",
        "oolong tea",
        "보이차",
        "푸얼차",
        "pu-erh",
        "pu erh",
        "puerh",
        "말차",
        "matcha",
        "센차",
        "sencha",
        "다즐링",
        "darjeeling",
        "아삼",
        "assam",
        "얼그레이",
        "earl grey",
        "자스민티",
        "자스민 차",
        "jasmine tea",
    )

    product_name_aliases = (
        "tea",
        "green tea",
        "black tea",
        "white tea",
        "oolong",
        "oolong tea",
        "pu-erh",
        "pu erh",
        "puerh",
        "matcha",
        "sencha",
        "darjeeling",
        "assam",
        "earl grey",
        "jasmine tea",
        "녹차",
        "홍차",
        "백차",
        "우롱차",
        "보이차",
        "푸얼차",
        "말차",
        "센차",
        "다즐링",
        "아삼",
        "얼그레이",
        "자스민티",
        "자스민 차",
    )

    def __init__(
        self,
        *,
        parser: TeaParser | None = None,
    ) -> None:
        """
        Parser 생성자 주입을 지원한다.

        테스트 또는 독립 Registry 검증에서는
        별도 TeaParser 인스턴스를 전달할 수 있다.
        """
        self.parser = (
            parser
            if parser is not None
            else TeaParser()
        )

    def supports(
        self,
        category_id: str | None = None,
        product_name: str | None = None,
    ) -> bool:
        """
        category_id 또는 상품명 alias를 기준으로
        Tea Provider 지원 여부를 반환한다.
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

        영문·숫자로만 구성된 alias는 다른 단어 내부에서
        오탐되지 않도록 Unicode word boundary를 적용한다.
        한글 또는 공백 포함 alias는 구문 검색을 유지한다.
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
        Tea 상품 전체 분석 Pipeline을 실행하여
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

        product_name = extract_tea_product_name(
            product_data
        )

        parse_result = self.parser.parse_product(
            product_data
        )

        attributes = build_tea_attributes(
            product=product_data,
            parse_result=parse_result,
        )

        scores = calculate_tea_scores(
            product=product_data,
            parse_result=parse_result,
        )

        reasons, warnings = apply_tea_rules(
            attributes=attributes,
            scores=scores,
            parse_result=parse_result,
        )

        final_score = calculate_tea_final_score(
            scores
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
    "TeaKnowledgeProvider",
]
