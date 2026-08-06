from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.services.food.knowledge.herb_spice.parser_models import (
    HerbSpiceParseResult,
)


HERB_SPICE_RULE_IDS: tuple[str, ...] = (
    "herb_spice.ingredient_identified",
    "herb_spice.complete_profile",
    "herb_spice.partial_profile",
    "herb_spice.ingredient_conflict",
    "herb_spice.origin_identified",
    "herb_spice.form_identified",
    "herb_spice.usage_identified",
    "herb_spice.organic_declared",
    "herb_spice.certification_present",
    "herb_spice.additives_present",
    "herb_spice.salt_added",
    "herb_spice.premium_ingredient",
    "herb_spice.product_information_missing",
)


def evaluate_herb_spice_rules(
    *,
    product: Mapping[str, Any],
    parse_result: HerbSpiceParseResult,
    attributes: Mapping[str, Any],
    scores: Mapping[str, Any],
) -> dict[str, Any]:
    """
    Herb & Spice 분석 결과에 Rule을 적용한다.

    반환 계약:
    - rules: 활성화된 Rule ID 목록
    - reasons: 설명 가능한 긍정·중립 근거
    - warnings: 주의 또는 정보 부족 메시지
    - flags: Provider가 참조할 수 있는 불리언 상태
    - metadata: Rule 평가 관련 결정적 메타데이터

    담당하지 않는 책임:
    - 상품명 파싱
    - Registry 조회
    - Attribute 생성
    - Score 계산
    - Final Score 계산
    - Provider orchestration
    """
    _validate_inputs(
        product=product,
        parse_result=parse_result,
        attributes=attributes,
        scores=scores,
    )

    rules: list[str] = []
    reasons: list[str] = []
    warnings: list[str] = []

    ingredient_identified = bool(
        parse_result.ingredient
    )
    complete_profile = bool(
        parse_result.is_complete
    )
    partial_profile = (
        parse_result.has_match
        and not parse_result.is_complete
    )
    ingredient_conflict = bool(
        parse_result.has_ingredient_conflict
    )
    origin_identified = bool(
        parse_result.origin
    )
    form_identified = bool(
        parse_result.form
    )
    usage_identified = bool(
        parse_result.usage
    )

    organic_declared = (
        attributes.get("organic") is True
    )
    certification_present = bool(
        _as_string_list(
            attributes.get("certifications")
        )
    )
    additives_present = bool(
        _as_string_list(
            attributes.get("additives")
        )
    )
    salt_added = (
        attributes.get("salt_added") is True
    )
    premium_ingredient = bool(
        attributes.get("ingredient_premium")
    )
    product_information_missing = (
        not parse_result.is_usable
    )

    if ingredient_identified:
        rules.append(
            "herb_spice.ingredient_identified"
        )
        reasons.append(
            _ingredient_reason(
                classification=(
                    parse_result.classification
                ),
                ingredient=(
                    parse_result.ingredient
                ),
            )
        )

    if complete_profile:
        rules.append(
            "herb_spice.complete_profile"
        )
        reasons.append(
            "성분, 원산지, 제품 형태 및 사용 용도가 "
            "모두 확인되었습니다."
        )
    elif partial_profile:
        rules.append(
            "herb_spice.partial_profile"
        )
        reasons.append(
            "일부 Herb & Spice 속성이 확인되었습니다."
        )

    if ingredient_conflict:
        rules.append(
            "herb_spice.ingredient_conflict"
        )
        warnings.append(
            "Herb와 Spice 성분이 동시에 탐지되었습니다. "
            "대표 성분은 Parser evidence 우선순위에 따라 "
            "선택되었습니다."
        )

    if origin_identified:
        rules.append(
            "herb_spice.origin_identified"
        )
        reasons.append(
            f"원산지가 '{parse_result.origin}'으로 "
            "확인되었습니다."
        )

    if form_identified:
        rules.append(
            "herb_spice.form_identified"
        )
        reasons.append(
            f"제품 형태가 '{parse_result.form}'으로 "
            "확인되었습니다."
        )

    if usage_identified:
        rules.append(
            "herb_spice.usage_identified"
        )
        reasons.append(
            f"사용 용도가 '{parse_result.usage}'으로 "
            "확인되었습니다."
        )

    if organic_declared:
        rules.append(
            "herb_spice.organic_declared"
        )
        reasons.append(
            "구조화된 상품 정보에 유기농 여부가 "
            "명시되어 있습니다."
        )

    if certification_present:
        rules.append(
            "herb_spice.certification_present"
        )
        certifications = ", ".join(
            _as_string_list(
                attributes.get(
                    "certifications"
                )
            )
        )
        reasons.append(
            f"인증 또는 품질 표시가 확인되었습니다: "
            f"{certifications}."
        )

    if premium_ingredient:
        rules.append(
            "herb_spice.premium_ingredient"
        )
        reasons.append(
            "선택된 성분이 Registry에서 Premium 항목으로 "
            "표시되어 있습니다."
        )

    if additives_present:
        rules.append(
            "herb_spice.additives_present"
        )
        additives = ", ".join(
            _as_string_list(
                attributes.get("additives")
            )
        )
        warnings.append(
            f"첨가 성분이 표시되어 있습니다: "
            f"{additives}."
        )

    if salt_added:
        rules.append(
            "herb_spice.salt_added"
        )
        warnings.append(
            "구조화된 상품 정보에 소금 첨가가 "
            "표시되어 있습니다."
        )

    if product_information_missing:
        rules.append(
            "herb_spice.product_information_missing"
        )
        warnings.append(
            "Herb & Spice 분석에 필요한 상품 정보가 "
            "충분하지 않습니다."
        )

    warnings.extend(
        parse_result.warnings
    )

    flags = {
        "ingredient_identified": (
            ingredient_identified
        ),
        "complete_profile": complete_profile,
        "partial_profile": partial_profile,
        "ingredient_conflict": (
            ingredient_conflict
        ),
        "origin_identified": (
            origin_identified
        ),
        "form_identified": form_identified,
        "usage_identified": usage_identified,
        "organic_declared": organic_declared,
        "certification_present": (
            certification_present
        ),
        "additives_present": (
            additives_present
        ),
        "salt_added": salt_added,
        "premium_ingredient": (
            premium_ingredient
        ),
        "product_information_missing": (
            product_information_missing
        ),
    }

    return {
        "rules": _deduplicate_strings(
            rules
        ),
        "reasons": _deduplicate_strings(
            reasons
        ),
        "warnings": _deduplicate_strings(
            warnings
        ),
        "flags": flags,
        "metadata": {
            "category_id": "herb_spice",
            "evaluated_rule_count": len(
                HERB_SPICE_RULE_IDS
            ),
            "activated_rule_count": len(
                _deduplicate_strings(
                    rules
                )
            ),
            "matched_field_count": (
                parse_result.matched_field_count
            ),
            "classification": (
                parse_result.classification
            ),
            "ingredient": (
                parse_result.ingredient
            ),
            "knowledge_score": (
                _safe_score(
                    scores.get("knowledge")
                )
            ),
            "final_score_available": (
                "final_score" in scores
            ),
        },
    }


