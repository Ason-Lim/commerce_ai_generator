from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.services.food.knowledge.base import (
    FoodKnowledgeProvider,
)
from app.services.food.knowledge.herb_spice.attributes import (
    build_herb_spice_attributes,
    extract_herb_spice_product_name,
)
from app.services.food.knowledge.herb_spice.parser import (
    HerbSpiceParser,
)
from app.services.food.knowledge.herb_spice.rules import (
    evaluate_herb_spice_rules,
)
from app.services.food.knowledge.herb_spice.scoring import (
    calculate_herb_spice_final_score,
    calculate_herb_spice_scores,
)
from app.services.food.knowledge.models import (
    FoodKnowledgeContext,
    FoodKnowledgeResult,
    FoodRuleResult,
)


class HerbSpiceKnowledgeProvider(
    FoodKnowledgeProvider
):
    """
    Herb & Spice Knowledge Provider.

    Provider 책임:
    - Parser 호출
    - Attribute Builder 호출
    - Scoring 호출
    - Rule Engine 호출
    - 공통 FoodKnowledgeResult 조립

    Provider가 담당하지 않는 책임:
    - 정규식 또는 Alias 탐지 로직 확장
    - Registry 데이터 변경
    - Attribute 계산 로직 직접 구현
    - Score 공식 직접 구현
    - Rule 판정 직접 구현
    - 공통 Runtime 계약 변경
    """

    category_id = "herb_spice"
    category_name = "허브·향신료"

    # Sprint 3에서는 현재 Provider.aliases Runtime Contract를 유지한다.
    aliases = (
        "herb_spice",
        "herb spice",
        "herb & spice",
        "herbs and spices",
        "herb",
        "herbs",
        "spice",
        "spices",
        "culinary herb",
        "culinary spice",
        "허브",
        "향신료",
        "허브 향신료",
        "허브·향신료",
        "로즈마리",
        "로즈메리",
        "타임",
        "백리향",
        "바질",
        "파슬리",
        "오레가노",
        "딜",
        "민트",
        "박하",
        "고수잎",
        "생고수",
        "후추",
        "흑후추",
        "통후추",
        "큐민",
        "커민",
        "쯔란",
        "계피",
        "시나몬",
        "강황",
        "울금",
        "생강",
        "파프리카 파우더",
        "고춧가루",
        "칠리 파우더",
        "고수씨",
        "코리앤더 씨드",
        "카다멈",
        "카르다몸",
        "cardamom",
        "cardamom pod",
        "green cardamom",
        "cinnamon",
        "cinnamon bark",
        "cassia",
        "와사비 분말",
        "와사비 뿌리",
    )

    # Condiment 및 Tea 도메인으로 분리해야 하는 표현이다.
    _EXCLUDED_PRODUCT_MARKERS = (
        "간장",
        "soy sauce",
        "식초",
        "vinegar",
        "된장",
        "doenjang",
        "고추장",
        "gochujang",
        "쌈장",
        "케첩",
        "ketchup",
        "마요네즈",
        "mayonnaise",
        "굴소스",
        "oyster sauce",
        "피시소스",
        "fish sauce",
        "와사비 소스",
        "wasabi sauce",
        "와사비 페이스트",
        "wasabi paste",
        "튜브 와사비",
        "허브티",
        "허브 티",
        "herbal tea",
        "herbal infusion",
    )

    def __init__(
        self,
        *,
        parser: HerbSpiceParser | None = None,
    ) -> None:
        self.parser = (
            parser
            if parser is not None
            else HerbSpiceParser()
        )

    def supports(
        self,
        category_id: str | None = None,
        product_name: str | None = None,
    ) -> bool:
        """
        명시된 카테고리 또는 상품명이
        Herb & Spice 도메인에 해당하는지 확인한다.

        Sprint 3에서는 별도 Alias Resolution Layer를
        구현하지 않고 Provider.aliases 계약을 유지한다.
        """
        if category_id:
            normalized_category = self._normalize_text(
                category_id
            )

            category_aliases = {
                self._normalize_text(alias)
                for alias in (
                    self.category_id,
                    self.category_name,
                    *self.aliases,
                )
                if self._normalize_text(alias)
            }

            if normalized_category in category_aliases:
                return True

        if not product_name:
            return False

        normalized_name = self._normalize_text(
            product_name
        )

        if not normalized_name:
            return False

        if any(
            self._normalize_text(marker)
            in normalized_name
            for marker in self._EXCLUDED_PRODUCT_MARKERS
        ):
            return False

        product_aliases = sorted(
            {
                self._normalize_text(alias)
                for alias in self.aliases
                if self._normalize_text(alias)
            },
            key=len,
            reverse=True,
        )

        return any(
            alias in normalized_name
            for alias in product_aliases
        )

    def analyze(
        self,
        product: Mapping[str, Any],
        context: FoodKnowledgeContext | None = None,
    ) -> FoodKnowledgeResult:
        """
        Herb & Spice 분석 Pipeline을 실행하여
        공통 FoodKnowledgeResult를 반환한다.
        """
        if not isinstance(
            product,
            Mapping,
        ):
            raise TypeError(
                "product must be a Mapping"
            )

        if not product:
            raise ValueError(
                "product must not be empty"
            )

        if (
            context is not None
            and not isinstance(
                context,
                FoodKnowledgeContext,
            )
        ):
            raise TypeError(
                "context must be "
                "FoodKnowledgeContext or None"
            )

        product_data = dict(product)

        product_name = (
            extract_herb_spice_product_name(
                product_data
            )
        )

        parse_result = (
            self.parser.parse_product(
                product_data
            )
        )

        attributes = build_herb_spice_attributes(
            product=product_data,
            parse_result=parse_result,
        )

        scores = calculate_herb_spice_scores(
            product=product_data,
            parse_result=parse_result,
        )

        rule_result = evaluate_herb_spice_rules(
            product=product_data,
            parse_result=parse_result,
            attributes=attributes,
            scores=scores,
        )

        final_score = (
            calculate_herb_spice_final_score(
                scores
            )
        )

        rule_objects = self._build_rule_objects(
            rule_result
        )

        return FoodKnowledgeResult(
            category_id=self.category_id,
            category_name=self.category_name,
            product_name=(
                product_name or None
            ),
            attributes=dict(attributes),
            scores=dict(scores),
            rules=rule_objects,
            reasons=list(
                rule_result["reasons"]
            ),
            warnings=list(
                rule_result["warnings"]
            ),
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
                "context_metadata": (
                    dict(context.metadata)
                    if context is not None
                    else {}
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
                "classification": (
                    parse_result.classification
                ),
                "ingredient": (
                    parse_result.ingredient
                ),
                "ingredient_conflict": (
                    parse_result
                    .has_ingredient_conflict
                ),
                "rule_flags": dict(
                    rule_result["flags"]
                ),
                "rule_metadata": dict(
                    rule_result["metadata"]
                ),
                "activated_rule_ids": list(
                    rule_result["rules"]
                ),
            },
            raw_product=product_data,
        )

    @staticmethod
    def _build_rule_objects(
        rule_result: Mapping[str, Any],
    ) -> list[FoodRuleResult]:
        active_rule_ids = list(
            rule_result.get(
                "rules",
                [],
            )
        )
        flags = dict(
            rule_result.get(
                "flags",
                {},
            )
        )
        metadata = dict(
            rule_result.get(
                "metadata",
                {},
            )
        )

        warning_rule_ids = {
            "herb_spice.ingredient_conflict",
            "herb_spice.additives_present",
            "herb_spice.salt_added",
            "herb_spice.product_information_missing",
        }

        results: list[FoodRuleResult] = []

        for rule_id in active_rule_ids:
            flag_name = str(
                rule_id
            ).removeprefix(
                "herb_spice."
            )

            results.append(
                FoodRuleResult(
                    rule_id=str(rule_id),
                    matched=True,
                    message=None,
                    severity=(
                        "warning"
                        if rule_id
                        in warning_rule_ids
                        else "info"
                    ),
                    metadata={
                        "category_id": (
                            "herb_spice"
                        ),
                        "flag": flags.get(
                            flag_name,
                            True,
                        ),
                        "classification": (
                            metadata.get(
                                "classification"
                            )
                        ),
                        "ingredient": (
                            metadata.get(
                                "ingredient"
                            )
                        ),
                    },
                )
            )

        return results

    @staticmethod
    def _normalize_text(
        value: Any,
    ) -> str:
        return " ".join(
            str(value or "")
            .strip()
            .casefold()
            .replace("_", " ")
            .replace("-", " ")
            .split()
        )


__all__ = [
    "HerbSpiceKnowledgeProvider",
]
