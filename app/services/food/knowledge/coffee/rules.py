from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from app.services.food.knowledge.coffee.parser_models import (
    CoffeeParseResult,
)


def deduplicate_strings(
    values: Iterable[Any],
) -> list[str]:
    """
    빈 문자열을 제거하고 최초 등장 순서를 유지하면서
    중복 문자열을 제거한다.
    """
    result: list[str] = []
    seen: set[str] = set()

    for value in values:
        normalized = str(value).strip()

        if (
            not normalized
            or normalized in seen
        ):
            continue

        seen.add(normalized)
        result.append(normalized)

    return result


def apply_coffee_rules(
    *,
    attributes: Mapping[str, Any],
    scores: Mapping[str, Any],
    parse_result: CoffeeParseResult,
) -> tuple[list[str], list[str]]:
    """
    Coffee Attributes와 Scores를 바탕으로
    설명 이유와 경고를 생성한다.

    이 함수는 다음 작업을 수행하지 않는다.

    - 상품명 재파싱
    - Registry 재조회
    - 점수 재계산
    - attributes, scores, parse_result 수정
    """
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

    if not isinstance(
        parse_result,
        CoffeeParseResult,
    ):
        raise TypeError(
            "parse_result must be CoffeeParseResult"
        )

    reasons: list[str] = []
    warnings: list[str] = list(
        parse_result.warnings
    )

    bean = _optional_text(
        attributes.get("bean")
    )
    origin = _optional_text(
        attributes.get("origin")
    )
    country = _optional_text(
        attributes.get("country")
    )
    roast = _optional_text(
        attributes.get("roast")
    )
    process = _optional_text(
        attributes.get("process")
    )
    grind_type = _optional_text(
        attributes.get("grind_type")
    )
    product_form = _optional_text(
        attributes.get("product_form")
    )
    weight = _optional_text(
        attributes.get("weight")
    )
    altitude = _optional_text(
        attributes.get("altitude")
    )
    roast_date = _optional_text(
        attributes.get("roast_date")
    )

    decaf = attributes.get("decaf")

    certifications = deduplicate_strings(
        attributes.get("certifications")
        or []
    )

    flavor_notes = deduplicate_strings(
        attributes.get("flavor_notes")
        or []
    )

    if bean:
        reasons.append(
            f"원두 종류는 {bean}입니다."
        )

    resolved_origin = country or origin

    if resolved_origin:
        reasons.append(
            f"원산지는 {resolved_origin}입니다."
        )

    if roast:
        reasons.append(
            f"로스팅 단계는 {roast}입니다."
        )

    if process:
        reasons.append(
            f"가공 방식은 {process}입니다."
        )

    if grind_type:
        reasons.append(
            f"분쇄 형태는 {grind_type}입니다."
        )

    if product_form:
        reasons.append(
            f"상품 형태는 {product_form}입니다."
        )

    if weight:
        reasons.append(
            f"표시 중량은 {weight}입니다."
        )

    if altitude:
        reasons.append(
            f"재배 고도 표시는 {altitude}입니다."
        )

    if roast_date:
        reasons.append(
            f"로스팅 날짜는 {roast_date}입니다."
        )

    if decaf is True:
        reasons.append(
            "디카페인 상품으로 표시되어 있습니다."
        )
    elif decaf is False:
        reasons.append(
            "일반 카페인 상품으로 표시되어 있습니다."
        )

    if certifications:
        reasons.append(
            "표시된 인증 정보는 "
            f"{', '.join(certifications)}입니다."
        )

    if flavor_notes:
        reasons.append(
            "표시된 향미 노트는 "
            f"{', '.join(flavor_notes)}입니다."
        )

    premium_fields = _premium_fields(
        attributes
    )

    if premium_fields:
        reasons.append(
            "Registry에서 프리미엄 속성이 "
            "확인되었습니다."
        )

    knowledge_score = _safe_score(
        scores.get("knowledge")
    )

    if knowledge_score >= 90.0:
        reasons.append(
            "Coffee Knowledge 평가가 "
            "매우 높은 수준입니다."
        )
    elif knowledge_score >= 80.0:
        reasons.append(
            "Coffee Knowledge 평가가 "
            "높은 수준입니다."
        )
    elif knowledge_score > 0.0:
        reasons.append(
            "Coffee Knowledge 평가가 "
            "확인되었습니다."
        )

    acidity_score = _safe_score(
        scores.get("acidity")
    )

    if acidity_score >= 90.0:
        reasons.append(
            "Registry 기준 산미 특성이 "
            "뚜렷한 상품입니다."
        )

    body_score = _safe_score(
        scores.get("body")
    )

    if body_score >= 90.0:
        reasons.append(
            "Registry 기준 바디감이 "
            "높은 상품입니다."
        )

    aroma_score = _safe_score(
        scores.get("aroma")
    )

    if aroma_score >= 90.0:
        reasons.append(
            "Registry 기준 향미 평가가 "
            "높은 상품입니다."
        )

    sweetness_score = _safe_score(
        scores.get("sweetness")
    )

    if sweetness_score >= 90.0:
        reasons.append(
            "Registry 기준 단맛 특성이 "
            "높은 가공 방식입니다."
        )

    clarity_score = _safe_score(
        scores.get("clarity")
    )

    if clarity_score >= 90.0:
        reasons.append(
            "Registry 기준 향미 선명도가 "
            "높은 가공 방식입니다."
        )

    if not bean:
        warnings.append(
            "원두 종류 정보가 확인되지 않았습니다."
        )

    if not resolved_origin:
        warnings.append(
            "커피 원산지 정보가 확인되지 않았습니다."
        )

    if not roast:
        warnings.append(
            "로스팅 단계 정보가 확인되지 않았습니다."
        )

    if not process:
        warnings.append(
            "가공 방식 정보가 확인되지 않았습니다."
        )

    if knowledge_score <= 0.0:
        warnings.append(
            "Coffee Registry 기반 평가 점수를 "
            "계산할 수 없습니다."
        )

    if not parse_result.is_usable:
        warnings.append(
            "Coffee 도메인 분석에 필요한 정보가 "
            "충분하지 않습니다."
        )

    return (
        deduplicate_strings(reasons),
        deduplicate_strings(warnings),
    )


def _premium_fields(
    attributes: Mapping[str, Any],
) -> list[str]:
    premium_keys = {
        "bean_premium": "bean",
        "origin_premium": "origin",
        "roast_premium": "roast",
        "process_premium": "process",
    }

    return [
        label
        for key, label in premium_keys.items()
        if bool(attributes.get(key))
    ]


def _safe_score(
    value: Any,
) -> float:
    try:
        score = float(value)
    except (TypeError, ValueError):
        return 0.0

    return max(
        0.0,
        min(
            100.0,
            score,
        ),
    )


def _optional_text(
    value: Any,
) -> str | None:
    if value is None:
        return None

    normalized = str(value).strip()

    return normalized or None


__all__ = [
    "apply_coffee_rules",
    "deduplicate_strings",
]