def build_herb_spice_reasons(
    *,
    product: Mapping[str, Any],
    parse_result: HerbSpiceParseResult,
    attributes: Mapping[str, Any],
    scores: Mapping[str, Any],
) -> list[str]:
    """Rule 평가 결과에서 reasons만 반환한다."""
    result = evaluate_herb_spice_rules(
        product=product,
        parse_result=parse_result,
        attributes=attributes,
        scores=scores,
    )

    return list(result["reasons"])


def build_herb_spice_warnings(
    *,
    product: Mapping[str, Any],
    parse_result: HerbSpiceParseResult,
    attributes: Mapping[str, Any],
    scores: Mapping[str, Any],
) -> list[str]:
    """Rule 평가 결과에서 warnings만 반환한다."""
    result = evaluate_herb_spice_rules(
        product=product,
        parse_result=parse_result,
        attributes=attributes,
        scores=scores,
    )

    return list(result["warnings"])


def build_herb_spice_rule_flags(
    *,
    product: Mapping[str, Any],
    parse_result: HerbSpiceParseResult,
    attributes: Mapping[str, Any],
    scores: Mapping[str, Any],
) -> dict[str, bool]:
    """Rule 평가 결과에서 flags만 반환한다."""
    result = evaluate_herb_spice_rules(
        product=product,
        parse_result=parse_result,
        attributes=attributes,
        scores=scores,
    )

    return dict(result["flags"])


def _validate_inputs(
    *,
    product: Mapping[str, Any],
    parse_result: HerbSpiceParseResult,
    attributes: Mapping[str, Any],
    scores: Mapping[str, Any],
) -> None:
    if not isinstance(
        product,
        Mapping,
    ):
        raise TypeError(
            "product must be a Mapping"
        )

    if not isinstance(
        parse_result,
        HerbSpiceParseResult,
    ):
        raise TypeError(
            "parse_result must be "
            "HerbSpiceParseResult"
        )

    if not isinstance(
        attributes,
        Mapping,
    ):
        raise TypeError(
            "attributes must be a Mapping"
        )

    if not isinstance(
        scores,
        Mapping,
    ):
        raise TypeError(
            "scores must be a Mapping"
        )


def _ingredient_reason(
    *,
    classification: str | None,
    ingredient: str | None,
) -> str:
    if (
        classification == "herb"
        and ingredient
    ):
        return (
            f"Herb 성분 '{ingredient}'이 "
            "확인되었습니다."
        )

    if (
        classification == "spice"
        and ingredient
    ):
        return (
            f"Spice 성분 '{ingredient}'이 "
            "확인되었습니다."
        )

    if ingredient:
        return (
            f"Herb & Spice 성분 '{ingredient}'이 "
            "확인되었습니다."
        )

    return (
        "Herb & Spice 성분 정보가 "
        "확인되었습니다."
    )


def _as_string_list(
    value: Any,
) -> list[str]:
    if value is None:
        return []

    if isinstance(value, str):
        normalized = value.strip()

        return (
            [normalized]
            if normalized
            else []
        )

    if isinstance(
        value,
        (
            list,
            tuple,
            set,
            frozenset,
        ),
    ):
        return _deduplicate_strings(
            [
                str(item).strip()
                for item in value
                if str(item).strip()
            ]
        )

    normalized = str(value).strip()

    return (
        [normalized]
        if normalized
        else []
    )


def _safe_score(
    value: Any,
) -> float:
    try:
        score = float(value)
    except (TypeError, ValueError):
        score = 0.0

    return max(
        0.0,
        min(
            100.0,
            score,
        ),
    )


def _deduplicate_strings(
    values: list[str],
) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()

    for value in values:
        normalized = str(value).strip()
        key = normalized.casefold()

        if not normalized or key in seen:
            continue

        seen.add(key)
        result.append(normalized)

    return result


__all__ = [
    "HERB_SPICE_RULE_IDS",
    "build_herb_spice_reasons",
    "build_herb_spice_rule_flags",
    "build_herb_spice_warnings",
    "evaluate_herb_spice_rules",
]
