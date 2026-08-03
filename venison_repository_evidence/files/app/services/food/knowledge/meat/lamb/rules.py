from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.services.food.knowledge.meat.lamb.parser_models import (
    LambParseResult,
)


def apply_lamb_rules(
    *,
    attributes: Mapping[str, Any],
    scores: Mapping[str, float],
    parse_result: LambParseResult,
) -> tuple[
    list[str],
    list[str],
]:
    """
    양고기 분석 결과를 기반으로
    추천 이유와 경고를 생성한다.

    Rules는 설명과 경고만 생성하며,
    점수를 직접 변경하지 않는다.
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
        LambParseResult,
    ):
        raise TypeError(
            "parse_result must be LambParseResult"
        )

    reasons: list[str] = []
    warnings: list[str] = list(
        parse_result.warnings
    )

    country = attributes.get(
        "country"
    )
    age = attributes.get(
        "age"
    )
    breed = attributes.get(
        "breed"
    )
    cut = attributes.get(
        "cut"
    )

    if age:
        reasons.append(
            f"연령 분류는 {age}입니다."
        )

        age_description = attributes.get(
            "age_description"
        )

        if age_description:
            reasons.append(
                str(age_description)
            )

    if breed:
        reasons.append(
            f"품종은 {breed}입니다."
        )

    if country:
        reasons.append(
            f"원산지는 {country}입니다."
        )
    elif not any(
        "원산지" in warning
        for warning in warnings
    ):
        warnings.append(
            "원산지 정보가 확인되지 않았습니다."
        )

    if cut:
        reasons.append(
            f"{cut} 부위 상품입니다."
        )

    cooking_methods = (
        attributes.get(
            "cut_cooking_methods"
        )
        or []
    )

    if cooking_methods:
        method_text = ", ".join(
            str(method)
            for method in cooking_methods
            if str(method).strip()
        )

        if method_text:
            reasons.append(
                "Registry 기준 권장 조리 방식은 "
                f"{method_text}입니다."
            )

    flavor_intensity = attributes.get(
        "age_flavor_intensity"
    )

    if flavor_intensity == "mild":
        reasons.append(
            "연령 분류 기준 풍미 강도가 "
            "비교적 순한 편입니다."
        )
    elif flavor_intensity == "medium":
        reasons.append(
            "연령 분류 기준 적당한 풍미를 "
            "기대할 수 있습니다."
        )
    elif flavor_intensity == "strong":
        reasons.append(
            "연령 분류 기준 양고기 풍미가 "
            "강한 편입니다."
        )

    tenderness_level = attributes.get(
        "age_tenderness_level"
    )

    if tenderness_level == "high":
        reasons.append(
            "연령 분류 기준 부드러운 육질을 "
            "기대할 수 있습니다."
        )
    elif tenderness_level == "low":
        warnings.append(
            "연령 분류 기준 육질이 단단할 수 있어 "
            "장시간 조리가 적합할 수 있습니다."
        )

    if (
        scores.get(
            "age",
            0.0,
        )
        >= 85.0
    ):
        reasons.append(
            "연령 분류 기준 상품성이 높은 "
            "양고기입니다."
        )

    if (
        scores.get(
            "breed",
            0.0,
        )
        >= 85.0
    ):
        reasons.append(
            "품종 Registry 기준 평가가 "
            "높은 품종입니다."
        )

    if (
        scores.get(
            "cut",
            0.0,
        )
        >= 90.0
    ):
        reasons.append(
            "상품성이 높은 부위로 "
            "분류됩니다."
        )

    if (
        scores.get(
            "tenderness",
            0.0,
        )
        >= 85.0
    ):
        reasons.append(
            "품종과 부위 기준 부드러운 식감을 "
            "기대할 수 있습니다."
        )

    if (
        scores.get(
            "flavor",
            0.0,
        )
        >= 85.0
    ):
        reasons.append(
            "품종과 부위 기준 풍미 평가가 "
            "높은 상품입니다."
        )

    if (
        attributes.get(
            "age_premium"
        )
        or attributes.get(
            "breed_premium"
        )
        or attributes.get(
            "cut_premium"
        )
    ):
        reasons.append(
            "Registry에서 프리미엄 속성이 "
            "확인되었습니다."
        )

    storage_type = attributes.get(
        "storage_type"
    )

    if storage_type:
        reasons.append(
            f"보관 상태는 {storage_type}입니다."
        )

    certifications = (
        attributes.get(
            "certifications"
        )
        or []
    )

    if certifications:
        certification_text = ", ".join(
            str(certification)
            for certification in certifications
            if str(certification).strip()
        )

        if certification_text:
            reasons.append(
                "표시된 인증 정보는 "
                f"{certification_text}입니다."
            )

    if not parse_result.is_complete:
        warnings.append(
            "연령, 품종, 부위 정보가 "
            "모두 확인되지 않았습니다."
        )

    if (
        scores.get(
            "knowledge",
            0.0,
        )
        <= 0.0
    ):
        warnings.append(
            "양고기 Registry 기반 평가 점수를 "
            "계산할 수 없습니다."
        )

    return (
        deduplicate_strings(
            reasons
        ),
        deduplicate_strings(
            warnings
        ),
    )


def deduplicate_strings(
    values: list[str],
) -> list[str]:
    """
    빈 문자열과 중복 문자열을 제거한다.

    최초 등장 순서는 유지한다.
    """
    result: list[str] = []
    seen: set[str] = set()

    for value in values:
        normalized = str(
            value
        ).strip()

        if (
            not normalized
            or normalized in seen
        ):
            continue

        seen.add(normalized)
        result.append(
            normalized
        )

    return result


__all__ = [
    "apply_lamb_rules",
    "deduplicate_strings",
]
